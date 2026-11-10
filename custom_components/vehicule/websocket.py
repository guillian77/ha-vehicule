"""API websocket utilisée par le panneau frontend."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .services import get_coordinator

_LOGGER = logging.getLogger(__name__)


@callback
def async_register_websocket(hass: HomeAssistant) -> None:
    """Enregistre les commandes WS (idempotent)."""
    if hass.data.get(f"{DOMAIN}_ws"):
        return
    websocket_api.async_register_command(hass, ws_data)
    websocket_api.async_register_command(hass, ws_reload)
    hass.data[f"{DOMAIN}_ws"] = True


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/data"}
)
@websocket_api.async_response
async def ws_data(hass: HomeAssistant, connection, msg) -> None:
    """Renvoie l'état complet du carnet."""
    try:
        coordinator = get_coordinator(hass)
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "not_loaded", str(err))
        return
    connection.send_result(
        msg["id"],
        {
            **coordinator.data,
            "dossier": str(coordinator.storage.folder),
            "exports": str(coordinator.storage.exports_path),
        },
    )


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/reload"}
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_reload(hass: HomeAssistant, connection, msg) -> None:
    """Relit les fichiers JSON (après édition manuelle)."""
    try:
        coordinator = get_coordinator(hass)
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "not_loaded", str(err))
        return
    await coordinator.async_reload_from_disk()
    connection.send_result(msg["id"], {"ok": True, "interventions": len(coordinator.interventions)})
