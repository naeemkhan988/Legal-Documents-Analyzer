"""
Service - Named Entity Recognition
=====================================
Extracts entities (parties, dates, amounts, emails, phones) from legal text.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

from backend.utils.decorators import log_execution

logger = logging.getLogger(__name__)

_nlp = None


def _load_spacy():
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        import spacy
        for m in ("en_core_web_sm", "en_core_web_md"):
            try:
                _nlp = spacy.load(m)
                return _nlp
            except OSError:
                continue
        _nlp = spacy.blank("en")
        return _nlp
    except ImportError:
        return None


EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
AMOUNT_RE = re.compile(r"(?:USD|\$|€|£)\s?\d[\d,]*(?:\.\d{1,2})?", re.I)
DATE_RE = re.compile(
    r"\b(?:\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}|"
    r"\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})\b", re.I)


@log_execution
def extract_entities(text: str) -> Dict[str, Any]:
    return {
        "parties": extract_parties(text),
        "dates": extract_dates(text),
        "amounts": extract_amounts(text),
        "emails": extract_email_addresses(text),
        "phones": extract_phone_numbers(text),
        "locations": _spacy_entities(text, "GPE"),
        "organisations": _spacy_entities(text, "ORG"),
    }


def _spacy_entities(text: str, label: str) -> List[str]:
    nlp = _load_spacy()
    if nlp is None:
        return []
    try:
        doc = nlp(text[:30000])
        return sorted({e.text.strip() for e in doc.ents if e.label_ == label and len(e.text) > 2})
    except Exception:
        return []


def extract_parties(text: str) -> List[str]:
    parties: set[str] = set()
    for m in re.finditer(r"(?i)between\s+(.+?)\s+(?:and|&)\s+(.+?)(?:\s*[,(])", text[:5000]):
        parties.add(m.group(1).strip().strip('"'))
        parties.add(m.group(2).strip().strip('"'))
    nlp = _load_spacy()
    if nlp:
        try:
            doc = nlp(text[:20000])
            for e in doc.ents:
                if e.label_ in ("PERSON", "ORG") and len(e.text) > 2:
                    parties.add(e.text.strip())
        except Exception:
            pass
    return sorted(p for p in parties if len(p) > 1)


def extract_dates(text: str) -> List[str]:
    return sorted({m.group().strip() for m in DATE_RE.finditer(text)})


def extract_amounts(text: str) -> List[Dict[str, Any]]:
    results = []
    for m in AMOUNT_RE.finditer(text):
        raw = m.group().strip()
        currency = "EUR" if "€" in raw else ("GBP" if "£" in raw else "USD")
        digits = re.sub(r"[^\d.]", "", raw.replace(",", ""))
        try:
            value = float(digits)
        except ValueError:
            value = 0.0
        results.append({"raw": raw, "value": value, "currency": currency})
    return results


def extract_email_addresses(text: str) -> List[str]:
    return sorted(set(EMAIL_RE.findall(text)))


def extract_phone_numbers(text: str) -> List[str]:
    return sorted(set(PHONE_RE.findall(text)))
