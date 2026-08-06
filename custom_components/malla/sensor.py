from __future__ import annotations

import asyncio

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    api = hass.data[DOMAIN][entry.entry_id]
    api._refresh_lock = asyncio.Lock()
    api._last_refresh_task = None

    async_add_entities(
        [
            MeshSentSensor(api),
            MeshReportedSensor(api),
            MeshHealthSensor(api),
        ]
    )


class MeshBaseSensor(SensorEntity):
    _attr_should_poll = True

    def __init__(self, api):
        self.api = api
        self._packets = []
        self._state = 0

    async def _refresh_once(self):
        async with self.api._refresh_lock:
            await self.hass.async_add_executor_job(self.api.refresh)

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        # Evita superar el límite de 16 KB de atributos del Recorder
        MAX_EXPOSED_PACKETS = 10

        return {
            "packets": self._packets[:MAX_EXPOSED_PACKETS],
            "total_packets": len(self._packets),
        }


class MeshSentSensor(MeshBaseSensor):
    _attr_name = "Malla Sent"
    _attr_unique_id = "malla_sent"

    async def async_update(self):
        await self._refresh_once()
        self._packets = self.api.sent
        self._state = len(self._packets)


class MeshReportedSensor(MeshBaseSensor):
    _attr_name = "Malla Reported"
    _attr_unique_id = "malla_reported"

    async def async_update(self):
        await self._refresh_once()
        self._packets = self.api.reported
        self._state = len(self._packets)
        
class MeshHealthSensor(MeshBaseSensor):
    _attr_name = "Malla Health"
    _attr_unique_id = "malla_health"
    _attr_icon = "mdi:heart-pulse"

    async def async_update(self):
        await self._refresh_once()

        if self.api.last_success:
            self._state = "Online"
        else:
            self._state = "Offline"

    @property
    def extra_state_attributes(self):
        return {
            "last_success": self.api.last_success,
            "last_error": self.api.last_error,
            "latency_ms": self.api.last_latency,
            "error_count": self.api.error_count,
            "circuit_breaker": (
                "Open"
                if self.api._circuit_open_until > 0
                else "Closed"
            ),
        }