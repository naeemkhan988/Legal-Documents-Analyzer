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
    text = unicodedata.normalize("NFC", text)
    replacements = {
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-",
        "\u2026": "...",
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text


def remove_special_chars(text: str) -> str:
    return re.sub(r"[^\w\s.,;:!?'\"\-/()\[\]@#$%&*+=<>]", "", text)


def remove_headers_footers(text: str) -> str:
    lines = text.split("\n")
    from collections import Counter
    line_counts = Counter(line.strip() for line in lines if line.strip())
    frequent = {line for line, count in line_counts.items() if count >= 3 and len(line) < 120}
    cleaned = [line for line in lines if line.strip() not in frequent]
    return "\n".join(cleaned)


def split_into_chunks(
    text: str,
    chunk_size: int = 512,
    overlap: int = 50,
) -> List[str]:
    """Intelligent legal-aware chunking."""
    if not text:
        return []

    # Regex to identify legal sections/clauses (e.g. "1.", "1.1", "Article 1", "Section A")
    section_pattern = re.compile(
        r"^(?:(?:Article|Section|Clause)\s+[A-Z0-9]+|(?:\d+\.)+\d*)\s+",
        re.IGNORECASE | re.MULTILINE
    )
    
    # Split by paragraphs or sections
    raw_segments = re.split(r"\n{2,}|\.\s+(?=[A-Z])", text)
    
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_len = 0

    for seg in raw_segments:
        seg = seg.strip()
        if not seg:
            continue
            
        seg_len = len(seg)
        # If adding this segment exceeds chunk size, and we already have content
        if current_len + seg_len > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            
            # Handle overlap
            overlap_words = current_chunk[-1].split()[-overlap:] if current_chunk else []
            current_chunk = [" ".join(overlap_words)] if overlap_words else []
            current_len = len(current_chunk[0]) if current_chunk else 0

        current_chunk.append(seg)
        current_len += seg_len

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    logger.info("Split text (%d chars) into %d intelligent chunks", len(text), len(chunks))
    return chunks


@log_execution
def clean_for_analysis(text: str) -> str:
    """Run the full cleaning pipeline on raw extracted text."""
    text = normalize_text(text)
    text = remove_headers_footers(text)
    # text = remove_whitespace(text) # Let's preserve paragraphs for better chunking
    text = remove_special_chars(text)
    return text
