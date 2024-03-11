"""Driver that invokes home assistnat and pushes time forward."""

import pathlib
import logging
import hashlib

from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant import config

from . import runner

_LOGGER = logging.getLogger(__name__)


class Driver(runner.Runner):
    """Driver that performs data generation."""

    def __init__(
        self, synthetic_home_config: pathlib.Path, storage_dir: pathlib.Path
    ) -> None:
        """Initialize the driver."""
        super().__init__(storage_dir)
        self._synthetic_home_config = synthetic_home_config

    async def _async_run_in_loop(self, hass: HomeAssistant) -> None:
        _LOGGER.debug("Running driver")
        await config.async_create_default_config(hass)
        await hass.async_start()

        await self._async_create_synthetic_home(hass)

        _LOGGER.debug("Done; Shutting down")

    async def _async_create_synthetic_home(self, hass: HomeAssistant) -> None:
        """Create the synthetic home configuration entry."""
        hash = hashlib.sha256()
        hash.update(self._synthetic_home_config.encode())
        unique_id = hash.hexdigest()

        _LOGGER.debug("Creating configuration entry")
        entry = config_entries.ConfigEntry(
            version=1,
            minor_version=0,
            source=config_entries.SOURCE_USER,
            unique_id=unique_id,
            domain="synthetic_home",
            title="Synthetic Home",
            data={"config_filename": str(self._synthetic_home_config)},
        )
        _LOGGER.debug("Setting up configuration entry")
        await hass.config_entries.async_add(entry)
