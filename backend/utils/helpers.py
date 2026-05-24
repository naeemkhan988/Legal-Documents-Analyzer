"""
Utils - Helper Functions
=========================
Miscellaneous utility functions used across the backend codebase.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List

logger = logging.getLogger(__name__)


def generate_unique_id() -> str:
    """Return a 32-character hex UUID4 string."""
    return uuid.uuid4().hex


def format_timestamp(dt: datetime | None = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a datetime; defaults to *now* in UTC."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime(fmt)


def parse_json_safely(text: str) -> dict | list | None:
    """Attempt to parse JSON from *text*, returning ``None`` on failure.

    The function also handles LLM outputs that wrap JSON in markdown
    code fences (```json ... ```).
    """
    if not text:
        return None

    # Strip markdown fences
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`")

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to extract the first JSON-like structure
        match = re.search(r"[\[{].*[\]}]", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    logger.warning("Failed to parse JSON from text: %.100s…", text)
    return None


def chunk_text(text: str, size: int = 512, overlap: int = 50) -> List[str]:
    """Split *text* into overlapping chunks of approximately *size* characters.

    Chunks are split at sentence boundaries when possible.
    """
    if not text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_length = 0

    for sentence in sentences:
        sentence_len = len(sentence)
        if current_length + sentence_len > size and current_chunk:
            chunks.append(" ".join(current_chunk))
            # Keep overlap by retaining the last few sentences
            overlap_text = " ".join(current_chunk)
            overlap_sentences: List[str] = []
            overlap_len = 0
            for s in reversed(current_chunk):
                if overlap_len + len(s) > overlap:
                    break
                overlap_sentences.insert(0, s)
                overlap_len += len(s)
            current_chunk = overlap_sentences
            current_length = overlap_len

        current_chunk.append(sentence)
        current_length += sentence_len

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def sanitize_filename(filename: str) -> str:
    """Remove potentially dangerous characters from a filename."""
    # Keep only alphanumerics, hyphens, underscores, and dots
    name = re.sub(r"[^\w\-.]", "_", filename)
    # Collapse multiple underscores
    name = re.sub(r"_+", "_", name).strip("_")
    return name


def get_file_extension(filename: str) -> str:
    """Return the lowercase file extension without the leading dot."""
    return Path(filename).suffix.lstrip(".").lower()


def truncate_text(text: str, max_length: int = 4000) -> str:
    """Truncate text to *max_length* characters, appending '…' if cut."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "…"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Division that returns *default* instead of raising on zero denominator."""
    if denominator == 0:
        return default
    return numerator / denominator
