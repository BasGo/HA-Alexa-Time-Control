"""Switch platform for Alexa Time Control."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up the switch entities."""
    alexa_devices = hass.data[DOMAIN][entry.entry_id]["alexa_devices"]
    
    entities = []
    for alexa_entity_id in alexa_devices:
        # Create device info for this Alexa device
        device_info = DeviceInfo(
            identifiers={(DOMAIN, alexa_entity_id)},
        )
        
        entities.extend([
            AlexaTimeControlSwitch(
                entry.entry_id,
                alexa_entity_id,
                device_info,
                "enabled",
                False,
            ),
            AlexaTimeControlSwitch(
                entry.entry_id,
                alexa_entity_id,
                device_info,
                "blocked",
                False,
            ),
        ])

    async_add_entities(entities)


class AlexaTimeControlSwitch(SwitchEntity):
    """Representation of a time control switch entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry_id: str,
        alexa_entity_id: str,
        device_info: DeviceInfo | None,
        translation_key: str,
        default_state: bool,
    ) -> None:
        """Initialize the switch entity."""
        self._entry_id = entry_id
        self._alexa_entity_id = alexa_entity_id
        self._attr_unique_id = f"{alexa_entity_id}_{translation_key}"
        self._attr_translation_key = translation_key
        self._attr_is_on = default_state
        self._attr_device_info = device_info

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        self._attr_is_on = False
        self.async_write_ha_state()
