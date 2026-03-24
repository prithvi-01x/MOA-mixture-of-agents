"""
Centralised logging configuration for MOA.

Usage::

    from logger import logger

    logger.info("specialist_done", model=model, latency_ms=42)

Set environment variables to control behaviour:

- ``LOG_FORMAT=json``   — emit newline-delimited JSON (for log aggregators)
- ``LOG_LEVEL=DEBUG``   — override log level (default: INFO)
- ``DEBUG=true``        — enables the /api/logs endpoint
"""

import os
import sys
import collections
from loguru import logger as _logger

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LOG_FORMAT = os.getenv("LOG_FORMAT", "").strip().lower()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()
_MAX_BUFFER = 200  # keep last N log lines for /api/logs

# Ring buffer of the last _MAX_BUFFER raw log lines (thread-safe for read-only)
log_buffer: collections.deque[str] = collections.deque(maxlen=_MAX_BUFFER)


def _buffering_sink(message: str) -> None:
    """Secondary sink that captures log lines into the in-memory ring buffer."""
    log_buffer.append(message.rstrip())


# ---------------------------------------------------------------------------
# Logger setup
# ---------------------------------------------------------------------------

# Remove the default stderr sink so we can replace it with our own
_logger.remove()

if LOG_FORMAT == "json":
    _logger.add(
        sys.stderr,
        level=LOG_LEVEL,
        serialize=True,          # emits newline-delimited JSON
    )
else:
    _logger.add(
        sys.stderr,
        level=LOG_LEVEL,
        colorize=True,
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
            "{message}"
        ),
    )

# Always buffer to RAM for the /api/logs endpoint
_logger.add(
    _buffering_sink,
    level=LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | {message}",
    colorize=False,
)

# Public handle
logger = _logger

__all__ = ["logger", "log_buffer"]
