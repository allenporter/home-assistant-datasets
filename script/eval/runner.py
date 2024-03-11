"""A Home Assistant runner for making tools that can start Home Assistant.

You can subclass a home assistant runner and add additional methods that should
be run after the event loop is started, which can be used to do things like
install custom components or configure the instance.
"""

import asyncio
import pathlib
import threading
import logging
from typing import Any
from unittest import mock
from collections.abc import Generator, AsyncGenerator
from contextlib import asynccontextmanager, contextmanager

from homeassistant.core import HomeAssistant, CoreState, EVENT_HOMEASSISTANT_STOP
from homeassistant import config_entries
from homeassistant import auth
from homeassistant.auth import auth_store
from homeassistant.helpers import (
    area_registry as ar,
    entity,
    device_registry as dr,
    entity_registry as er,
    issue_registry as ir,
    restore_state as rs,
)
from homeassistant.util import dt as dt_util
from homeassistant.util.unit_system import METRIC_SYSTEM


_LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def async_create_home_assistant(
    event_loop: asyncio.AbstractEventLoop,
    storage_dir: pathlib.Path,
) -> AsyncGenerator[HomeAssistant, None]:
    """Return a Home Assistant object pointing at test config dir."""
    hass = HomeAssistant(str(storage_dir))

    store = auth_store.AuthStore(hass)
    hass.auth = auth.AuthManager(hass, store, {}, {})

    orig_tz = dt_util.DEFAULT_TIME_ZONE

    hass.config.location_name = "test home"
    hass.config.latitude = 32.87336
    hass.config.longitude = -117.22743
    hass.config.elevation = 0
    hass.config.set_time_zone("US/Pacific")
    hass.config.units = METRIC_SYSTEM
    hass.config.skip_pip = True
    hass.config.skip_pip_packages = []

    hass.config_entries = config_entries.ConfigEntries(
        hass,
        {
            "_": (
                "Not empty or else some bad checks for hass config in discovery.py"
                " breaks"
            )
        },
    )
    hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STOP, hass.config_entries._async_shutdown
    )

    # Load the registries
    entity.async_setup(hass)

    from homeassistant import loader

    loader.async_setup(hass)

    await ar.async_load(hass)
    await dr.async_load(hass)
    await er.async_load(hass)
    await ir.async_load(hass)
    await rs.async_load(hass)

    hass.set_state(CoreState.running)

    yield hass

    # Restore timezone, it is set when creating the hass object
    dt_util.DEFAULT_TIME_ZONE = orig_tz


class Runner:
    """A runner that invokes Home Assistant.

    You can subclass this class and implement `async_run_in_loop`.
    """

    def __init__(self, storage_dir: pathlib.Path) -> None:
        """Initialize the driver."""
        self._storage_dir = storage_dir

    @contextmanager
    def _home_assistant(self) -> Generator[HomeAssistant, None, None]:
        """Return a Home Assistant object pointing at test config directory."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        context_manager = async_create_home_assistant(loop, self._storage_dir)
        hass = loop.run_until_complete(context_manager.__aenter__())

        loop_stop_event = threading.Event()

        def run_loop() -> None:
            """Run event loop."""
            loop._thread_ident = threading.get_ident()
            loop.run_forever()
            loop_stop_event.set()

        orig_stop = hass.stop
        hass._stopped = mock.Mock(set=loop.stop)

        def start_hass(*mocks: Any) -> None:
            """Start hass."""
            asyncio.run_coroutine_threadsafe(
                self._async_run_in_loop(hass), loop
            ).result()

        def stop_hass() -> None:
            """Stop hass."""
            orig_stop()
            loop_stop_event.wait()

        hass.start = start_hass
        hass.stop = stop_hass

        threading.Thread(name="LoopThread", target=run_loop, daemon=False).start()

        yield hass
        loop.run_until_complete(context_manager.__aexit__(None, None, None))
        loop.close()

    async def _async_run_in_loop(self, hass: HomeAssistant) -> None:
        """Run in the Home Assistant event loop."""
        pass

    def run_until_complete(self) -> None:
        """Start the driver and run until the work in the event loop is complete."""
        with self._home_assistant() as hass:
            hass.start()
            hass.stop()
