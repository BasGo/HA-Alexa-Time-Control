"""Config flow for Alexa Time Control integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AlexaTimeControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Alexa Time Control."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_alexa_entity_id: str | None = None

    async def async_step_discovery(
        self, discovery_info: dict[str, Any]
    ) -> FlowResult:
        """Handle discovery of an Alexa device."""
        alexa_entity_id = discovery_info["alexa_entity_id"]
        
        # Set unique ID and abort if already configured
        await self.async_set_unique_id(alexa_entity_id)
        self._abort_if_unique_id_configured()
        
        self._discovered_alexa_entity_id = alexa_entity_id
        
        # Get device name for the title
        state = self.hass.states.get(alexa_entity_id)
        device_name = state.attributes.get("friendly_name", alexa_entity_id.split(".")[-1]) if state else alexa_entity_id.split(".")[-1]
        
        # Set context for the discovered device
        self.context["title_placeholders"] = {"name": device_name}
        
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"Time Control - {self._discovered_alexa_entity_id.split('.')[-1]}",
                data={"alexa_entity_id": self._discovered_alexa_entity_id},
            )

        state = self.hass.states.get(self._discovered_alexa_entity_id)
        device_name = state.attributes.get("friendly_name", self._discovered_alexa_entity_id) if state else self._discovered_alexa_entity_id
        
        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders={"name": device_name},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            alexa_entity_id = user_input["alexa_entity_id"]
            
            # Create unique ID based on the Alexa entity
            await self.async_set_unique_id(alexa_entity_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Time Control - {alexa_entity_id.split('.')[-1]}",
                data=user_input,
            )

        # Get all media player entities that might be Alexa devices
        states = self.hass.states.async_all("media_player")
        alexa_entities = [
            state.entity_id for state in states
            if "alexa" in state.entity_id.lower() or 
               (state.attributes.get("integration") == "alexa_media")
        ]

        if not alexa_entities:
            alexa_entities = [state.entity_id for state in states]

        data_schema = vol.Schema(
            {
                vol.Required("alexa_entity_id"): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="media_player",
                    ),
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
