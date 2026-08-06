from homeassistant.const import Platform
import logging


class BleakRetryFilter(logging.Filter):
    _IGNORED = (
        "BleakClient.connect() called without bleak-retry-connector",
        "Unexpected json for",
    )
    def filter(self, record):
        message = record.getMessage()
        return not any(s in message for s in self._IGNORED)


logging.getLogger("habluetooth.wrappers").addFilter(BleakRetryFilter())
logging.getLogger("linkplay").addFilter(BleakRetryFilter())

from .api import MeshViewAPI
from .const import DOMAIN

PLATFORMS = [Platform.SENSOR]


async def async_setup(hass, config):
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass, entry):

    api = MeshViewAPI(entry.data["node_id"])

    hass.data[DOMAIN][entry.entry_id] = api

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(hass, entry):

    hass.data[DOMAIN].pop(entry.entry_id)

    return await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )