"""Shared pytest fixtures for the MOA test suite."""

import contextlib
import importlib
import os
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from providers.base import BaseProvider, ProviderError


# ---------------------------------------------------------------------------
# DB / config path fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_db_path(tmp_path: Path):
    """Return a temporary database file path and set DB_PATH env var."""
    db_file = str(tmp_path / "test.db")
    os.environ["DB_PATH"] = db_file
    yield db_file
    os.environ.pop("DB_PATH", None)


@pytest.fixture()
def tmp_config_path(tmp_path: Path):
    """Return a temporary config file path and set CONFIG_PATH env var."""
    config_file = str(tmp_path / "config.json")
    os.environ["CONFIG_PATH"] = config_file
    yield config_file
    os.environ.pop("CONFIG_PATH", None)


@pytest_asyncio.fixture()
async def db(tmp_db_path):
    """Create tables in a temp DB and return the path."""
    import database
    importlib.reload(database)
    await database.create_tables()
    yield tmp_db_path


# ---------------------------------------------------------------------------
# Fake provider classes
# ---------------------------------------------------------------------------

class FakeProvider(BaseProvider):
    """Returns a fixed list of token strings per call."""

    def __init__(self, tokens: list[str] | None = None, fail: bool = False):
        self._tokens = tokens if tokens is not None else ["Hello", " world", "!"]
        self._fail = fail

    async def stream(self, model, messages, system_prompt=None,
                     temperature=0.7, max_tokens=1024) -> AsyncGenerator[str, None]:
        if self._fail:
            raise ProviderError(provider="fake", message="Fake error", status_code=500)
        for tok in self._tokens:
            yield tok

    async def chat(self, model, messages, system_prompt=None,
                   temperature=0.7, max_tokens=1024) -> str:
        if self._fail:
            raise ProviderError(provider="fake", message="Fake error", status_code=500)
        return "".join(self._tokens)

    async def list_models(self) -> list[str]:
        return ["fake-model"]

    async def health_check(self) -> bool:
        return True


class _MixedProvider(BaseProvider):
    """Shared provider that fails only on its 2nd stream() call.

    Specialists call stream(); chairman calls stream() after them.
    By failing on call 2 we fail exactly one specialist.
    """

    def __init__(self):
        self._call = 0
        self._ok = FakeProvider()
        self._bad = FakeProvider(fail=True)

    async def stream(self, model, messages, system_prompt=None,
                     temperature=0.7, max_tokens=1024):
        self._call += 1
        src = self._bad if self._call == 2 else self._ok
        async for tok in src.stream(model, messages, system_prompt, temperature, max_tokens):
            yield tok

    async def chat(self, model, messages, system_prompt=None,
                   temperature=0.7, max_tokens=1024):
        return await self._ok.chat(model, messages, system_prompt, temperature, max_tokens)

    async def list_models(self): return []
    async def health_check(self): return True


# ---------------------------------------------------------------------------
# ASGI async client fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def async_client(db):
    """
    Return an httpx.AsyncClient mounted against the FastAPI app.

    DB is set up before the app is imported so the lifespan picks up the
    correct DB path.
    """
    import database
    importlib.reload(database)

    import main as app_module
    importlib.reload(app_module)

    transport = ASGITransport(app=app_module.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ---------------------------------------------------------------------------
# Provider-patch helpers
#
# pipeline.py and chairman.py use `from providers.factory import get_provider`
# which binds a *local name*.  Patching providers.factory.get_provider alone
# doesn't affect local bindings already resolved by the import.  We must
# patch the symbol in every module that imported it.
# ---------------------------------------------------------------------------

_PATCH_TARGETS = [
    "providers.factory.get_provider",
    "moa.pipeline.get_provider",
    "moa.chairman.get_provider",
]


@contextlib.contextmanager
def _patch_all(return_value=None, side_effect=None):
    """Patch get_provider in all three modules simultaneously."""
    import providers.factory as _fac
    _fac._provider_cache.clear()
    active = []
    for target in _PATCH_TARGETS:
        p = patch(target, return_value=return_value, side_effect=side_effect)
        p.start()
        active.append(p)
    try:
        yield
    finally:
        for p in active:
            p.stop()
        _fac._provider_cache.clear()


# ---------------------------------------------------------------------------
# Provider-patch fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def fake_provider_factory():
    """All get_provider calls return a working FakeProvider."""
    with _patch_all(return_value=FakeProvider()):
        yield


@pytest.fixture()
def fake_provider_factory_one_fail():
    """All get_provider calls return the *same* _MixedProvider instance.

    _MixedProvider fails on its 2nd stream() call, so one specialist fails.
    """
    with _patch_all(return_value=_MixedProvider()):
        yield


@pytest.fixture()
def fake_provider_all_fail():
    """All get_provider calls return a failing FakeProvider."""
    with _patch_all(return_value=FakeProvider(fail=True)):
        yield
