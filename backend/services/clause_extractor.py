"""
Service - Clause Extractor
============================
Detects and extracts 14+ types of legal clauses from contract text
using a combination of NLP pattern matching (spaCy + regex) and
heuristic confidence scoring.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from backend.utils.constants import ALL_CLAUSE_TYPES, ClauseType
from backend.utils.decorators import log_execution
from backend.utils.exceptions import AnalysisError

logger = logging.getLogger(__name__)

# ── spaCy model cache ─────────────────────────────────────────────────
_nlp = None


def _load_spacy():
    """Load spaCy English model (sm for speed, md/lg for accuracy)."""
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        import spacy

        for model in ("en_core_web_sm", "en_core_web_md"):
            try:
                _nlp = spacy.load(model)
                logger.info("Loaded spaCy model: %s", model)
                return _nlp
            except OSError:
                continue
        # Final fallback: blank model
        _nlp = spacy.blank("en")
        logger.warning("Using blank spaCy model — install en_core_web_sm for better results")
        return _nlp
    except ImportError:
        logger.warning("spaCy not installed — clause extraction will rely on regex only")
        return None


# ── Clause Pattern Definitions ────────────────────────────────────────

# Each pattern maps a clause type to a list of regex patterns that
# typically introduce that clause in legal documents.
CLAUSE_PATTERNS: Dict[str, List[str]] = {
    ClauseType.LIABILITY_LIMITATION: [
        r"(?i)(limitation\s+of\s+liability|liability\s+shall\s+(not\s+)?exceed|"
        r"aggregate\s+liability|total\s+liability|cap\s+on\s+liability)",
    ],
    ClauseType.TERMINATION: [
        r"(?i)(termination|terminate\s+this\s+agreement|right\s+to\s+terminate|"
        r"upon\s+termination|termination\s+for\s+cause|termination\s+for\s+convenience|"
        r"either\s+party\s+may\s+terminate)",
    ],
    ClauseType.PAYMENT_TERMS: [
        r"(?i)(payment\s+terms|payment\s+shall\s+be|payable\s+within|"
        r"invoice|net\s+\d+\s+days|payment\s+schedule|compensation|"
        r"fee\s+schedule|billing)",
    ],
    ClauseType.CONFIDENTIALITY: [
        r"(?i)(confidential\s+information|non-disclosure|confidentiality|"
        r"proprietary\s+information|trade\s+secret|shall\s+not\s+disclose|"
        r"keep\s+confidential)",
    ],
    ClauseType.INDEMNIFICATION: [
        r"(?i)(indemnif|hold\s+harmless|defend\s+and\s+indemnify|"
        r"indemnification\s+obligations|shall\s+indemnify)",
    ],
    ClauseType.WARRANTIES: [
        r"(?i)(warrant(y|ies)|represents?\s+and\s+warrants?|"
        r"as-is|without\s+warranty|disclaimer\s+of\s+warranties|"
        r"no\s+warranty|merchantability|fitness\s+for\s+a\s+particular\s+purpose)",
    ],
    ClauseType.LIMITATION_OF_LIABILITY: [
        r"(?i)(in\s+no\s+event\s+shall|shall\s+not\s+be\s+liable|"
        r"exclusion\s+of\s+(consequential|indirect)\s+damages|"
        r"no\s+liability\s+for|maximum\s+liability)",
    ],
    ClauseType.FORCE_MAJEURE: [
        r"(?i)(force\s+majeure|act\s+of\s+god|beyond\s+(the\s+)?reasonable\s+control|"
        r"unforeseeable\s+circumstances|natural\s+disaster|pandemic|epidemic)",
    ],
    ClauseType.SEVERABILITY: [
        r"(?i)(severab|if\s+any\s+provision.*invalid|"
        r"remaining\s+provisions\s+shall\s+remain|"
        r"unenforceable\s+provision)",
    ],
    ClauseType.GOVERNING_LAW: [
        r"(?i)(governing\s+law|governed\s+by\s+the\s+laws|"
        r"jurisdiction|applicable\s+law|venue\s+shall\s+be|"
        r"courts?\s+of\s+competent\s+jurisdiction)",
    ],
    ClauseType.INTELLECTUAL_PROPERTY: [
        r"(?i)(intellectual\s+property|patent|copyright|trademark|"
        r"proprietary\s+rights|ownership\s+of\s+work\s+product|"
        r"ip\s+rights|license\s+grant)",
    ],
    ClauseType.NON_COMPETE: [
        r"(?i)(non-compete|non\s+compete|restrictive\s+covenant|"
        r"shall\s+not\s+compete|competitive\s+activity|"
        r"non-solicitation|non\s+solicitation)",
    ],
    ClauseType.DISPUTE_RESOLUTION: [
        r"(?i)(dispute\s+resolution|arbitration|mediation|"
        r"shall\s+be\s+resolved|binding\s+arbitration|"
        r"dispute\s+settlement)",
    ],
    ClauseType.ASSIGNMENT: [
        r"(?i)(assignment|shall\s+not\s+assign|assignable|"
        r"transfer\s+of\s+rights|delegation\s+of\s+duties|"
        r"may\s+not\s+assign)",
    ],
}


@dataclass
class ExtractedClause:
    """Data class for a single extracted clause."""
    clause_type: str
    text: str
    start: int = 0
    end: int = 0
    confidence: float = 0.0
    risk_level: Optional[str] = None
    suggested_change: Optional[str] = None


def _extract_sentence_around_match(
    text: str, match_start: int, match_end: int, context_chars: int = 500
) -> Tuple[str, int, int]:
    """Extract a sentence / paragraph around a regex match with context."""
    start = max(0, match_start - context_chars)
    end = min(len(text), match_end + context_chars)

    # Expand to sentence boundaries
    while start > 0 and text[start] not in ".!?\n":
        start -= 1
    if start > 0:
        start += 1  # skip the period

    while end < len(text) and text[end] not in ".!?\n":
        end += 1
    if end < len(text):
        end += 1  # include the period

    return text[start:end].strip(), start, end


def _compute_confidence(text: str, clause_type: str) -> float:
    """Heuristic confidence score based on keyword density and length."""
    patterns = CLAUSE_PATTERNS.get(clause_type, [])
    if not patterns:
        return 0.5

    match_count = sum(
        len(re.findall(pat, text, re.IGNORECASE))
        for pat in patterns
    )

    # Longer text with more matches → higher confidence
    length_factor = min(1.0, len(text) / 200)
    match_factor = min(1.0, match_count / 3)
    confidence = 0.4 + 0.3 * match_factor + 0.3 * length_factor
    return round(min(confidence, 0.99), 2)


def detect_clauses_by_type(text: str, clause_type: str) -> List[ExtractedClause]:
    """Find all occurrences of a specific clause type in *text*."""
    patterns = CLAUSE_PATTERNS.get(clause_type, [])
    clauses: List[ExtractedClause] = []
    seen_spans: set = set()

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            excerpt, start, end = _extract_sentence_around_match(
                text, match.start(), match.end()
            )
            # De-duplicate overlapping spans
            span_key = (start // 100, end // 100)
            if span_key in seen_spans:
                continue
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


def identify_clause_boundaries(text: str) -> List[Tuple[int, int]]:
    """Identify logical clause boundaries using common section headers.

    Returns a list of (start, end) character offsets.
    """
    # Common legal section header patterns
    section_pattern = re.compile(
        r"(?:^|\n)\s*(?:\d+\.?\s+|[A-Z]+\.\s+|ARTICLE\s+\w+|SECTION\s+\d+|"
        r"CLAUSE\s+\d+)[:\.\s]",
        re.MULTILINE,
    )
    matches = list(section_pattern.finditer(text))

    boundaries: List[Tuple[int, int]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        boundaries.append((start, end))

    return boundaries


@log_execution
def extract_all_clauses(text: str) -> List[ExtractedClause]:
    """Run clause extraction for all known clause types.

    Parameters
    ----------
    text : str
        Cleaned document text.

    Returns
    -------
    List[ExtractedClause]
        All detected clauses, de-duplicated and sorted by position.
    """
    if not text:
        return []

    all_clauses: List[ExtractedClause] = []

    for clause_type in ALL_CLAUSE_TYPES:
        found = detect_clauses_by_type(text, clause_type)
        all_clauses.extend(found)
        if found:
            logger.debug("Found %d %s clause(s)", len(found), clause_type)

    # Sort by position in document
    all_clauses.sort(key=lambda c: c.start)

    logger.info("Extracted %d total clauses from document (%d chars)", len(all_clauses), len(text))
    return all_clauses
