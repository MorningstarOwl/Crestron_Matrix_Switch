"""The Crestron HD-MD Matrix Switch integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .coordinator import CrestronCoordinator
from .crestron import CrestronConnectionError, CrestronHdMd

PLATFORMS: list[Platform] = [Platform.SELECT]

CrestronConfigEntry = ConfigEntry[CrestronCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: CrestronConfigEntry
) -> bool:
    """Set up Crestron HD-MD from a config entry."""
    api = CrestronHdMd(entry.data[CONF_HOST], entry.data[CONF_PORT])

    try:
        await api.async_test_connection()
    except CrestronConnectionError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = CrestronCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: CrestronConfigEntry
) -> None:
    """Reload the entry when options (input/output names) change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: CrestronConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
