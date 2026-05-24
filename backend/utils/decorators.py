"""
Utils - Decorators
===================
Reusable decorators for logging, validation, error handling, and caching.
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


# ── 1. Log Execution Time ─────────────────────────────────────────────

def log_execution(func: F) -> F:
    """Log the name and wall-clock duration of the decorated function."""

    @functools.wraps(func)
    def _wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        logger.info("⏱  START  %s.%s", func.__module__, func.__qualname__)
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.info(
                "✅  END    %s.%s  (%.3fs)",
                func.__module__,
                func.__qualname__,
                elapsed,
            )
            return result
        except Exception as exc:
            elapsed = time.perf_counter() - start
            logger.error(
                "❌  FAIL   %s.%s  (%.3fs) — %s",
                func.__module__,
                func.__qualname__,
                elapsed,
                exc,
            )
            raise

    return _wrapper  # type: ignore[return-value]


# ── 2. Async Log Execution ────────────────────────────────────────────

def log_execution_async(func: F) -> F:
    """Async variant of :func:`log_execution`."""

    @functools.wraps(func)
    async def _wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        logger.info("⏱  START  %s.%s", func.__module__, func.__qualname__)
        try:
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.info(
                "✅  END    %s.%s  (%.3fs)",
                func.__module__,
                func.__qualname__,
                elapsed,
            )
            return result
        except Exception as exc:
            elapsed = time.perf_counter() - start
            logger.error(
                "❌  FAIL   %s.%s  (%.3fs) — %s",
                func.__module__,
                func.__qualname__,
                elapsed,
                exc,
            )
            raise

    return _wrapper  # type: ignore[return-value]


# ── 3. Input Validation ──────────────────────────────────────────────

def validate_input(*expected_types: type) -> Callable:
    """Validate positional argument types at call-time.

    Usage::

        @validate_input(str, int)
        def greet(name: str, age: int) -> str: ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def _wrapper(*args: Any, **kwargs: Any) -> Any:
            for idx, (arg, exp_type) in enumerate(zip(args, expected_types)):
                if not isinstance(arg, exp_type):
                    raise TypeError(
                        f"Argument {idx} of {func.__qualname__} expected "
                        f"{exp_type.__name__}, got {type(arg).__name__}"
                    )
            return func(*args, **kwargs)

        return _wrapper  # type: ignore[return-value]

    return decorator


# ── 4. Error Handling ─────────────────────────────────────────────────

def handle_errors(default: Any = None, reraise: bool = False) -> Callable:
    """Catch exceptions, log them, and optionally return a default value.

    Parameters
    ----------
    default:
        Value to return when the function raises.
    reraise:
        If ``True`` the exception is re-raised after logging.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def _wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                logger.exception(
                    "Handled error in %s.%s: %s",
                    func.__module__,
                    func.__qualname__,
                    exc,
                )
                if reraise:
                    raise
                return default

        return _wrapper  # type: ignore[return-value]

    return decorator


# ── 5. Simple In-Memory Cache ─────────────────────────────────────────

def cache_result(maxsize: int = 128) -> Callable:
    """Decorator that caches return values keyed by a hash of the arguments.

    Works with non-hashable arguments by JSON-serialising them first.
    """

    def decorator(func: F) -> F:
        _cache: dict[str, Any] = {}

        @functools.wraps(func)
        def _wrapper(*args: Any, **kwargs: Any) -> Any:
            key_data = json.dumps({"a": str(args), "k": str(kwargs)}, sort_keys=True)
            key = hashlib.md5(key_data.encode()).hexdigest()
            if key in _cache:
                logger.debug("Cache HIT for %s", func.__qualname__)
                return _cache[key]
            result = func(*args, **kwargs)
            if len(_cache) >= maxsize:
                # Evict oldest entry (FIFO)
                oldest = next(iter(_cache))
                del _cache[oldest]
            _cache[key] = result
            logger.debug("Cache MISS for %s — stored", func.__qualname__)
            return result

        _wrapper.cache_clear = lambda: _cache.clear()  # type: ignore[attr-defined]
        return _wrapper  # type: ignore[return-value]

    return decorator
