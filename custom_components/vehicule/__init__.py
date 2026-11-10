"""Intégration Véhicule — carnet d'entretien pour Home Assistant."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ANNEE,
    CONF_IMMATRICULATION,
    CONF_KM_ACTUEL,
    CONF_MARQUE,
    CONF_MODELE,
    CONF_MOTEUR,
    CONF_NOM,
    CONF_VIN,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import CarnetCoordinator
from .panel import async_register_panel
from .services import async_setup_services, async_unload_services
from .websocket import async_register_websocket

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Services et API websocket disponibles dès le chargement."""
    await async_setup_services(hass)
    async_register_websocket(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Charge le carnet et démarre les entités."""
    coordinator = CarnetCoordinator(hass, entry)
    await coordinator.async_load()
    await _async_apply_entry_data(coordinator, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await async_setup_services(hass)
    async_register_websocket(hass)
    _async_schedule_panel(hass)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharge les plateformes et retire les services si plus rien n'est chargé."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        async_unload_services(hass)
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


def _async_schedule_panel(hass: HomeAssistant) -> None:
    """Le panneau ne peut être enregistré qu'une fois le frontend prêt."""
    if hass.is_running:
        hass.async_create_task(async_register_panel(hass))
        return

    async def _on_started(_event) -> None:
        await async_register_panel(hass)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_started)


async def _async_apply_entry_data(
    coordinator: CarnetCoordinator, entry: ConfigEntry
) -> None:
    """Reporte les valeurs de la config entry dans profil.json (premier lancement)."""
    source = {**entry.data, **entry.options}
    vehicule = coordinator.vehicule
    modifie = False

    for cle, champ in (
        (CONF_NOM, "nom"),
        (CONF_MARQUE, "marque"),
        (CONF_MODELE, "modele"),
        (CONF_ANNEE, "annee"),
        (CONF_VIN, "vin"),
        (CONF_MOTEUR, "moteur"),
        (CONF_IMMATRICULATION, "immatriculation"),
    ):
        valeur = source.get(cle)
        if valeur not in (None, "") and not vehicule.get(champ):
            vehicule[champ] = valeur
            modifie = True

    if coordinator.km_actuel is None and source.get(CONF_KM_ACTUEL) is not None:
        try:
            vehicule["km_actuel"] = int(source[CONF_KM_ACTUEL])
            modifie = True
        except (TypeError, ValueError):
            _LOGGER.warning("Kilométrage initial invalide : %s", source.get(CONF_KM_ACTUEL))

    if modifie:
        await coordinator.storage.async_save_profil(coordinator.profil)
