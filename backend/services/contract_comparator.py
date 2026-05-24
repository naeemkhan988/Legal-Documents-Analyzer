"""
Service - Contract Comparator
================================
Compares two or more legal documents side-by-side by clause type.
"""

from __future__ import annotations

import logging
from difflib import SequenceMatcher, unified_diff
from typing import Any, Dict, List

from backend.services.clause_extractor import extract_all_clauses
from backend.utils.constants import ALL_CLAUSE_TYPES
from backend.utils.decorators import log_execution

logger = logging.getLogger(__name__)


@log_execution
def compare_documents(texts: Dict[str, str]) -> Dict[str, Any]:
    """Compare multiple documents.

    Parameters
    ----------
    texts : dict
        Mapping of document_id → cleaned_text.

    Returns
    -------
    dict
        comparison_result, differences, and similarity_score.
    """
    doc_ids = list(texts.keys())
    if len(doc_ids) < 2:
        return {"error": "Need at least 2 documents to compare."}

    # Extract clauses from each
    doc_clauses: Dict[str, list] = {}
    for did, text in texts.items():
        doc_clauses[did] = extract_all_clauses(text)

    # Pairwise comparison of first two documents
    id_a, id_b = doc_ids[0], doc_ids[1]
    text_a, text_b = texts[id_a], texts[id_b]

    diffs = find_differences(text_a, text_b)
    similarity = SequenceMatcher(None, text_a[:10000], text_b[:10000]).ratio()

    clause_comparison = compare_by_clause_type_internal(doc_clauses)

    return {
        "document_ids": doc_ids,
        "similarity_score": round(similarity, 4),
        "differences": diffs,
        "clause_comparison": clause_comparison,
    }


def find_differences(text1: str, text2: str) -> Dict[str, Any]:
    """Compute a unified diff between two texts."""
    lines1 = text1.split("\n")
    lines2 = text2.split("\n")

    diff = list(unified_diff(lines1, lines2, lineterm="", n=2))
    added = [l[1:] for l in diff if l.startswith("+") and not l.startswith("+++")]
    removed = [l[1:] for l in diff if l.startswith("-") and not l.startswith("---")]

    return {
        "total_changes": len(added) + len(removed),
        "added_lines": len(added),
        "removed_lines": len(removed),
        "added_samples": added[:20],
        "removed_samples": removed[:20],
    }


def highlight_changes(comparison: Dict) -> Dict:
    """Add HTML-style highlighting to diff results."""
    diffs = comparison.get("differences", {})
    highlighted = {
        "added": [f'<span class="added">{line}</span>' for line in diffs.get("added_samples", [])],
        "removed": [f'<span class="removed">{line}</span>' for line in diffs.get("removed_samples", [])],
    }
    return {**comparison, "highlighted": highlighted}


def generate_comparison_summary(comparison: Dict) -> str:
    """Generate a human-readable summary of the comparison."""
    sim = comparison.get("similarity_score", 0)
    diffs = comparison.get("differences", {})
    total = diffs.get("total_changes", 0)

    parts = [
        f"Document Similarity: {sim * 100:.1f}%",
        f"Total changes detected: {total}",
        f"Lines added: {diffs.get('added_lines', 0)}",
        f"Lines removed: {diffs.get('removed_lines', 0)}",
    ]

    clause_comp = comparison.get("clause_comparison", {})
    if clause_comp:
        parts.append("\nClause-level comparison:")
        for ctype, info in clause_comp.items():
            parts.append(f"  {ctype}: {info.get('summary', 'N/A')}")

    return "\n".join(parts)


def compare_by_clause_type_internal(doc_clauses: Dict[str, list]) -> Dict[str, Any]:
    """Compare clauses across documents grouped by type."""
    result: Dict[str, Any] = {}
    doc_ids = list(doc_clauses.keys())

    for clause_type in ALL_CLAUSE_TYPES:
        type_data: Dict[str, list] = {}
        for did in doc_ids:
            matching = [c for c in doc_clauses[did] if c.clause_type == clause_type]
            type_data[did] = [c.text[:200] for c in matching]

        has_any = any(bool(v) for v in type_data.values())
        if has_any:
            all_present = all(bool(v) for v in type_data.values())
            result[clause_type] = {
                "present_in_all": all_present,
                "clauses_by_document": type_data,
                "summary": "Present in all documents" if all_present else "Missing in some documents",
            }

    return result


def compare_by_clause_type(texts: Dict[str, str], clause_type: str) -> Dict[str, Any]:
    """Compare a specific clause type across documents."""
    doc_clauses = {}
    for did, text in texts.items():
        from backend.services.clause_extractor import detect_clauses_by_type
        doc_clauses[did] = detect_clauses_by_type(text, clause_type)

    result: Dict[str, Any] = {"clause_type": clause_type, "documents": {}}
    for did, clauses in doc_clauses.items():
        result["documents"][did] = {
            "count": len(clauses),
            "texts": [c.text[:300] for c in clauses],
            "avg_confidence": sum(c.confidence for c in clauses) / max(len(clauses), 1),
        }

    return result
