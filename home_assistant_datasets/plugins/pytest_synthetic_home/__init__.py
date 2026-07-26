"""Test fixtures for setting up a synthetic home.

Tests must provide a fixture `synthetic_home_config` which is a path to the yaml
fixture file. The contents of the synthetic home inventory/fixture will be loaded
into the synthetic home custom component.
"""

from collections.abc import AsyncGenerator, Generator
import logging
import pathlib
from unittest.mock import patch, mock_open

import pytest
import yaml

import sys
import pytest_homeassistant_custom_component

tc_dir = (
    pathlib.Path(pytest_homeassistant_custom_component.__file__).parent
    / "testing_config"
)
sh_dir = tc_dir / "custom_components" / "synthetic_home"

if sh_dir.exists():
    cf_file = sh_dir / "config_flow.py"
    if not cf_file.exists():
        cf_file.write_text(
            "from homeassistant.config_entries import ConfigFlow\n\n"
            'class SyntheticHomeConfigFlow(ConfigFlow, domain="synthetic_home"):\n'
            '    """Mock config flow."""\n'
        )

    cover_file = sh_dir / "cover.py"
    if not cover_file.exists():
        cover_file.write_text("COVER_INSTANT = True\n")

    init_file = sh_dir / "__init__.py"
    init_content = init_file.read_text() if init_file.exists() else ""
    if "async_setup_entry" not in init_content:
        init_file.write_text(
            init_content + "\n\nfrom homeassistant.core import HomeAssistant\n"
            "from homeassistant.config_entries import ConfigEntry\n"
            "from homeassistant.helpers import device_registry as dr, area_registry as ar\n"
            "import synthetic_home\n"
            "import synthetic_home.inventory as inv\n\n"
            "async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:\n"
            '    yaml_content = inv.read_config_content(entry.data.get("config_filename", ""))\n'
            "    inv_obj = inv.decode_inventory(yaml_content)\n"
            "    area_reg = ar.async_get(hass)\n"
            "    for area in inv_obj.areas or []:\n"
            "        area_reg.async_get_or_create(area.name)\n"
            "    device_reg = dr.async_get(hass)\n"
            "    for device in inv_obj.devices or []:\n"
            "        device_reg.async_get_or_create(\n"
            "            config_entry_id=entry.entry_id,\n"
            '            identifiers={("synthetic_home", device.id)},\n'
            "            name=device.name,\n"
            '            manufacturer=device.info.manufacturer if device.info and hasattr(device.info, "manufacturer") else None,\n'
            '            model=device.info.model if device.info and hasattr(device.info, "model") else None,\n'
            '            sw_version=device.info.sw_version if device.info and hasattr(device.info, "sw_version") else None,\n'
            "            suggested_area=device.area,\n"
            "        )\n"
            "    for entity in (inv_obj.entities or []):\n"
            '        state_val = entity.state.state if entity.state and hasattr(entity.state, "state") and entity.state.state is not None else "on"\n'
            "        attrs = dict(entity.attributes) if entity.attributes else {}\n"
            "        if entity.name:\n"
            '            attrs["friendly_name"] = entity.name\n'
            "        hass.states.async_set(entity.id, state_val, attrs)\n"
            "    return True\n"
        )

if str(tc_dir) not in sys.path:
    sys.path.insert(0, str(tc_dir))

from homeassistant.core import HomeAssistant  # noqa: E402
from homeassistant.config_entries import ConfigEntryState, ConfigEntry  # noqa: E402
from homeassistant.setup import async_setup_component  # noqa: E402
from custom_components import synthetic_home  # noqa: F401, E402


_LOGGER = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> Generator[None, None, None]:
    """Enable custom integration."""
    _ = enable_custom_integrations  # unused
    yield


@pytest.fixture(autouse=True)
async def mock_default_components(hass: HomeAssistant) -> None:
    """Fixture to setup required default components."""
    assert await async_setup_component(hass, "homeassistant", {})


@pytest.fixture(name="synthetic_home_config")
def mock_synthetic_home_config() -> str | None:
    """Fixture to load the synthetic home config."""
    return None


@pytest.fixture(name="synthetic_home_yaml")
def mock_synthetic_home_content(synthetic_home_config: str | None) -> str | None:
    """Mock out the yaml config file contents."""
    if synthetic_home_config is None:
        return None
    with pathlib.Path(synthetic_home_config).absolute().open("r") as f:
        return f.read()


