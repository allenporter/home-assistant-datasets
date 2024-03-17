"""Driver that creates the synthetic home configuration for Home Assistant."""

import hashlib
from importlib import resources
import logging
import os
import pathlib
import shutil

from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant import config



_LOGGER = logging.getLogger(__name__)

STORAGE_RESOURCE_PATH = resources.files().joinpath("storage")
DEST_STORAGE_DIR = ".storage"


class DriverException(Exception):
    """Driver exception."""


class ConfigDriver:
    """Driver that performs data generation."""

    def __init__(self, synthetic_home_config: pathlib.Path) -> None:
        """Initialize the driver."""
        self._synthetic_home_config = synthetic_home_config

    async def async_setup(self, hass: HomeAssistant) -> None:
        _LOGGER.info("Creating initial configuration")
        await config.async_create_default_config(hass)

        _LOGGER.info("Copying synthetic home configuration")
        os.mkdir(hass.config.config_dir / DEST_STORAGE_DIR)
        for config_file in STORAGE_RESOURCE_PATH.iterdir():
            _LOGGER.debug("Copying %s", config_file)
            shutil.copy(
                str(config_file),
                hass.config.config_dir / DEST_STORAGE_DIR / config_file.name,
            )

    async def async_run(self, hass: HomeAssistant) -> None:
        """Create the synthetic home configuration entry."""
        hash = hashlib.sha256()
        hash.update(self._synthetic_home_config.encode())
        unique_id = hash.hexdigest()

        _LOGGER.info(
            "Creating configuration entry %s", hass.data.get("custom_components")
        )
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
        await hass.async_block_till_done()
        if entry.state != config_entries.ConfigEntryState.LOADED:
            _LOGGER.warning("Failed to setup synthetic home, in state: %s", entry.state)
            return False
        _LOGGER.debug("Synthetic home setup complete")
        return True
