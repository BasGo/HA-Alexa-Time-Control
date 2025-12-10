"""Switch platform for Alexa Time Control."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
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
    alexa_entity_id = entry.data["alexa_entity_id"]
    
    # Get the device info from the existing Alexa entity
    entity_reg = er.async_get(hass)
    alexa_entity = entity_reg.async_get(alexa_entity_id)
    
    device_info = None
    if alexa_entity and alexa_entity.device_id:
        device_reg = dr.async_get(hass)
        device = device_reg.async_get(alexa_entity.device_id)
        if device:
            device_info = DeviceInfo(
                identifiers=device.identifiers,
            )

    entities = [
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
    ]

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