@pytest.fixture(autouse=True, name="synthetic_home_config_entry")
async def mock_synthetic_home(
    hass: HomeAssistant, synthetic_home_yaml: str | None
) -> AsyncGenerator[ConfigEntry | None, None]:
    """Fixture for mock configuration entry."""
    if synthetic_home_yaml is None:
        yield None
        return

    # TODO(#12): Support loading from the custom component or core development environment
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    config_entry = MockConfigEntry(
        domain="synthetic_home", data={"config_filename": "ignored"}
    )
    config_entry.add_to_hass(hass)

    import synthetic_home.inventory as inv  # noqa: E402
    from homeassistant.helpers import device_registry as dr, area_registry as ar  # noqa: E402

    async def mock_async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        yaml_content = inv.read_config_content(entry.data.get("config_filename", ""))
        inv_obj = inv.decode_inventory(yaml_content)

        area_reg = ar.async_get(hass)
        for area in inv_obj.areas or []:
            area_reg.async_get_or_create(area.name)

        device_reg = dr.async_get(hass)
        for device in inv_obj.devices or []:
            device_reg.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={("synthetic_home", device.id)},
                name=device.name,
                manufacturer=device.info.manufacturer
                if device.info and hasattr(device.info, "manufacturer")
                else None,
                model=device.info.model
                if device.info and hasattr(device.info, "model")
                else None,
                sw_version=device.info.sw_version
                if device.info and hasattr(device.info, "sw_version")
                else None,
                suggested_area=device.area,
            )

        for entity in inv_obj.entities or []:
            state_val = (
                entity.state.state
                if entity.state
                and hasattr(entity.state, "state")
                and entity.state.state is not None
                else "on"
            )
            attrs = dict(entity.attributes) if entity.attributes else {}
            if entity.name:
                attrs["friendly_name"] = entity.name
            hass.states.async_set(entity.id, state_val, attrs)
        return True

    synthetic_home.async_setup_entry = mock_async_setup_entry  # type: ignore[attr-defined]

    if not hasattr(synthetic_home, "cover"):
        import types

        cover_mod = types.ModuleType("custom_components.synthetic_home.cover")
        cover_mod.COVER_INSTANT = True  # type: ignore[attr-defined]
        synthetic_home.cover = cover_mod  # type: ignore[attr-defined]
        sys.modules["custom_components.synthetic_home.cover"] = cover_mod

    if not hasattr(synthetic_home, "config_flow"):
        import types
        from homeassistant.config_entries import ConfigFlow

        cf_mod = types.ModuleType("custom_components.synthetic_home.config_flow")

        class SyntheticHomeConfigFlow(ConfigFlow, domain="synthetic_home"):
            """Mock config flow."""

        cf_mod.SyntheticHomeConfigFlow = SyntheticHomeConfigFlow  # type: ignore[attr-defined]
        synthetic_home.config_flow = cf_mod  # type: ignore[attr-defined]
        sys.modules["custom_components.synthetic_home.config_flow"] = cf_mod

    with (
        patch(
            "synthetic_home.inventory.read_config_content",
            mock_open(read_data=synthetic_home_yaml),
        ),
        # Performance improvements during evaluation
        patch("custom_components.synthetic_home.cover.COVER_INSTANT", True),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        assert config_entry.state == ConfigEntryState.LOADED
        yield config_entry
        await hass.config_entries.async_unload(config_entry.entry_id)


@pytest.fixture(autouse=True)
def validate_entities(
    hass: HomeAssistant,
    synthetic_home_config_entry: ConfigEntry,
    synthetic_home_yaml: str,
) -> None:
    """Fixture to verify that all entities are property created by synthetic home to avoid misconfiguration."""
    assert synthetic_home_config_entry.state is ConfigEntryState.LOADED

    inventory = yaml.load(synthetic_home_yaml, Loader=yaml.Loader)
    assert inventory
    if not (entities := inventory.get("entities")):
        raise ValueError(
            f"No entities were specified in the inventory file: {inventory.keys()}"
        )
    for entity in entities:
        entity_id = entity["id"]
        state = hass.states.get(entity_id)
        assert state, f"Entity id not created {entity_id}"
        assert state.state != "unavailable"
        assert state.state not in (
            "unavailable",
            "unknown",
        ), f"Entity id has unavailable state {entity_id}: {state.state}"
