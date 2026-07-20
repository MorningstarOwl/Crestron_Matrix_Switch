"""Config flow for the Crestron HD-MD Matrix Switch integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback

from .const import (
    CONF_INPUTS,
    CONF_OUTPUTS,
    DEFAULT_INPUTS,
    DEFAULT_OUTPUTS,
    DEFAULT_PORT,
    DOMAIN,
    OPT_INPUT_NAME,
    OPT_OUTPUT_NAME,
)
from .crestron import CrestronConnectionError, CrestronHdMd

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
        vol.Required(CONF_INPUTS, default=DEFAULT_INPUTS): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=8)
        ),
        vol.Required(CONF_OUTPUTS, default=DEFAULT_OUTPUTS): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=8)
        ),
    }
)


class CrestronHdMdConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup of a switcher."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api = CrestronHdMd(user_input[CONF_HOST], user_input[CONF_PORT])
            try:
                await api.async_test_connection()
            except CrestronConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error probing switcher")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"HD-MD ({user_input[CONF_HOST]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                USER_SCHEMA, user_input
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> CrestronOptionsFlow:
        """Return the options flow handler."""
        return CrestronOptionsFlow()


class CrestronOptionsFlow(OptionsFlow):
    """Let the user give friendly names to inputs and outputs."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show one text field per input and output."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        entry = self.config_entry
        options = entry.options
        schema: dict[Any, Any] = {}

        for i in range(1, entry.data[CONF_INPUTS] + 1):
            key = OPT_INPUT_NAME.format(i)
            schema[
                vol.Required(
                    key, default=options.get(key, f"Input {i}")
                )
            ] = str

        for o in range(1, entry.data[CONF_OUTPUTS] + 1):
            key = OPT_OUTPUT_NAME.format(o)
            schema[
                vol.Required(
                    key, default=options.get(key, f"Output {o}")
                )
            ] = str

        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(schema)
        )
