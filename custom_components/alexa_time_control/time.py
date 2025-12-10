"""Time platform for Alexa Time Control."""
from __future__ import annotations

import logging
from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the time entities."""
    alexa_devices = hass.data[DOMAIN][entry.entry_id]["alexa_devices"]
    
    entities = []
    for alexa_entity_id in alexa_devices:
        # Create device info for this Alexa device
        device_info = DeviceInfo(
            identifiers={(DOMAIN, alexa_entity_id)},
        )
        
        entities.extend([
            AlexaTimeControlTime(
                entry.entry_id,
                alexa_entity_id,
                device_info,
                "start_time",
                time(8, 0),
            ),
            AlexaTimeControlTime(
                entry.entry_id,
                alexa_entity_id,
                device_info,
                "end_time",
                time(20, 0),
            ),
        ])

    async_add_entities(entities)


class AlexaTimeControlTime(TimeEntity):
    """Representation of a time control time entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry_id: str,
        alexa_entity_id: str,
        device_info: DeviceInfo | None,
        translation_key: str,
        default_time: time,
    ) -> None:
        """Initialize the time entity."""
        self._entry_id = entry_id
        self._alexa_entity_id = alexa_entity_id
        self._attr_unique_id = f"{alexa_entity_id}_{translation_key}"
        self._attr_translation_key = translation_key
        self._attr_native_value = default_time
        self._attr_device_info = device_info

    async def async_set_value(self, value: time) -> None:
        """Update the current value."""
        self._attr_native_value = value
        self.async_write_ha_state()
