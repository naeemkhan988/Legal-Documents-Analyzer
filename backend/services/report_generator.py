"""
Service - Report Generator
=============================
Generates PDF, HTML, JSON, and Excel reports from analysis results.
"""

from __future__ import annotations

import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from backend.config import settings
from backend.utils.decorators import log_execution

logger = logging.getLogger(__name__)


@log_execution
def generate_pdf_report(analysis: Dict[str, Any]) -> bytes:
    """Generate a PDF report using ReportLab."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
        )
    except ImportError:
        logger.error("ReportLab not installed")
        return b""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=18, spaceAfter=20)
    elements.append(Paragraph("Legal Document Analysis Report", title_style))
    elements.append(Spacer(1, 12))

    # Risk Score
    risk_score = analysis.get("risk_score", "N/A")
    risk_level = analysis.get("risk_level", "N/A")
    elements.append(Paragraph(f"<b>Risk Score:</b> {risk_score}/100 ({risk_level})", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Summary
    summary = analysis.get("summary", "No summary available.")
    elements.append(Paragraph("<b>Summary:</b>", styles["Heading2"]))
    elements.append(Paragraph(summary[:2000], styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Clauses table
    clauses = analysis.get("clauses", [])
    if clauses:
        elements.append(Paragraph("<b>Extracted Clauses:</b>", styles["Heading2"]))
        table_data = [["Type", "Risk", "Confidence", "Excerpt"]]
        for c in clauses[:20]:
            ctype = c.get("clause_type", c.get("type", ""))
            risk = c.get("risk_level", "")
            conf = f"{c.get('confidence', 0):.0%}"
            text = (c.get("text", ""))[:80] + "…"
            table_data.append([ctype, risk, conf, text])

        t = Table(table_data, colWidths=[1.3 * inch, 0.8 * inch, 0.8 * inch, 3.5 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

    # Recommendations
    recs = analysis.get("recommendations", [])
    if recs:
        elements.append(Paragraph("<b>Recommendations:</b>", styles["Heading2"]))
        for r in recs[:10]:
            elements.append(Paragraph(f"• {r}", styles["Normal"]))

    doc.build(elements)
    return buffer.getvalue()


@log_execution
def generate_html_report(analysis: Dict[str, Any]) -> str:
    """Generate an HTML report."""
    risk_score = analysis.get("risk_score", "N/A")
    risk_level = analysis.get("risk_level", "N/A")
    summary = analysis.get("summary", "")
    clauses = analysis.get("clauses", [])
    recs = analysis.get("recommendations", [])

    color_map = {"RED": "#ef4444", "YELLOW": "#eab308", "GREEN": "#22c55e"}
    risk_color = color_map.get(str(risk_level), "#666")

    clauses_html = ""
    for c in clauses[:20]:
        ctype = c.get("clause_type", c.get("type", ""))
        c_risk = c.get("risk_level", "")
        c_color = color_map.get(c_risk, "#666")
        clauses_html += f"""
        <tr>
            <td>{ctype}</td>
            <td><span style="color:{c_color};font-weight:bold">{c_risk}</span></td>
            <td>{c.get('confidence', 0):.0%}</td>
            <td>{(c.get('text', ''))[:120]}…</td>
        </tr>"""

    recs_html = "".join(f"<li>{r}</li>" for r in recs[:10])

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Legal Analysis Report</title>
<style>
body{{font-family:Inter,sans-serif;max-width:900px;margin:auto;padding:20px;color:#1a1a2e}}
h1{{color:#1a1a2e}} table{{width:100%;border-collapse:collapse;margin:1em 0}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left;font-size:14px}}
th{{background:#1a1a2e;color:white}} .score{{font-size:2em;font-weight:bold;color:{risk_color}}}
</style></head><body>
<h1>Legal Document Analysis Report</h1>
<p class="score">{risk_score}/100 — {risk_level}</p>
<h2>Summary</h2><p>{summary}</p>
<h2>Extracted Clauses</h2>
<table><tr><th>Type</th><th>Risk</th><th>Confidence</th><th>Excerpt</th></tr>{clauses_html}</table>
<h2>Recommendations</h2><ul>{recs_html}</ul>
</body></html>"""


def generate_json_report(analysis: Dict[str, Any]) -> Dict:
    """Return the analysis data as a structured JSON-serialisable dict."""
    return {
        "report_type": "json",
        "risk_score": analysis.get("risk_score"),
        "risk_level": analysis.get("risk_level"),
        "summary": analysis.get("summary"),
        "clauses": analysis.get("clauses", []),
        "entities": analysis.get("entities"),
        "recommendations": analysis.get("recommendations", []),
    }


@log_execution
def export_to_excel(analyses: List[Dict[str, Any]]) -> bytes:
    """Export multiple analyses to an Excel file using pandas."""
    try:
        import pandas as pd

        rows = []
        for a in analyses:
            for c in a.get("clauses", []):
                rows.append({
                    "Document": a.get("document_id", ""),
                    "Risk Score": a.get("risk_score", ""),
                    "Clause Type": c.get("clause_type", c.get("type", "")),
                    "Risk Level": c.get("risk_level", ""),
                    "Confidence": c.get("confidence", 0),
                    "Text": (c.get("text", ""))[:200],
                })

        df = pd.DataFrame(rows)
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        return buffer.getvalue()
    except ImportError:
        # Fallback: return CSV bytes
        import csv
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=["Document", "Risk Score", "Clause Type", "Risk Level", "Confidence", "Text"])
        writer.writeheader()
        for a in analyses:
            for c in a.get("clauses", []):
                writer.writerow({
                    "Document": a.get("document_id", ""),
                    "Risk Score": a.get("risk_score", ""),
                    "Clause Type": c.get("clause_type", ""),
                    "Risk Level": c.get("risk_level", ""),
                    "Confidence": c.get("confidence", 0),
                    "Text": (c.get("text", ""))[:200],
                })
        return buffer.getvalue().encode()
