"""Driver that invokes home assistnat and pushes time forward."""

from importlib import resources
import logging
import pathlib
import yaml

from homeassistant.core import HomeAssistant

from . import runner


_LOGGER = logging.getLogger(__name__)

STORAGE_RESOURCE_PATH = resources.files().joinpath("storage")
DEST_STORAGE_DIR = ".storage"

PROMPT = (
    "You are a Home Automation agent responsible for summarizing the state of an area."
)


class DriverException(Exception):
    """Driver exception."""


class EvalDriver(runner.Runner):
    """Driver that performs service calls and evaluates the results."""

    def __init__(
        self, synthetic_home_config: pathlib.Path, storage_dir: pathlib.Path
    ) -> None:
        """Initialize the driver."""
        super().__init__(storage_dir)
        self._synthetic_home_config = synthetic_home_config
        self._status = False

    @property
    def status(self) -> bool:
        """Return the status of the driver."""
        return self._status

    async def _async_run_in_loop(self, hass: HomeAssistant) -> None:
        _LOGGER.debug("Running driver")
        await hass.async_start()
        await self._async_evaluate_conversation_agent(hass)

        _LOGGER.debug("Done; Shutting down")

    async def _async_evaluate_conversation_agent(self, hass: HomeAssistant) -> bool:
        """Run an evaluation on the home conversation agent."""

        with open(self._storage_dir / self._synthetic_home_config, "r") as fd:
            content = fd.read()

        obj = yaml.load(content, Loader=yaml.FullLoader)
        summaries = obj.get("summaries")
        if not summaries:
            raise DriverException("No summaries found in configuration")

        area_summaries = summaries.get("area_summaries")
        if not area_summaries:
            raise DriverException("No area summaries found in configuration")

        _LOGGER.debug("Loaded %s area summariies to evaluate")

        for area_summary in area_summaries:
            _LOGGER.debug("Evaluating area summary: %s", area_summary)
            # await hass.services.async_call(
            #     "conversation",
            #     "process",
            #     {"text": PROMPT},.format(area_summary=area_summary")},
            #     blocking=True,
            # )

        return True
