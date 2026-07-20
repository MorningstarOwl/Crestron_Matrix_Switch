"""Select entities — one source picker per switcher output."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CrestronConfigEntry
from .const import (
    CONF_INPUTS,
    DOMAIN,
    OPT_INPUT_NAME,
    OPT_OUTPUT_NAME,
    OPTION_NONE,
    ROUTE_NONE,
)
from .coordinator import CrestronCoordinator
from .crestron import CrestronConnectionError

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CrestronConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one select entity per output."""
    coordinator = entry.runtime_data

    input_names = {
        i: entry.options.get(OPT_INPUT_NAME.format(i), f"Input {i}")
        for i in range(1, entry.data[CONF_INPUTS] + 1)
    }

    async_add_entities(
        CrestronOutputSelect(
            coordinator,
            entry,
            output,
            entry.options.get(OPT_OUTPUT_NAME.format(output), f"Output {output}"),
            input_names,
        )
        for output in range(1, coordinator.outputs + 1)
    )


class CrestronOutputSelect(
    CoordinatorEntity[CrestronCoordinator], SelectEntity
):
    """A dropdown that routes an input to one switcher output."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:video-switch"

    def __init__(
        self,
        coordinator: CrestronCoordinator,
        entry: CrestronConfigEntry,
        output: int,
        output_name: str,
        input_names: dict[int, str],
    ) -> None:
        super().__init__(coordinator)
        self._output = output
        self._input_names = input_names
        self._attr_name = output_name
        self._attr_unique_id = f"{entry.entry_id}_output_{output}"
        self._attr_options = [OPTION_NONE, *input_names.values()]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Crestron",
            model="HD-MD Series HDMI Switcher",
            configuration_url=f"http://{coordinator.api.host}",
        )

    @property
    def current_option(self) -> str | None:
        """Return the input currently routed to this output."""
        route = self.coordinator.data.get(self._output)
        if route is None:
            return None
        if route == ROUTE_NONE:
            return OPTION_NONE
        return self._input_names.get(route, f"Input {route}")

    async def async_select_option(self, option: str) -> None:
        """Route the chosen input to this output."""
        if option == OPTION_NONE:
            route = ROUTE_NONE
        else:
            route = next(
                num
                for num, name in self._input_names.items()
                if name == option
            )

        try:
            confirmed = await self.coordinator.api.async_set_route(
                self._output, route
            )
        except CrestronConnectionError as err:
            _LOGGER.error(
                "Failed to route input %s to output %s: %s",
                route,
                self._output,
                err,
            )
            return

        # The device confirms the route in its reply, so update
        # immediately instead of waiting for the next poll.
        self.coordinator.data[self._output] = confirmed
        self.coordinator.async_set_updated_data(self.coordinator.data)
