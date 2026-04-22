"""Tests for config.py — config read/write, key management, and caching."""

import importlib
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _reload_config(tmp_config_path):
    """Reload the config module so it picks up the temp CONFIG_PATH."""
    import config
    importlib.reload(config)
    # Point the module to the temp path
    config.CONFIG_PATH = tmp_config_path
    config._cache = None
    config._cache_mtime = 0
    yield config


def test_default_config_created(tmp_config_path):
    """Config file is created with defaults on first read."""
    import config
    cfg = config.get_config()
    assert "keys" in cfg
    assert Path(tmp_config_path).exists()


def test_set_and_get_key(tmp_config_path):
    """set_key persists and get_key retrieves the value."""
    import config
    config.set_key("openrouter", "sk-test-123")
    assert config.get_key("openrouter") == "sk-test-123"


def test_get_key_returns_none_for_empty():
    """get_key returns None when the key is empty or missing."""
    import config
    assert config.get_key("nonexistent") is None


def test_set_config_top_level():
    """set_config writes a top-level key."""
    import config
    config.set_config("default_pipeline", "serial")
    cfg = config.get_config()
    assert cfg["default_pipeline"] == "serial"


def test_config_caching(tmp_config_path):
    """Repeated reads return the cached dict without re-reading disk."""
    import config
    cfg1 = config.get_config()
    cfg2 = config.get_config()
    # Should be the same object (cached)
    assert cfg1 is cfg2


def test_cache_invalidation(tmp_path, monkeypatch):
    """Writing invalidates the cache so the next read returns fresh data."""
    import config
    config.get_config()
    config.set_config("default_pipeline", "debate")
    cfg2 = config.get_config()
    assert cfg2["default_pipeline"] == "debate"


def test_get_pipeline_mode():
    """get_pipeline_mode returns the configured default."""
    import config
    assert config.get_pipeline_mode() == "parallel"
    config.set_config("default_pipeline", "serial")
    assert config.get_pipeline_mode() == "serial"
