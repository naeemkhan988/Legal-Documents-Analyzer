"""
Service - Celery Worker Setup
=============================
Configures Celery with Redis for background processing.
"""

import os
from celery import Celery
from backend.config import settings

# Initialize Celery
celery_app = Celery(
    "legal_analyzer_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# We will define tasks here or import them
@celery_app.task(bind=True, name="run_document_analysis")
def run_document_analysis_task(self, document_id: str):
    from backend.database.session import SessionLocal
    from backend.database.models import Task, Document, Analysis, Clause
    from backend.services.clause_extractor import extract_all_clauses
    from backend.services.ner_service import extract_entities
    from backend.services.risk_scorer import score_document, explain_risk, get_risk_level
    from backend.services.llm_service import summarize_document, get_recommendations
    from backend.utils.constants import DEFAULT_USER_ID
    from backend.schemas.analysis import ClauseResponse, EntityResponse

    db = SessionLocal()
    try:
        task_record = db.query(Task).filter(Task.task_id == self.request.id).first()
        if task_record:
            task_record.status = "RUNNING"
            db.commit()

        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc or not doc.cleaned_text:
            raise Exception("Document not found or no text available.")

        text = doc.cleaned_text
        extracted = extract_all_clauses(text)
        clause_dicts = [{"clause_type": c.clause_type, "text": c.text, "risk_level": c.risk_level, "confidence": c.confidence, "suggested_change": getattr(c, "suggested_change", None), "obligations": getattr(c, "obligations", [])} for c in extracted]
        risk_score = score_document(extracted)
        risk_level = get_risk_level(risk_score)
        risk_summary = explain_risk(extracted, risk_score)
        entities = extract_entities(text)
        
        try: summary = summarize_document(text)
        except Exception: summary = "Summary unavailable."
        
        try:
            clauses_text = "\n".join(f"[{c.clause_type}] {c.text[:200]}" for c in extracted[:10])
            recs = get_recommendations(clauses_text, risk_score)
        except Exception:
            recs = ["No recommendations available."]

        analysis = Analysis(
            document_id=document_id,
            user_id=DEFAULT_USER_ID,
            risk_score=risk_score,
            risk_level=risk_level,
            risk_summary=risk_summary,
            clauses_json=clause_dicts,
            entities_json=entities,
            summary=summary,
            recommendations_json=recs,
        )
        db.add(analysis)
        for c in extracted:
            db.add(Clause(analysis_id=analysis.id, clause_type=c.clause_type, text=c.text, risk_level=c.risk_level, confidence=c.confidence, suggested_change=c.suggested_change))
        db.commit()
        db.refresh(analysis)

        if task_record:
            task_record.status = "COMPLETED"
            task_record.result = {"analysis_id": analysis.id}
            db.commit()

        return {"status": "success", "analysis_id": analysis.id}
    except Exception as e:
        if task_record:
            task_record.status = "FAILED"
            task_record.error = str(e)
            db.commit()
        raise e
    finally:
        db.close()


@celery_app.task(bind=True, name="generate_report")
def generate_report_task(self, analysis_id: str, report_type: str):
    from backend.database.session import SessionLocal
    from backend.database.models import Task, Analysis, Report
    from backend.services.report_generator import generate_pdf_report, generate_html_report, generate_json_report, export_to_excel
    from backend.config import settings
    from pathlib import Path
    import uuid
    import json
    from backend.utils.constants import DEFAULT_USER_ID

    db = SessionLocal()
    try:
        task_record = db.query(Task).filter(Task.task_id == self.request.id).first()
        if task_record:
            task_record.status = "RUNNING"
            db.commit()

        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise Exception("Analysis not found.")

        analysis_data = {
            "document_id": analysis.document_id, "risk_score": analysis.risk_score,
            "risk_level": analysis.risk_level, "risk_summary": analysis.risk_summary,
            "summary": analysis.summary, "clauses": analysis.clauses_json or [],
            "entities": analysis.entities_json, "recommendations": analysis.recommendations_json or [],
        }

        reports_dir = Path(settings.UPLOAD_DIR) / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        file_id = uuid.uuid4().hex[:12]

        if report_type == "pdf":
            content = generate_pdf_report(analysis_data)
            file_path = reports_dir / f"report_{file_id}.pdf"
            file_path.write_bytes(content)
        elif report_type == "html":
            content = generate_html_report(analysis_data)
            file_path = reports_dir / f"report_{file_id}.html"
            file_path.write_text(content, encoding="utf-8")
        elif report_type == "json":
            content = generate_json_report(analysis_data)
            file_path = reports_dir / f"report_{file_id}.json"
            file_path.write_text(json.dumps(content, indent=2), encoding="utf-8")
        elif report_type == "excel":
            content = export_to_excel([analysis_data])
            file_path = reports_dir / f"report_{file_id}.xlsx"
            file_path.write_bytes(content)
        else:
            raise Exception("Unsupported report type.")

        report = Report(user_id=DEFAULT_USER_ID, analysis_id=analysis_id, report_type=report_type, file_path=str(file_path))
        db.add(report)
        db.commit()

        if task_record:
            task_record.status = "COMPLETED"
            task_record.result = {"report_id": report.id, "file_path": str(file_path)}
            db.commit()

        return {"status": "success", "report_id": report.id}
    except Exception as e:
        if task_record:
            task_record.status = "FAILED"
            task_record.error = str(e)
            db.commit()
        raise e
    finally:
        db.close()
