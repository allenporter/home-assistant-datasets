"""Driver that invokes home assistnat and pushes time forward."""

import logging
import importlib
import pathlib
from typing import Any
import yaml

from homeassistant.core import HomeAssistant

from . import config


_LOGGER = logging.getLogger(__name__)

EVAL_CONFIG_YAML = "eval_config.yaml"


class DriverException(Exception):
    """Driver exception."""


def load_evaluation_config(config_file: pathlib.Path) -> dict[str, Any]:
    """Load synthetic home configuration from disk."""
    try:
        with config_file.open("r") as f:
            content = f.read()
    except FileNotFoundError:
        raise DriverException(f"Configuration file '{config_file}' does not exist")
    try:
        return yaml.load(content, Loader=yaml.SafeLoader)
    except ValueError as err:
        raise DriverException(f"Could not parse config file '{config_file}': {err}")


class EvalDriver:
    """Driver that performs service calls and evaluates the results."""

    def __init__(
        self,
        eval_config_dir: pathlib.Path,
    ) -> None:
        """Initialize the driver."""
        self._eval_config_dir = eval_config_dir
        self._eval_config = load_evaluation_config(eval_config_dir / EVAL_CONFIG_YAML)

    async def async_setup(self, hass: HomeAssistant) -> None:
        """Run setup to prepare configuration data."""
        await config.async_setup(hass, self._eval_config)

    async def async_run(self, hass: HomeAssistant) -> None:
        """Run an evaluation on the home conversation agent."""

        # Create all config entries
        await config.async_setup_config_entries(hass, self._eval_config)

        # Load the python module from the evaluation package
        # Load the evaluation model
        module_path = self._eval_config_dir.absolute()
        _LOGGER.info("Loading eval module from %s", module_path)
        module_name = "eval"
        module_filename = module_path / f"{module_name}.py"
        spec = importlib.util.spec_from_file_location(module_name, module_filename)
        _LOGGER.info("Loading module from spec %s", spec)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except FileNotFoundError as err:
            raise DriverException(f"Cannot load module 'eval': {err}") from err
        except SyntaxError as err:
            raise DriverException(f"Cannot load module 'eval' from {module_filename}: {err}") from err

        if (run := getattr(module, "async_run_eval", None)) is None:
            raise DriverException(f"Module eval does not have method `async def async_run_eval(hass: HomeAssistant, config: dict[str, Any]) -> None:` in {module_filename}")

        await run(hass, self._eval_config)
