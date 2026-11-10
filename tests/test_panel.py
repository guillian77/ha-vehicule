"""Tests du panneau : fichiers servis, enregistrement tolérant, cohérence JS."""

from __future__ import annotations

import json
from pathlib import Path

from custom_components.vehicule import panel
from custom_components.vehicule.const import DOMAIN

DOSSIER = Path(__file__).parent.parent / "custom_components" / "vehicule"


def test_le_fichier_js_existe_et_declare_lelement():
    contenu = (DOSSIER / "www" / "panel.js").read_text(encoding="utf-8")
    assert 'customElements.define("vehicule-panel"' in contenu
    assert panel.PANEL_WEBCOMPONENT == "vehicule-panel"
    # Aucune dépendance distante : tout doit fonctionner hors ligne.
    assert "http://" not in contenu
    assert "https://" not in contenu


def test_version_alignee_sur_le_manifest():
    from custom_components.vehicule.const import VERSION

    manifest = json.loads((DOSSIER / "manifest.json").read_text(encoding="utf-8"))
    assert VERSION == manifest["version"], "const.VERSION doit suivre manifest.json"


def test_manifest_declare_les_dependances_du_panneau():
    manifest = json.loads((DOSSIER / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["domain"] == DOMAIN
    assert "panel_custom" in manifest["dependencies"]
    assert "websocket_api" in manifest["dependencies"]


async def test_enregistrement_reel_du_panneau(hass):
    """Le panneau est réellement enregistré auprès du frontend (await compris)."""
    from homeassistant.components import frontend
    from homeassistant.setup import async_setup_component

    assert await async_setup_component(hass, "frontend", {})
    hass.data.pop(f"{DOMAIN}_panel", None)

    await panel.async_register_panel(hass)

    assert hass.data.get(f"{DOMAIN}_panel") is True
    panneau = hass.data[frontend.DATA_PANELS]["vehicule"]
    assert panneau.component_name == "custom"
    details = panneau.config["_panel_custom"]
    assert details["name"] == "vehicule-panel"
    assert details["module_url"].startswith("/vehicule_panel/panel.js?v=")
    assert panneau.sidebar_title == "Véhicule"
    assert panneau.require_admin is False

    # Chemin statique du JS monté sur le serveur HTTP embarqué.
    routes = [str(getattr(route, "resource", "")) for route in hass.http.app.router.routes()]
    assert any("/vehicule_panel" in route and "/www" in route for route in routes)

    # Second appel : idempotent, pas de doublon ni d'exception.
    await panel.async_register_panel(hass)
    assert list(hass.data[frontend.DATA_PANELS]).count("vehicule") == 1


async def test_enregistrement_sans_frontend_ne_plante_pas(hass):
    """Sans composant HTTP, l'enregistrement reste silencieux et réessayable."""
    hass.data.pop(f"{DOMAIN}_panel", None)
    await panel.async_register_panel(hass)
    assert not hass.data.get(f"{DOMAIN}_panel")


def test_chemins_du_panneau():
    assert panel.PANEL_URL_PATH == "vehicule"
    assert panel.STATIC_URL == "/vehicule_panel"
    assert panel.PANEL_ICONE == "mdi:car-wrench"
