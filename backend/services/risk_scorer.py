"""
Service - Risk Scorer
=======================
Scores individual clauses and full documents on a 0-100 risk scale,
mapping to RED / YELLOW / GREEN risk levels.
"""

from __future__ import annotations

import logging
import re
from typing import List

from backend.services.clause_extractor import ExtractedClause
from backend.utils.constants import ClauseType, RiskLevel
from backend.utils.decorators import log_execution

logger = logging.getLogger(__name__)

# High-risk keywords by clause type
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


def score_clause(clause_text: str, clause_type: str) -> float:
    """Score a single clause on a 0.0–1.0 risk scale.

    Higher = riskier.
    """
    base_risk = 0.3  # neutral baseline
    text_lower = clause_text.lower()

    # Check risky keywords
    risky_words = _RISKY_KEYWORDS.get(clause_type, [])
    for keyword in risky_words:
        if keyword in text_lower:
            base_risk += 0.15

    # Generic high-risk language
    generic_risky = [
        "sole discretion", "without limitation", "irrevocable",
        "unconditional", "shall not be liable", "waive any claim",
        "automatically renew", "binding arbitration", "liquidated damages",
    ]
    for term in generic_risky:
        if term in text_lower:
            base_risk += 0.08

    # Favorable language reduces risk
    favorable = [
        "mutual", "reasonable", "commercially reasonable", "written consent",
        "good faith", "reasonable notice", "cure period", "30 days",
    ]
    for term in favorable:
        if term in text_lower:
            base_risk -= 0.05

    return round(max(0.0, min(1.0, base_risk)), 2)


@log_execution
def score_document(clauses: List[ExtractedClause]) -> float:
    """Aggregate clause scores into a document-level risk score (0–100).

    Weights high-risk clauses more heavily.
    """
    if not clauses:
        return 50.0  # Unknown / neutral when no clauses found

    scores: list[float] = []
    for clause in clauses:
        clause_score = score_clause(clause.text, clause.clause_type)
        clause.risk_level = get_risk_level_for_score(clause_score)
        scores.append(clause_score)

    # Weighted average: higher scores get more weight
    weighted_sum = sum(s ** 1.5 for s in scores)
    weighted_count = sum(s ** 0.5 for s in scores) or 1.0
    avg = weighted_sum / weighted_count

    document_score = round(avg * 100, 1)
    logger.info("Document risk score: %.1f/100 from %d clauses", document_score, len(clauses))
    return document_score


def get_risk_level(score: float) -> str:
    """Map a 0–100 document score to a risk level string."""
    if score >= 70:
        return RiskLevel.RED
    elif score >= 40:
        return RiskLevel.YELLOW
    return RiskLevel.GREEN


def get_risk_level_for_score(score: float) -> str:
    """Map a 0–1 clause score to a risk level string."""
    if score >= 0.7:
        return RiskLevel.RED
    elif score >= 0.4:
        return RiskLevel.YELLOW
    return RiskLevel.GREEN


def explain_risk(clauses: List[ExtractedClause], risk_score: float) -> str:
    """Generate a human-readable risk summary."""
    level = get_risk_level(risk_score)
    red_clauses = [c for c in clauses if c.risk_level == RiskLevel.RED]
    yellow_clauses = [c for c in clauses if c.risk_level == RiskLevel.YELLOW]

    summary_parts = [
        f"Overall Risk Score: {risk_score:.1f}/100 ({level})",
        f"Total clauses analysed: {len(clauses)}",
        f"High-risk clauses (RED): {len(red_clauses)}",
        f"Medium-risk clauses (YELLOW): {len(yellow_clauses)}",
    ]

    if red_clauses:
        summary_parts.append("\nHigh-risk items:")
        for c in red_clauses[:5]:
            summary_parts.append(f"  - [{c.clause_type}] {c.text[:100]}…")

    if yellow_clauses:
        summary_parts.append("\nMedium-risk items:")
        for c in yellow_clauses[:5]:
            summary_parts.append(f"  - [{c.clause_type}] {c.text[:100]}…")

    return "\n".join(summary_parts)
