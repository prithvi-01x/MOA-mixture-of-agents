"""
Async retry decorator with exponential backoff and jitter.

Usage::

    from providers.retry import async_retry
    from providers.base import ProviderError

    @async_retry(max_attempts=3, base_delay=1.0)
    async def my_func():
        ...
"""

import asyncio
import functools
import random
from typing import Callable, Awaitable, TypeVar

from logger import logger
from providers.base import ProviderError

F = TypeVar("F")

# Status codes that are worth retrying
_RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({429, 500, 502, 503, 504})


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
) -> Callable:
    """
    Decorator factory that retries an async function on retryable
    ``ProviderError`` (status codes 429 or 5xx) using exponential backoff
    plus random jitter.

    Backoff formula::

        delay = base_delay * (2 ** attempt) + uniform(0, 1)

    Args:
        max_attempts: Maximum total invocations (including the first).
        base_delay: Base delay in seconds before the first retry.

    Returns:
        A decorator that wraps the target coroutine function.
    """
    def decorator(fn: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            last_exc: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return await fn(*args, **kwargs)
                except ProviderError as exc:
                    last_exc = exc
                    retryable = (
                        exc.status_code is not None
                        and exc.status_code in _RETRYABLE_STATUS_CODES
                    )
                    if not retryable or attempt == max_attempts - 1:
                        raise
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        "provider_retry",
                        attempt=attempt + 1,
                        provider=exc.provider,
                        status_code=exc.status_code,
                        delay_s=round(delay, 2),
                    )
                    await asyncio.sleep(delay)
            # Should not be reached, but satisfies type checkers
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator


def async_retry_stream(
    max_attempts: int = 3,
    base_delay: float = 1.0,
) -> Callable:
    """
    Same as ``async_retry`` but for async generator functions (stream methods).

    Because async generators cannot be wrapped with a simple ``return await``,
    this decorator wraps the generator and retries from scratch on failure
    *before* any values have been yielded.  If the generator starts yielding
    and then fails mid-stream, the exception propagates as normal (partial
    output cannot be rewound).
    """
    def decorator(fn: Callable[..., object]) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            last_exc: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    async for item in fn(*args, **kwargs):
                        yield item
                    return  # success — exit generator
                except ProviderError as exc:
                    last_exc = exc
                    retryable = (
                        exc.status_code is not None
                        and exc.status_code in _RETRYABLE_STATUS_CODES
                    )
                    if not retryable or attempt == max_attempts - 1:
                        raise
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        "provider_retry",
                        attempt=attempt + 1,
                        provider=exc.provider,
                        status_code=exc.status_code,
                        delay_s=round(delay, 2),
                    )
                    await asyncio.sleep(delay)
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator
