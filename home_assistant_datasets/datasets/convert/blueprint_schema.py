"""Module for converting blueprint schemas."""

from typing import Any
import itertools
from inspect import signature

import voluptuous as vol
from voluptuous_openapi import convert

from homeassistant.const import (
    CONF_CONDITIONS,
    CONF_TRIGGERS,
    CONF_VARIABLES,
    CONF_NAME,
    CONF_DESCRIPTION,
    CONF_DOMAIN,
    CONF_DEFAULT,
    CONF_SELECTOR,
    CONF_ACTIONS,
)
from homeassistant.components.blueprint.const import CONF_BLUEPRINT, CONF_INPUT
from homeassistant.helpers import config_validation as cv, llm, selector


BLUEPRINT_INPUT_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME): str,
        vol.Optional(CONF_DESCRIPTION): str,
        vol.Optional(CONF_DEFAULT): Any,
        vol.Optional(CONF_SELECTOR): selector.validate_selector,
    }
)


BLUEPRINT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BLUEPRINT): vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Optional(CONF_DESCRIPTION): str,
                vol.Required(CONF_DOMAIN): str,
                vol.Optional(CONF_INPUT): vol.Schema(
                    {
                        str: BLUEPRINT_INPUT_SCHEMA,
                    }
                ),
            }
        ),
        vol.Optional(CONF_VARIABLES): cv.SCRIPT_VARIABLES_SCHEMA,
        vol.Required(CONF_TRIGGERS): cv.TRIGGER_BASE_SCHEMA,
        vol.Optional(CONF_CONDITIONS): cv.BUILT_IN_CONDITIONS,
        vol.Optional(CONF_ACTIONS): [
            vol.Schema(
                {
                    vol.Optional(action): dict
                    for action, schema in itertools.islice(
                        cv.ACTION_TYPE_SCHEMAS.items(), 5
                    )
                }
            )
        ],
    },
    extra=vol.ALLOW_EXTRA,
)


def selector_serializer(value: Any) -> Any:
    """Custom serializer for selectors."""
    if callable(value):
        try:
            signature(value)
        except ValueError:
            return {"type": "object"}
        # # isinstance(value, datetime.timedelta):
        # assert value == "A", value
        # return {"type": "duration"}

    return llm.selector_serializer(value)


def blueprint_openapi_schema() -> dict[str, Any]:
    return convert(  # type: ignore[no-any-return]
        BLUEPRINT_SCHEMA, custom_serializer=selector_serializer
    )
