"""
Service - Report Generator
=============================
Generates PDF, HTML, JSON, and Excel reports from analysis results.
Uses WeasyPrint for high-quality PDF generation.
"""

from __future__ import annotations

import io
import json
import logging
from typing import Any, Dict, List

from backend.utils.decorators import log_execution

logger = logging.getLogger(__name__)


@log_execution
def generate_pdf_report(analysis: Dict[str, Any]) -> bytes:
    """Generate a high-quality PDF report using WeasyPrint."""
    try:
        from weasyprint import HTML
    except ImportError:
        logger.error("WeasyPrint not installed. Falling back to empty PDF.")
        return b""

    html_content = generate_html_report(analysis)
    return HTML(string=html_content).write_pdf()


@log_execution
def generate_html_report(analysis: Dict[str, Any]) -> str:
    """Generate an interactive HTML report."""
    risk_score = analysis.get("risk_score", "N/A")
    risk_level = analysis.get("risk_level", "N/A")
    summary = analysis.get("summary", "")
    clauses = analysis.get("clauses", [])
    recs = analysis.get("recommendations", [])

    color_map = {"RED": "#ef4444", "YELLOW": "#eab308", "GREEN": "#22c55e"}
    risk_color = color_map.get(str(risk_level), "#666")

    clauses_html = ""
    for c in clauses:
        ctype = c.get("clause_type", c.get("type", ""))
        c_risk = c.get("risk_level", "")
        c_color = color_map.get(c_risk, "#666")
        obligations = ", ".join(c.get("obligations", []))
        if not obligations: obligations = "None identified"
        
        clauses_html += f"""
        <tr>
            <td>{ctype}</td>
            <td><span style="color:{c_color};font-weight:bold">{c_risk}</span></td>
            <td>{c.get('confidence', 0):.0%}</td>
            <td>
                <strong>Excerpt:</strong> {(c.get('text', ''))[:150]}…<br/>
                <strong>Obligations:</strong> {obligations}
            </td>
        </tr>"""

    recs_html = "".join(f"<li>{r}</li>" for r in recs)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Legal Analysis Report</title>
<style>
    @page {{ margin: 1in; }}
    body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 900px; margin: auto; padding: 20px; color: #333; }}
    h1, h2, h3 {{ color: #1a1a2e; }}
    .header {{ border-bottom: 2px solid #1a1a2e; padding-bottom: 10px; margin-bottom: 20px; }}
    .score-container {{ text-align: center; margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }}
    .score {{ font-size: 3em; font-weight: bold; color: {risk_color}; margin: 0; }}
    .score-label {{ font-size: 1.2em; color: #666; text-transform: uppercase; letter-spacing: 1px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; page-break-inside: auto; }}
    tr {{ page-break-inside: avoid; page-break-after: auto; }}
    th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; font-size: 14px; vertical-align: top; }}
    th {{ background: #1a1a2e; color: white; }}
    ul {{ padding-left: 20px; }}
    li {{ margin-bottom: 10px; line-height: 1.5; }}
    p {{ line-height: 1.6; }}
</style>
</head>
<body>
    <div class="header">
        <h1>Legal Document Analysis Report</h1>
        <p>Document ID: {analysis.get('document_id', 'Unknown')}</p>
    </div>
    
    <div class="score-container">
        <p class="score">{risk_score}/100</p>
        <p class="score-label">Risk Level: {risk_level}</p>
    </div>

    <h2>Executive Summary</h2>
    <p>{summary}</p>
    
    <h2>Actionable Recommendations</h2>
    <ul>{recs_html}</ul>

    <h2>Extracted Clauses & Obligations</h2>
    <table>
        <tr>
            <th width="15%">Type</th>
            <th width="10%">Risk</th>
            <th width="10%">Confidence</th>
            <th width="65%">Details</th>
        </tr>
        {clauses_html}
    </table>
</body>
</html>"""


def generate_json_report(analysis: Dict[str, Any]) -> Dict:
    """Return the analysis data as a structured JSON-serialisable dict."""
    return {
        "report_type": "json",
        "document_id": analysis.get("document_id"),
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
                    "Obligations": ", ".join(c.get("obligations", [])),
                    "Text": (c.get("text", ""))[:500],
                })
        df = pd.DataFrame(rows)
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        return buffer.getvalue()
    except ImportError:
        import csv
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=["Document", "Risk Score", "Clause Type", "Risk Level", "Confidence", "Obligations", "Text"])
        writer.writeheader()
        for a in analyses:
            for c in a.get("clauses", []):
                writer.writerow({
                    "Document": a.get("document_id", ""),
                    "Risk Score": a.get("risk_score", ""),
                    "Clause Type": c.get("clause_type", ""),
                    "Risk Level": c.get("risk_level", ""),
                    "Confidence": c.get("confidence", 0),
                    "Obligations": ", ".join(c.get("obligations", [])),
                    "Text": (c.get("text", ""))[:500],
                })
        return buffer.getvalue().encode()
