"""The Alexa Time Control integration."""
from __future__ import annotations

import logging
from datetime import datetime, time

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event

_LOGGER = logging.getLogger(__name__)

DOMAIN = "alexa_time_control"
PLATFORMS: list[Platform] = [Platform.TIME, Platform.SWITCH, Platform.TEXT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Alexa Time Control from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "alexa_devices": {},
        "listeners": []
    }

    # Discover and set up Alexa devices
    await _async_discover_and_setup_devices(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up state listener after entities are created
    async def async_setup_listener(event):
        """Set up the state listener after entities are ready."""
        for alexa_entity_id in hass.data[DOMAIN][entry.entry_id]["alexa_devices"]:
            await _async_setup_state_listener(hass, entry, alexa_entity_id)

    hass.bus.async_listen_once("homeassistant_started", async_setup_listener)

    return True


async def _async_discover_and_setup_devices(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Discover Alexa media players and create devices for them."""
    # Get all media player entities
    states = hass.states.async_all("media_player")
    
    device_registry = dr.async_get(hass)
    
    # Find Alexa media players
    for state in states:
        # Check if it's an Alexa device
        if "alexa" in state.entity_id.lower() or state.attributes.get("integration") == "alexa_media":
            alexa_entity_id = state.entity_id
            device_name = state.attributes.get("friendly_name", alexa_entity_id.split(".")[-1])
            
            # Create a device for this Alexa media player
            device = device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, alexa_entity_id)},
                name=device_name,
                manufacturer="Amazon",
                model="Alexa Device with Time Control",
            )
            
            # Store the device info
            hass.data[DOMAIN][entry.entry_id]["alexa_devices"][alexa_entity_id] = {
                "device_id": device.id,
                "name": device_name,
            }


async def _async_setup_state_listener(hass: HomeAssistant, entry: ConfigEntry, alexa_entity_id: str) -> None:
    """Set up the state change listener for the Alexa device."""
    entry_id = entry.entry_id

    @callback
    async def async_state_changed(event):
        """Handle state changes of the Alexa media player."""
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        if new_state is None or new_state.state != "playing":
            return

        if old_state and old_state.state == "playing":
            return

        # Get the control entities
        entity_reg = er.async_get(hass)
        entities = er.async_entries_for_config_entry(entity_reg, entry_id)

        enabled_entity = None
        blocked_entity = None
        start_time_entity = None
        end_time_entity = None
        name_entity = None

        for entity in entities:
            if entity.unique_id.endswith("_enabled"):
                enabled_entity = entity.entity_id
            elif entity.unique_id.endswith("_blocked"):
                blocked_entity = entity.entity_id
            elif entity.unique_id.endswith("_start_time"):
                start_time_entity = entity.entity_id
            elif entity.unique_id.endswith("_end_time"):
                end_time_entity = entity.entity_id
            elif entity.unique_id.endswith("_name"):
                name_entity = entity.entity_id

        if not all([enabled_entity, blocked_entity, start_time_entity, end_time_entity]):
            _LOGGER.warning("Not all control entities found for %s", alexa_entity_id)
            return

        # Check if enabled
        enabled_state = hass.states.get(enabled_entity)
        if not enabled_state or enabled_state.state != "on":
            return

        # Get the name for TTS prefix
        name_prefix = ""
        if name_entity:
            name_state = hass.states.get(name_entity)
            if name_state and name_state.state:
                name_prefix = f"{name_state.state}, "

        # Check if blocked
        blocked_state = hass.states.get(blocked_entity)
        if blocked_state and blocked_state.state == "on":
            message = _get_translation(hass, "blocked", name_prefix)
            await _send_tts_and_stop(hass, alexa_entity_id, message)
            return

        # Check time constraints
        start_time_state = hass.states.get(start_time_entity)
        end_time_state = hass.states.get(end_time_entity)

        if not start_time_state or not end_time_state:
            return

        try:
            # Parse time strings (format: HH:MM:SS)
            start_time_parts = start_time_state.state.split(":")
            end_time_parts = end_time_state.state.split(":")
            
            start_hour = int(start_time_parts[0])
            start_minute = int(start_time_parts[1]) if len(start_time_parts) > 1 else 0
            end_hour = int(end_time_parts[0])
            end_minute = int(end_time_parts[1]) if len(end_time_parts) > 1 else 0
            
            now = datetime.now()
            current_minutes = now.hour * 60 + now.minute
            start_minutes = start_hour * 60 + start_minute
            end_minutes = end_hour * 60 + end_minute
            
            # Check if current time is outside allowed range
            if start_minutes <= end_minutes:
                # Normal range (e.g., 8:00 to 20:00)
                is_outside = current_minutes < start_minutes or current_minutes >= end_minutes
            else:
                # Range crosses midnight (e.g., 20:00 to 8:00)
                is_outside = current_minutes >= end_minutes and current_minutes < start_minutes

            if is_outside:
                current_time_str = now.strftime("%H:%M")
                start_time_str = f"{start_hour:02d}:{start_minute:02d}"
                end_time_str = f"{end_hour:02d}:{end_minute:02d}"
                
                message = _get_translation(
                    hass, "time_restricted", name_prefix,
                    current_time_str, end_time_str, start_time_str
                )
                await _send_tts_and_stop(hass, alexa_entity_id, message)

        except (ValueError, TypeError) as err:
            _LOGGER.error("Error processing time values: %s", err)

    # Register the listener
    remove_listener = async_track_state_change_event(
        hass, [alexa_entity_id], async_state_changed
    )
    hass.data[DOMAIN][entry.entry_id]["listeners"].append(remove_listener)


def _get_translation(
    hass: HomeAssistant,
    message_type: str,
    name_prefix: str,
    current_time: str = "",
    end_time: str = "",
    start_time: str = "",
) -> str:
    """Get translated TTS message."""
    language = hass.config.language or "en"
    
    messages = {
        "en": {
            "blocked": f"{name_prefix}, your device is currently blocked",
            "time_restricted": (
                f"{name_prefix}, actually it is {current_time}, "
                f"your alexa has been enabled up to {end_time} "
                f"and can be used at {start_time} again"
            ),
        },
        "de": {
            "blocked": f"{name_prefix}, dein Gerät ist derzeit gesperrt",
            "time_restricted": (
                f"{name_prefix}, es ist jetzt {current_time}, "
                f"deine Alexa ist bis {end_time} freigeschaltet "
                f"und kann ab {start_time} wieder benutzt werden"
            ),
        },
    }
    
    # Default to English if language not found
    lang_messages = messages.get(language, messages["en"])
    return lang_messages.get(message_type, "")


async def _send_tts_and_stop(hass: HomeAssistant, entity_id: str, message: str) -> None:
    """Send TTS message and stop the media player."""
    # Send TTS notification
    await hass.services.async_call(
        "notify",
        entity_id.replace("media_player.", "alexa_media_"),
        {
            "message": message,
            "data": {
                "type": "tts"
            }
        },
        blocking=True
    )

    # Stop the media player
    await hass.services.async_call(
        "media_player",
        "media_stop",
        {"entity_id": entity_id},
        blocking=False
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Remove state listeners
    for remove_listener in hass.data[DOMAIN][entry.entry_id]["listeners"]:
        remove_listener()

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
