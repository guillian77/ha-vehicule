"""Enregistrement du panneau frontend (panel_custom)."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.core import HomeAssistant

from .const import DOMAIN, VERSION

_LOGGER = logging.getLogger(__name__)

PANEL_URL_PATH = DOMAIN  # /vehicule
STATIC_URL = f"/{DOMAIN}_panel"
MODULE_PATH = "panel.js"
PANEL_WEBCOMPONENT = "vehicule-panel"
PANEL_TITLE = "Véhicule"
PANEL_ICONE = "mdi:car-wrench"


async def async_register_panel(hass: HomeAssistant) -> None:
    """Publie le JS et ajoute l'entrée dans la barre latérale (une fois)."""
    if hass.data.get(f"{DOMAIN}_panel"):
        return

    http = getattr(hass, "http", None)
    if http is None:
        _LOGGER.debug("HTTP non disponible : panneau non enregistré")
        return

    try:
        from homeassistant.components.http import StaticPathConfig

        await http.async_register_static_paths(
            [
                StaticPathConfig(
                    STATIC_URL,
                    str(Path(__file__).parent / "www"),
                    cache_headers=False,
                )
            ]
        )
    except Exception as err:  # pragma: no cover - déjà monté / contexte de test
        _LOGGER.debug("Chemin statique du panneau non enregistré : %s", err)

    module_url = f"{STATIC_URL}/{MODULE_PATH}?v={VERSION}"
    try:
        from homeassistant.components.panel_custom import async_register_panel as register

        await register(
            hass,
            frontend_url_path=PANEL_URL_PATH,
            webcomponent_name=PANEL_WEBCOMPONENT,
            sidebar_title=PANEL_TITLE,
            sidebar_icon=PANEL_ICONE,
            module_url=module_url,
            config={"domain": DOMAIN},
            require_admin=False,
        )
        hass.data[f"{DOMAIN}_panel"] = True
        _LOGGER.debug("Panneau Véhicule enregistré : /%s (%s)", PANEL_URL_PATH, module_url)
    except Exception as err:  # pragma: no cover - frontend absent (tests)
        _LOGGER.warning("Impossible d'enregistrer le panneau Véhicule : %s", err)


def async_unregister_panel(hass: HomeAssistant) -> None:
    """Retire l'entrée de la barre latérale."""
    if not hass.data.get(f"{DOMAIN}_panel"):
        return
    try:
        from homeassistant.components import frontend

        frontend.async_remove_panel(hass, PANEL_URL_PATH)
    except Exception as err:  # pragma: no cover
        _LOGGER.debug("Retrait du panneau impossible : %s", err)
    hass.data[f"{DOMAIN}_panel"] = False
