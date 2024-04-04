"""A Home Assistant runner for making tools that can start Home Assistant.

You can subclass a home assistant runner and add additional methods that should
be run after the event loop is started, which can be used to do things like
install custom components or configure the instance.
"""

import asyncio
from dataclasses import dataclass
import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from homeassistant import config_entries, auth, config as conf_util, bootstrap
from homeassistant.core import HomeAssistant, CoreState, EVENT_HOMEASSISTANT_STOP
from homeassistant.auth.auth_store import AuthStore
from homeassistant.helpers import (
    area_registry as ar,
    entity,
    device_registry as dr,
    entity_registry as er,
    issue_registry as ir,
    restore_state as rs,
    translation,
)
from homeassistant.util import dt as dt_util
from homeassistant.util.unit_system import METRIC_SYSTEM


_LOGGER = logging.getLogger(__name__)


class RunnerException(Exception):
    """Runner exception."""


@dataclass
class RuntimeConfig:
    """Class to hold the information for running Home Assistant."""

    config_dir: str
    load_registries: bool = True
    load_config_entries: bool = False

    # Callback fired before Home Assistant is started
    setup_callback: Callable[[HomeAssistant], Awaitable[None]] | None = None

    # Callback fired after Home Assistant is started
    run_callback: Callable[[HomeAssistant], Awaitable[None]] | None = None


async def async_setup_config_entries(hass: HomeAssistant) -> None:
    """Initialize HomeAssistant configuration and existing config entires."""
    config_dict = await conf_util.async_hass_config_yaml(hass)
    await bootstrap.async_from_config_dict(config_dict, hass)


@asynccontextmanager
async def _async_create_home_assistant(
    runtime_config: RuntimeConfig,
) -> AsyncGenerator[HomeAssistant, None]:
    """Return a Home Assistant object pointing at test config dir."""
    hass = HomeAssistant(runtime_config.config_dir)

    if runtime_config.load_registries:
        auth_store = AuthStore(hass)
        hass.auth = auth.AuthManager(hass, auth_store, {}, {})

    orig_tz = dt_util.DEFAULT_TIME_ZONE

    hass.config.location_name = "test home"
    hass.config.latitude = 32.87336
    hass.config.longitude = -117.22743
    hass.config.elevation = 0
    hass.config.set_time_zone("US/Pacific")
    hass.config.units = METRIC_SYSTEM
    hass.config.skip_pip = False

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

    hass.data[translation.TRANSLATION_FLATTEN_CACHE] = translation._TranslationCache(
        hass
    )

    from homeassistant import loader

    loader.async_setup(hass)

    if runtime_config.load_registries:
        await ar.async_load(hass)
        await dr.async_load(hass)
        await er.async_load(hass)
        await ir.async_load(hass)
        await rs.async_load(hass)
        await auth_store.async_load()

    hass.set_state(CoreState.running)

    yield hass

    # Restore timezone, it is set when creating the hass object
    dt_util.DEFAULT_TIME_ZONE = orig_tz


async def _setup_and_run_hass(runtime_config: RuntimeConfig) -> int:
    """Set up Home Assistant and run."""
    async with _async_create_home_assistant(runtime_config) as hass:
        if runtime_config.setup_callback:
            try:
                await runtime_config.setup_callback(hass)
            except Exception as err:
                _LOGGER.exception("Error setting up runtime: %s", err)
                return 1
        await hass.async_start()
        if runtime_config.load_config_entries:
            await async_setup_config_entries(hass)
        if runtime_config.run_callback:
            try:
                await runtime_config.run_callback(hass)
            except Exception as err:
                _LOGGER.exception("Error running callback: %s", err)
                hass.exit_code = 1
        await hass.async_stop()
        return hass.exit_code


def run(runtime_config: RuntimeConfig) -> int:
    """Run Home Assistant."""

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_setup_and_run_hass(runtime_config))
    finally:
        try:
            # _cancel_all_tasks_with_timeout(loop, TASK_CANCELATION_TIMEOUT)
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(loop.shutdown_default_executor())
        finally:
            asyncio.set_event_loop(None)
            loop.close()
