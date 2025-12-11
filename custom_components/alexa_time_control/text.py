"""Text platform for Alexa Time Control."""
from __future__ import annotations

import logging

from homeassistant.components.text import TextEntity
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
    """Set up the text entities."""
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
        AlexaTimeControlText(
            entry.entry_id,
            alexa_entity_id,
            device_info,
            "name",
        ),
    ]

    async_add_entities(entities)


class AlexaTimeControlText(TextEntity):
    """Representation of a name text entity."""

    _attr_has_entity_name = True
    _attr_native_min = 0
    _attr_native_max = 100

    def __init__(
        self,
        entry_id: str,
        alexa_entity_id: str,
        device_info: DeviceInfo | None,
        translation_key: str,
    ) -> None:
        """Initialize the text entity."""
        self._entry_id = entry_id
        self._alexa_entity_id = alexa_entity_id
        self._attr_unique_id = f"{alexa_entity_id}_{translation_key}"
        self._attr_translation_key = translation_key
        self._attr_native_value = ""
        self._attr_device_info = device_info

    async def async_set_value(self, value: str) -> None:
        """Update the current value."""
        self._attr_native_value = value
        self.async_write_ha_state()
