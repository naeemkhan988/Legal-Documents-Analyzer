"""
Service - Text Cleaner
========================
Pre-processing pipeline that normalises and cleans raw text extracted
from legal documents before it is sent to NLP / embedding / LLM stages.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import List

from backend.utils.decorators import log_execution

logger = logging.getLogger(__name__)


def remove_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters into single spaces and strip."""
    return re.sub(r"\s+", " ", text).strip()


def normalize_text(text: str) -> str:
    """Unicode-normalise, strip control characters, and fix smart quotes."""
    # NFC normalisation
    text = unicodedata.normalize("NFC", text)
    # Replace smart quotes / dashes with ASCII equivalents
    replacements = {
        "\u2018": "'", "\u2019": "'",  # single curly quotes
        "\u201c": '"', "\u201d": '"',  # double curly quotes
        "\u2013": "-", "\u2014": "-",  # en-dash, em-dash
        "\u2026": "...",               # ellipsis
        "\u00a0": " ",                 # non-breaking space
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove control characters (keep newlines and tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text


def remove_special_chars(text: str) -> str:
    """Remove characters that add no semantic value for NLP.

    Keeps letters, digits, basic punctuation, and whitespace.
    """
    return re.sub(r"[^\w\s.,;:!?'\"\-/()\[\]@#$%&*+=<>]", "", text)


def remove_headers_footers(text: str) -> str:
    """Heuristic removal of repeated page headers / footers.

    Looks for lines that appear verbatim on many pages (≥3 occurrences)
    and strips them.
    """
    lines = text.split("\n")
    from collections import Counter

    line_counts = Counter(line.strip() for line in lines if line.strip())
    frequent = {line for line, count in line_counts.items() if count >= 3 and len(line) < 120}
    if frequent:
        logger.debug("Removing %d repeated header/footer lines", len(frequent))
    cleaned = [line for line in lines if line.strip() not in frequent]
    return "\n".join(cleaned)


def split_into_chunks(
    text: str,
    chunk_size: int = 512,
    overlap: int = 50,
) -> List[str]:
    """Split cleaned text into overlapping chunks for embedding.

    Parameters
    ----------
    text : str
        The input text.
    chunk_size : int
        Target chunk size in characters.
    overlap : int
        Number of overlapping characters between consecutive chunks.

    Returns
    -------
    List[str]
        List of text chunks.
    """
    if not text:
        return []

    # Try to split on sentence boundaries first
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for sentence in sentences:
        s_len = len(sentence)
        if current_len + s_len > chunk_size and current:
            chunks.append(" ".join(current))
            # Retain overlap
            overlap_sents: List[str] = []
            ol = 0
            for s in reversed(current):
                if ol + len(s) > overlap:
                    break
                overlap_sents.insert(0, s)
                ol += len(s)
            current = overlap_sents
            current_len = ol
        current.append(sentence)
        current_len += s_len

    if current:
        chunks.append(" ".join(current))

    logger.info("Split text (%d chars) into %d chunks (size=%d, overlap=%d)",
                len(text), len(chunks), chunk_size, overlap)
    return chunks


@log_execution
def clean_for_analysis(text: str) -> str:
    """Run the full cleaning pipeline on raw extracted text.

    Steps:
    1. Unicode normalisation
    2. Remove headers / footers
    3. Collapse whitespace
    4. Remove stray special characters

    Returns
    -------
    str
        Cleaned text ready for NLP / embedding.
    """
    text = normalize_text(text)
    text = remove_headers_footers(text)
    text = remove_whitespace(text)
    text = remove_special_chars(text)
    logger.info("Cleaned text: %d characters", len(text))
    return text
