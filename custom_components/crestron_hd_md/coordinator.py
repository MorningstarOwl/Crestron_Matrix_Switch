"""DataUpdateCoordinator for the Crestron HD-MD integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import CONF_OUTPUTS, DOMAIN, SCAN_INTERVAL_SECONDS
from .crestron import CrestronConnectionError, CrestronHdMd

_LOGGER = logging.getLogger(__name__)


class CrestronCoordinator(DataUpdateCoordinator[dict[int, int]]):
    """Polls the switcher for the current routing state."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: CrestronHdMd,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.api = api
        self.outputs: int = entry.data[CONF_OUTPUTS]

    async def _async_update_data(self) -> dict[int, int]:
        try:
            return await self.api.async_get_routes(self.outputs)
        except CrestronConnectionError as err:
            raise UpdateFailed(str(err)) from err
