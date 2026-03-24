"""
Configuration management for the MOA FastAPI application.

- Loads environment variables from .env via python-dotenv.
- Reads/writes persistent user config at ~/.moa/config.json.
- Never logs or prints API key values.
"""

import json
import os
import stat
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# In-memory config cache (invalidated when the file's mtime changes)
# ---------------------------------------------------------------------------

_cache: dict | None = None
_cache_mtime: float = 0

# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CONFIG_PATH: str = os.getenv("CONFIG_PATH", str(Path.home() / ".moa" / "config.json"))
DB_PATH: str = os.getenv("DB_PATH", str(Path.home() / ".moa" / "moa.db"))

# ── Performance ──────────────────────────────────────────────────────────────
HTTPX_MAX_CONNECTIONS: int = int(os.getenv("HTTPX_MAX_CONNECTIONS", "20"))
HTTPX_MAX_KEEPALIVE_CONNECTIONS: int = int(os.getenv("HTTPX_MAX_KEEPALIVE_CONNECTIONS", "10"))
HTTPX_TIMEOUT: float = float(os.getenv("HTTPX_TIMEOUT", "30.0"))

# ── Retry ────────────────────────────────────────────────────────────────────
RETRY_MAX_ATTEMPTS: int = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
RETRY_BASE_DELAY: float = float(os.getenv("RETRY_BASE_DELAY", "1.0"))

# ── Streaming ────────────────────────────────────────────────────────────────
SSE_QUEUE_SIZE: int = int(os.getenv("SSE_QUEUE_SIZE", "100"))

# ---------------------------------------------------------------------------
# Default config structure
# ---------------------------------------------------------------------------

_DEFAULT_CONFIG: dict = {
    "keys": {"openrouter": "", "bytez": ""},
    "default_pipeline": "parallel",
    "default_specialists": [],
    "default_chairman": {},
}


def _ensure_config_dir() -> None:
    """Create the ~/.moa/ directory with 700 permissions if it doesn't exist."""
    config_dir = Path(CONFIG_PATH).parent
    if not config_dir.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
        config_dir.chmod(stat.S_IRWXU)  # 700


def _ensure_config_file() -> None:
    """Create config.json with default values if it doesn't exist."""
    _ensure_config_dir()
    config_file = Path(CONFIG_PATH)
    if not config_file.exists():
        config_file.write_text(json.dumps(_DEFAULT_CONFIG, indent=2))
        config_file.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 600


def _read_config() -> dict:
    """Read and return the full config dict, using an in-memory cache."""
    global _cache, _cache_mtime
    _ensure_config_file()
    mtime = os.path.getmtime(CONFIG_PATH)
    if _cache is not None and mtime == _cache_mtime:
        return _cache
    _cache = json.loads(Path(CONFIG_PATH).read_text())
    _cache_mtime = mtime
    return _cache


def _write_config(config: dict) -> None:
    """Write the full config dict to disk and update the cache."""
    global _cache, _cache_mtime
    _ensure_config_file()
    Path(CONFIG_PATH).write_text(json.dumps(config, indent=2))
    _cache = config
    _cache_mtime = os.path.getmtime(CONFIG_PATH)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_config() -> dict:
    """Return the full configuration dictionary."""
    return _read_config()


def set_config(key: str, value) -> None:
    """Write a top-level key to the config file."""
    config = _read_config()
    config[key] = value
    _write_config(config)


def get_key(provider: str) -> str | None:
    """
    Return the API key for *provider*, or None if it is empty / missing.

    Checks the config file's ``keys`` section.
    """
    config = _read_config()
    keys: dict = config.get("keys", {})
    value = keys.get(provider)
    return value if value else None


def set_key(provider: str, value: str) -> None:
    """Save an API key for *provider* to the config file."""
    config = _read_config()
    config.setdefault("keys", {})[provider] = value
    _write_config(config)


def get_default_specialists() -> list[dict]:
    """Return the list of default specialist configurations."""
    config = _read_config()
    return config.get("default_specialists", [])


def get_default_chairman() -> dict:
    """Return the default chairman configuration."""
    config = _read_config()
    return config.get("default_chairman", {})


def get_pipeline_mode() -> str:
    """Return the default pipeline mode (e.g. 'parallel')."""
    config = _read_config()
    return config.get("default_pipeline", "parallel")
