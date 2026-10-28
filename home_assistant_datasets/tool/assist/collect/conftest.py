import asyncio
import threading

import aiohttp.resolver
import pytest

pytest_plugins = [
    "home_assistant_datasets.plugins.pytest_synthetic_home",
    "home_assistant_datasets.plugins.pytest_scrape",
]


@pytest.fixture(autouse=True)
def fix_aiohttp_resolver(monkeypatch):
    """Ensure aiohttp resolver uses the running event loop."""

    def _make_resolver(hass):
        resolver = aiohttp.resolver.AsyncResolver(loop=asyncio.get_running_loop())
        resolver.real_close = resolver.close
        return resolver

    monkeypatch.setattr(
        "homeassistant.helpers.aiohttp_client._async_make_resolver",
        _make_resolver,
    )


orig_enumerate = threading.enumerate


def _filtered_enumerate():
    return [t for t in orig_enumerate() if t.name not in ("tqdm_monitor",)]


threading.enumerate = _filtered_enumerate
