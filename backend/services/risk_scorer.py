"""
Service - Risk Scorer
=======================
Advanced Risk Scoring with hybrid rule-based and LLM judgment.
"""

from __future__ import annotations

import logging
import json
from typing import List, Dict

from backend.services.clause_extractor import ExtractedClause, detect_missing_clauses
from backend.utils.constants import ClauseType, RiskLevel
from backend.utils.decorators import log_execution

logger = logging.getLogger(__name__)

_RISKY_KEYWORDS: dict[str, list[str]] = {
    ClauseType.LIABILITY_LIMITATION: ["unlimited liability", "no cap", "full liability"],
    ClauseType.TERMINATION: ["immediate termination", "without cause", "sole discretion"],
    ClauseType.INDEMNIFICATION: ["unlimited indemnification", "broad indemnity", "full indemnification"],
    ClauseType.WARRANTIES: ["as-is", "no warranty", "disclaim all warranties"],
    ClauseType.CONFIDENTIALITY: ["perpetual", "unlimited duration", "survive indefinitely"],
    ClauseType.NON_COMPETE: ["worldwide", "indefinite", "all industries"],
    ClauseType.FORCE_MAJEURE: ["not excused", "no relief"],
    ClauseType.GOVERNING_LAW: ["foreign jurisdiction", "unfavorable venue"],
}


def get_risk_level(score: float) -> str:
    if score >= 70: return RiskLevel.RED
    elif score >= 40: return RiskLevel.YELLOW
    return RiskLevel.GREEN


def get_risk_level_for_score(score: float) -> str:
    if score >= 0.7: return RiskLevel.RED
    elif score >= 0.4: return RiskLevel.YELLOW
    return RiskLevel.GREEN


def rule_based_score(clause_text: str, clause_type: str) -> float:
    base_risk = 0.3
    text_lower = clause_text.lower()
    for keyword in _RISKY_KEYWORDS.get(clause_type, []):
        if keyword in text_lower: base_risk += 0.15
    for term in ["sole discretion", "without limitation", "irrevocable", "binding arbitration"]:
        if term in text_lower: base_risk += 0.08
    for term in ["mutual", "reasonable", "written consent", "good faith"]:
        if term in text_lower: base_risk -= 0.05
    return max(0.0, min(1.0, base_risk))


def hybrid_score_clause(clause: ExtractedClause) -> float:
    """Use rule-based scoring plus LLM if confidence is low."""
    from backend.services.llm_service import generate_text
    from backend.utils.prompts import CLAUSE_ANALYSIS_PROMPT
    
    rule_score = rule_based_score(clause.text, clause.clause_type)
    
    if clause.confidence > 0.8:
        return rule_score

    # Use LLM for deeper judgment
    prompt = CLAUSE_ANALYSIS_PROMPT.format(clause_type=clause.clause_type, text=clause.text[:1000])
    try:
        llm_resp = generate_text(prompt, max_tokens=300)
        # Parse JSON
        start = llm_resp.find('{')
        end = llm_resp.rfind('}') + 1
        data = json.loads(llm_resp[start:end])
        llm_score = float(data.get("risk_score", rule_score))
        clause.suggested_change = data.get("explanation")
        clause.obligations = data.get("obligations", [])
        
        # Hybrid average
        return round((rule_score + llm_score) / 2, 2)
    except Exception:
        return rule_score


@log_execution
def score_document(clauses: List[ExtractedClause]) -> float:
    if not clauses: return 50.0

    scores = []
    for clause in clauses:
        clause_score = hybrid_score_clause(clause)
        clause.risk_level = get_risk_level_for_score(clause_score)
        scores.append(clause_score)

    weighted_sum = sum(s ** 1.5 for s in scores)
    weighted_count = sum(s ** 0.5 for s in scores) or 1.0
    return round((weighted_sum / weighted_count) * 100, 1)


def explain_risk(clauses: List[ExtractedClause], risk_score: float) -> str:
    level = get_risk_level(risk_score)
    red = [c for c in clauses if c.risk_level == RiskLevel.RED]
    yellow = [c for c in clauses if c.risk_level == RiskLevel.YELLOW]
    
    found_types = list(set([c.clause_type for c in clauses]))
    missing = detect_missing_clauses(found_types)

    summary = [
        f"Overall Risk Score: {risk_score:.1f}/100 ({level})",
        f"Total clauses analysed: {len(clauses)}",
        f"Missing critical clauses: {', '.join(missing) if missing else 'None'}"
    ]
    if red:
        summary.append("\nHigh-risk items:")
        for c in red[:5]:
            exp = f" - Reason: {c.suggested_change}" if c.suggested_change else ""
            summary.append(f"  - [{c.clause_type}] {c.text[:100]}…{exp}")
    if yellow:
        summary.append("\nMedium-risk items:")
        for c in yellow[:5]:
            summary.append(f"  - [{c.clause_type}] {c.text[:100]}…")
    return "\n".join(summary)
