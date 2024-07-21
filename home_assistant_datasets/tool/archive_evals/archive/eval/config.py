"""Creates the Home Assistant configuration for the eval driver.

This file is invoked with a config file that supports the following:

copy_config_files: A list of filenames to copy into the config/ dir
config_entries: A list of of ConfigEntry dictionaries.

"""

import hashlib
import logging
import json
import os
import pathlib
import shutil
import yaml

from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from typing import Any


_LOGGER = logging.getLogger(__name__)



CONF_COPY_CONFIG_FILES = "copy_config_files"
CONF_CONFIG_ENTRIES = "config_entries"

# A minimal set of domains from `default_config` that are used for running
# the evaluation that disable things like zeroconf or bluetooth discovery
# that have chatty log messages.
CONFIURATION_YAML = pathlib.Path("configuration.yaml")
MINIMAL_CONFIG = {
    "assist_pipeline": {},
    "conversation": {},
    "energy": {},
    "history": {},
    "logbook": {},
    "map": {},
    "sun": {},
    "webhook": {},
}

STORAGE_DIR = pathlib.Path(".storage")
ONBOARDING_FILE = STORAGE_DIR / "onboarding"
ONBOARDING_CONFIG = {
    "version": 4,
    "minor_version": 1,
    "key": "onboarding",
    "data": {
        "done": [
            "user",
            "core_config",
            "analytics",
            "integration",
        ]
    }
}


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> None:
    """Perform any pre-configuration before Home Assistant starts."""

    # Instead of writing the default configuration, we write a stripped down
    # configuration and mark onboarding as complete.
    # await config.async_create_default_config(hass)

    config_dir = pathlib.Path(hass.config.config_dir)
    with (config_dir / CONFIURATION_YAML).open('w') as configuration_yaml_file:
        configuration_yaml_file.write(yaml.dump(MINIMAL_CONFIG, sort_keys=False))

    os.makedirs(config_dir / STORAGE_DIR, exist_ok=True)
    with (config_dir / ONBOARDING_FILE).open('w') as onboarding_file:
        json.dump(ONBOARDING_CONFIG, onboarding_file)

    # Copy eval specifc configuration files
    for config_file in config.get(CONF_COPY_CONFIG_FILES, []):
        shutil.copy(
            config_file,
            config_dir / pathlib.Path(config_file).name,
        )


def create_config_entry(config_entry: dict[str, Any]) -> config_entries.ConfigEntry:
    """Create a ConfigEntry from a dict."""
    # Arbitarily assign a unique id based on the contents of the entry
    hash = hashlib.sha256()
    hash.update(str(config_entry).encode())
    unique_id = hash.hexdigest()

    return config_entries.ConfigEntry(
        version=1,
        minor_version=1,
        source=config_entries.SOURCE_USER,
        unique_id=unique_id,
        domain=config_entry["domain"],
        title=config_entry["title"],
        data=config_entry.get("data"),
        options=config_entry.get("options"),
    )


async def async_setup_config_entries(hass: HomeAssistant, config: dict[str, Any]) -> None:
    """Perform setup of any config entries specified in the dictionary."""

    for config_entry_dict in config.get(CONF_CONFIG_ENTRIES, []):
        config_entry = create_config_entry(config_entry_dict)
        _LOGGER.info("Creating config entry for domain %s", config_entry.domain)
        await hass.config_entries.async_add(config_entry)
        await hass.async_block_till_done()
        if config_entry.state != config_entries.ConfigEntryState.LOADED:
            _LOGGER.warning("Config entry %s failed to load: %s", config_entry.domain, config_entry.state)
            raise ValueError(f"Failed to load config entry for domain {config_entry.domain}")
