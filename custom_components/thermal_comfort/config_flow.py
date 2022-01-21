"""Tests for config flows."""
from __future__ import annotations

import logging

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import entity_registry
import voluptuous as vol

from .const import (
    CONF_HUMIDITY_SENSOR,
    CONF_POLL,
    CONF_TEMPERATURE_SENSOR,
    DEFAULT_NAME,
    DOMAIN,
)
from .sensor import SensorType

_LOGGER = logging.getLogger(__name__)


def get_value(
    config_entry: config_entries.ConfigEntry | None, param: str, default=None
):
    """Get current value for configuration parameter.

    :param config_entry: config_entries|None: config entry from Flow
    :param param: str: parameter name for getting value
    :param default: default value for parameter, defaults to None
    :returns: parameter value, or default value or None
    """
    if config_entry is not None:
        return config_entry.options.get(param, config_entry.data.get(param, default))
    else:
        return default


def build_schema(config_entry: config_entries | None) -> vol.Schema:
    """Build configuration schema.

    :param config_entry: config entry for getting current parameters on None
    :return: Configuration schema with default parameters
    """
    # ToDo: get list of CONF_TEMPERATURE_SENSOR and CONF_HUMIDITY_SENSOR to create dropdown list and "one of" selection
    schema = vol.Schema(
        {
            vol.Required(
                CONF_NAME, default=get_value(config_entry, CONF_NAME, DEFAULT_NAME)
            ): str,
            vol.Required(
                CONF_TEMPERATURE_SENSOR,
                default=get_value(config_entry, CONF_TEMPERATURE_SENSOR),
            ): str,
            vol.Required(
                CONF_HUMIDITY_SENSOR,
                default=get_value(config_entry, CONF_HUMIDITY_SENSOR),
            ): str,
            vol.Optional(
                CONF_POLL, default=get_value(config_entry, CONF_POLL, False)
            ): bool,
        }
    )

    for st in SensorType:
        schema = schema.extend(
            {
                vol.Optional(
                    str(st), default=get_value(config_entry, str(st), True)
                ): bool
            }
        )

    return schema


class ThermalComfortConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configuration flow for setting up new thermal_comfort entry."""

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return ThermalComfortOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            er = entity_registry.async_get(self.hass)

            t_sensor = er.async_get(user_input[CONF_TEMPERATURE_SENSOR])
            p_sensor = er.async_get(user_input[CONF_HUMIDITY_SENSOR])
            _LOGGER.debug(f"Going to use t_sensor {t_sensor}")
            _LOGGER.debug(f"Going to use p_sensor {p_sensor}")

            if t_sensor is None:
                self.async_abort(reason="Temperature sensor not found")

            if p_sensor is None:
                self.async_abort(reason="Pressure sensor not found")

            await self.async_set_unique_id(f"{t_sensor.unique_id}-{p_sensor.unique_id}")
            self._abort_if_unique_id_configured()

            # ToDo: we should not trust user and check:
            #  - that t_sensor is temperature sensor and have state_class measurement
            #  - that p_sensor is humidity sensor and have state_class measurement

            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=build_schema(None), errors=errors
        )


class ThermalComfortOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            _LOGGER.debug(f"OptionsFlow: configuration updated {user_input}")
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=build_schema(self.config_entry),
        )
