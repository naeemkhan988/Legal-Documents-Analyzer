"""
Service - Clause Extractor
============================
Detects and extracts 14+ types of legal clauses from contract text
using NLP pattern matching and obligation extraction.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from backend.utils.constants import ALL_CLAUSE_TYPES, ClauseType
from backend.utils.decorators import log_execution

logger = logging.getLogger(__name__)

CLAUSE_PATTERNS: Dict[str, List[str]] = {
    ClauseType.LIABILITY_LIMITATION: [r"(?i)(limitation\s+of\s+liability|liability\s+shall\s+(not\s+)?exceed|aggregate\s+liability|total\s+liability|cap\s+on\s+liability)"],
    ClauseType.TERMINATION: [r"(?i)(termination|terminate\s+this\s+agreement|right\s+to\s+terminate|upon\s+termination|termination\s+for\s+cause|termination\s+for\s+convenience|either\s+party\s+may\s+terminate)"],
    ClauseType.PAYMENT_TERMS: [r"(?i)(payment\s+terms|payment\s+shall\s+be|payable\s+within|invoice|net\s+\d+\s+days|payment\s+schedule|compensation|fee\s+schedule|billing)"],
    ClauseType.CONFIDENTIALITY: [r"(?i)(confidential\s+information|non-disclosure|confidentiality|proprietary\s+information|trade\s+secret|shall\s+not\s+disclose|keep\s+confidential)"],
    ClauseType.INDEMNIFICATION: [r"(?i)(indemnif|hold\s+harmless|defend\s+and\s+indemnify|indemnification\s+obligations|shall\s+indemnify)"],
    ClauseType.WARRANTIES: [r"(?i)(warrant(y|ies)|represents?\s+and\s+warrants?|as-is|without\s+warranty|disclaimer\s+of\s+warranties|no\s+warranty|merchantability|fitness\s+for\s+a\s+particular\s+purpose)"],
    ClauseType.LIMITATION_OF_LIABILITY: [r"(?i)(in\s+no\s+event\s+shall|shall\s+not\s+be\s+liable|exclusion\s+of\s+(consequential|indirect)\s+damages|no\s+liability\s+for|maximum\s+liability)"],
    ClauseType.FORCE_MAJEURE: [r"(?i)(force\s+majeure|act\s+of\s+god|beyond\s+(the\s+)?reasonable\s+control|unforeseeable\s+circumstances|natural\s+disaster|pandemic|epidemic)"],
    ClauseType.SEVERABILITY: [r"(?i)(severab|if\s+any\s+provision.*invalid|remaining\s+provisions\s+shall\s+remain|unenforceable\s+provision)"],
    ClauseType.GOVERNING_LAW: [r"(?i)(governing\s+law|governed\s+by\s+the\s+laws|jurisdiction|applicable\s+law|venue\s+shall\s+be|courts?\s+of\s+competent\s+jurisdiction)"],
    ClauseType.INTELLECTUAL_PROPERTY: [r"(?i)(intellectual\s+property|patent|copyright|trademark|proprietary\s+rights|ownership\s+of\s+work\s+product|ip\s+rights|license\s+grant)"],
    ClauseType.NON_COMPETE: [r"(?i)(non-compete|non\s+compete|restrictive\s+covenant|shall\s+not\s+compete|competitive\s+activity|non-solicitation|non\s+solicitation)"],
    ClauseType.DISPUTE_RESOLUTION: [r"(?i)(dispute\s+resolution|arbitration|mediation|shall\s+be\s+resolved|binding\s+arbitration|dispute\s+settlement)"],
    ClauseType.ASSIGNMENT: [r"(?i)(assignment|shall\s+not\s+assign|assignable|transfer\s+of\s+rights|delegation\s+of\s+duties|may\s+not\s+assign)"],
}


@dataclass
class ExtractedClause:
    clause_type: str
    text: str
    start: int = 0
    end: int = 0
    confidence: float = 0.0
    risk_level: Optional[str] = None
    suggested_change: Optional[str] = None
    obligations: List[str] = field(default_factory=list)


def _extract_sentence_around_match(text: str, match_start: int, match_end: int, context_chars: int = 500) -> Tuple[str, int, int]:
    start = max(0, match_start - context_chars)
    end = min(len(text), match_end + context_chars)
    while start > 0 and text[start] not in ".!?\n": start -= 1
    if start > 0: start += 1
    while end < len(text) and text[end] not in ".!?\n": end += 1
    if end < len(text): end += 1
    return text[start:end].strip(), start, end


def _compute_confidence(text: str, clause_type: str) -> float:
    patterns = CLAUSE_PATTERNS.get(clause_type, [])
    if not patterns: return 0.5
    match_count = sum(len(re.findall(pat, text, re.IGNORECASE)) for pat in patterns)
    length_factor = min(1.0, len(text) / 200)
    match_factor = min(1.0, match_count / 3)
    return round(min(0.4 + 0.3 * match_factor + 0.3 * length_factor, 0.99), 2)


def detect_clauses_by_type(text: str, clause_type: str) -> List[ExtractedClause]:
    patterns = CLAUSE_PATTERNS.get(clause_type, [])
    clauses: List[ExtractedClause] = []
    seen_spans: set = set()

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            excerpt, start, end = _extract_sentence_around_match(text, match.start(), match.end())
            span_key = (start // 100, end // 100)
            if span_key in seen_spans: continue
            seen_spans.add(span_key)
            confidence = _compute_confidence(excerpt, clause_type)
            clauses.append(ExtractedClause(
                clause_type=clause_type,
                text=excerpt,
                start=start,
                end=end,
                confidence=confidence,
            ))
    return clauses


@log_execution
def extract_all_clauses(text: str) -> List[ExtractedClause]:
    if not text: return []
    all_clauses: List[ExtractedClause] = []
    for clause_type in ALL_CLAUSE_TYPES:
        all_clauses.extend(detect_clauses_by_type(text, clause_type))
    all_clauses.sort(key=lambda c: c.start)
    return all_clauses

def detect_missing_clauses(found_clause_types: List[str]) -> List[str]:
    from backend.services.llm_service import generate_text
    from backend.utils.prompts import MISSING_CLAUSE_PROMPT
    import json
    
    prompt = MISSING_CLAUSE_PROMPT.format(
        found_clauses=", ".join(found_clause_types) if found_clause_types else "None",
        all_clauses=", ".join(ALL_CLAUSE_TYPES)
    )
    try:
        response = generate_text(prompt, max_tokens=200)
        missing = json.loads(response)
        return [c for c in missing if isinstance(c, str)]
    except Exception:
        # Fallback to simple rule-based missing detection
        essential = [ClauseType.GOVERNING_LAW, ClauseType.TERMINATION, ClauseType.LIABILITY_LIMITATION, ClauseType.CONFIDENTIALITY]
        return [c for c in essential if c not in found_clause_types]
