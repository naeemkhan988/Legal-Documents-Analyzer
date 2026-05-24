"""
Service - LLM Service
=======================
Unified interface to multiple LLM backends:
  1. Ollama (local, default)
  2. Groq  (cloud API)
  3. HuggingFace Inference API

The module auto-selects the best available backend at runtime and
gracefully degrades when a backend is unreachable.
"""

from __future__ import annotations

import logging
from typing import Generator, Optional

from backend.config import LLMProvider, settings
from backend.utils.decorators import log_execution
from backend.utils.exceptions import LLMServiceError
from backend.utils.helpers import truncate_text

logger = logging.getLogger(__name__)


# ── Backend Implementations ──────────────────────────────────────────

def _generate_ollama(prompt: str, max_tokens: int = 500) -> str:
    """Generate text using a local Ollama instance."""
    try:
        import ollama as ollama_client

        response = ollama_client.generate(
            model=settings.OLLAMA_MODEL,
            prompt=prompt,
            options={"num_predict": max_tokens, "temperature": 0.3},
        )
        return response.get("response", "").strip()
    except Exception as exc:
        raise LLMServiceError(
            message="Ollama generation failed.",
            detail=str(exc),
        )


def _generate_groq(prompt: str, max_tokens: int = 500) -> str:
    """Generate text via the Groq cloud API."""
    if not settings.GROQ_API_KEY:
        raise LLMServiceError(message="GROQ_API_KEY not configured.")
    try:
        from groq import Groq

        client = Groq(api_key=settings.GROQ_API_KEY)
        chat = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return chat.choices[0].message.content.strip()
    except Exception as exc:
        raise LLMServiceError(message="Groq generation failed.", detail=str(exc))


def _generate_huggingface(prompt: str, max_tokens: int = 500) -> str:
    """Generate text via the HuggingFace Inference API."""
    if not settings.HF_API_TOKEN:
        raise LLMServiceError(message="HF_API_TOKEN not configured.")
    try:
        import requests

        url = f"https://api-inference.huggingface.co/models/{settings.HF_MODEL}"
        headers = {"Authorization": f"Bearer {settings.HF_API_TOKEN}"}
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": max_tokens, "temperature": 0.3},
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and data:
            return data[0].get("generated_text", "").strip()
        return str(data)
    except Exception as exc:
        raise LLMServiceError(message="HuggingFace generation failed.", detail=str(exc))


# ── Provider Dispatch ─────────────────────────────────────────────────

_PROVIDERS = {
    LLMProvider.OLLAMA: _generate_ollama,
    LLMProvider.GROQ: _generate_groq,
    LLMProvider.HUGGINGFACE: _generate_huggingface,
}

_FALLBACK_ORDER = [LLMProvider.OLLAMA, LLMProvider.GROQ, LLMProvider.HUGGINGFACE]


@log_execution
def generate_text(prompt: str, max_tokens: int = 500) -> str:
    """Generate text using the configured (or best available) LLM backend.

    Tries the configured ``LLM_SERVICE`` first, then falls back through
    the other providers in order.
    """
    # Put the configured provider first
    order = [settings.LLM_SERVICE] + [p for p in _FALLBACK_ORDER if p != settings.LLM_SERVICE]

    last_error: Optional[Exception] = None
    for provider in order:
        gen_fn = _PROVIDERS.get(provider)
        if gen_fn is None:
            continue
        try:
            result = gen_fn(prompt, max_tokens)
            if result:
                logger.info("LLM response generated via %s (%d chars)", provider.value, len(result))
                return result
        except LLMServiceError as exc:
            logger.warning("Provider %s failed: %s — trying next", provider.value, exc.message)
            last_error = exc

    # All providers failed — return a useful fallback
    logger.error("All LLM providers failed. Last error: %s", last_error)
    raise LLMServiceError(
        message="All LLM providers are unavailable.",
        detail=str(last_error) if last_error else None,
    )


# ── High-Level Convenience Functions ──────────────────────────────────

def summarize_document(text: str) -> str:
    """Produce a concise summary of a legal document."""
    from backend.utils.prompts import SUMMARIZE_PROMPT

    prompt = SUMMARIZE_PROMPT.format(text=truncate_text(text, 6000))
    return generate_text(prompt, max_tokens=800)


def extract_key_terms(text: str) -> list[str]:
    """Extract key legal terms from the document."""
    from backend.utils.prompts import EXTRACT_KEY_TERMS_PROMPT
    from backend.utils.helpers import parse_json_safely

    prompt = EXTRACT_KEY_TERMS_PROMPT.format(text=truncate_text(text, 6000))
    raw = generate_text(prompt, max_tokens=300)
    terms = parse_json_safely(raw)
    if isinstance(terms, list):
        return [str(t) for t in terms]
    # Fallback: split by commas / newlines
    return [t.strip().strip('"') for t in raw.replace("\n", ",").split(",") if t.strip()]


def get_recommendations(clauses: str, risk_score: float) -> list[str]:
    """Generate actionable recommendations based on analysis results."""
    from backend.utils.prompts import GENERATE_RECOMMENDATIONS_PROMPT

    risk_level = "RED" if risk_score >= 70 else ("YELLOW" if risk_score >= 40 else "GREEN")
    prompt = GENERATE_RECOMMENDATIONS_PROMPT.format(
        summary="See clauses below.",
        clauses=truncate_text(clauses, 4000),
        risk_score=risk_score,
        risk_level=risk_level,
    )
    raw = generate_text(prompt, max_tokens=600)
    # Split numbered recommendations
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    return lines if lines else [raw]


def stream_response(prompt: str) -> Generator[str, None, None]:
    """Stream tokens from the LLM (Ollama only; others fall back to batch)."""
    try:
        import ollama as ollama_client

        stream = ollama_client.generate(
            model=settings.OLLAMA_MODEL,
            prompt=prompt,
            stream=True,
            options={"temperature": 0.3},
        )
        for chunk in stream:
            token = chunk.get("response", "")
            if token:
                yield token
    except Exception:
        # Fallback: batch generate and yield in one go
        result = generate_text(prompt)
        yield result


def check_llm_health() -> bool:
    """Quick health check — can we generate a single token?"""
    try:
        result = generate_text("Say 'ok'.", max_tokens=5)
        return bool(result)
    except Exception:
        return False
