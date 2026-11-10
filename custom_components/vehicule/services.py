"""Services du carnet d'entretien."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from .const import (
    ATTR_ACTIF,
    ATTR_ANNEE,
    ATTR_COUT,
    ATTR_DATE,
    ATTR_FORMAT,
    ATTR_GARAGE,
    ATTR_ICONE,
    ATTR_ID,
    ATTR_IMMATRICULATION,
    ATTR_KM,
    ATTR_MARQUE,
    ATTR_MODELE,
    ATTR_MOIS,
    ATTR_MOTEUR,
    ATTR_NOM,
    ATTR_NOM_FICHIER,
    ATTR_NOTES,
    ATTR_PIECES,
    ATTR_POSTE,
    ATTR_PROCHAIN_DATE,
    ATTR_PROCHAIN_KM,
    ATTR_TYPE,
    ATTR_VIN,
    DOMAIN,
    SERVICE_DEFINIR_POSTE,
    SERVICE_ENREGISTRER,
    SERVICE_EXPORTER,
    SERVICE_MAJ_KM,
    SERVICE_MAJ_VEHICULE,
    SERVICE_MODIFIER,
    SERVICE_SUPPRIMER,
)

_LOGGER = logging.getLogger(__name__)

SCHEMA_PIECE = vol.Schema(
    {
        vol.Required("nom"): vol.Coerce(str),
        vol.Optional("qte"): vol.Any(None, vol.Coerce(float)),
        vol.Optional("ref"): vol.Any(None, vol.Coerce(str)),
        vol.Optional("prix"): vol.Any(None, vol.Coerce(float)),
    }
)

SCHEMA_ENREGISTRER = vol.Schema(
    {
        vol.Required(ATTR_TYPE): vol.Coerce(str),
        vol.Optional(ATTR_NOM): vol.Coerce(str),
        vol.Optional(ATTR_DATE): vol.Coerce(str),
        vol.Optional(ATTR_KM): vol.Any(None, vol.Coerce(int)),
        vol.Optional(ATTR_PIECES): vol.Any(None, [vol.Any(SCHEMA_PIECE, vol.Coerce(str))]),
        vol.Optional(ATTR_COUT): vol.Any(None, vol.Coerce(float)),
        vol.Optional(ATTR_GARAGE): vol.Any(None, vol.Coerce(str)),
        vol.Optional(ATTR_NOTES): vol.Any(None, vol.Coerce(str)),
        vol.Optional(ATTR_PROCHAIN_KM): vol.Any(None, vol.Coerce(int)),
        vol.Optional(ATTR_PROCHAIN_DATE): vol.Any(None, vol.Coerce(str)),
    }
)

SCHEMA_MODIFIER = vol.Schema(
    {
        vol.Required(ATTR_ID): vol.Coerce(str),
        vol.Optional(ATTR_TYPE): vol.Coerce(str),
        vol.Optional(ATTR_NOM): vol.Coerce(str),
        vol.Optional(ATTR_DATE): vol.Coerce(str),
        vol.Optional(ATTR_KM): vol.Any(None, vol.Coerce(int)),
        vol.Optional(ATTR_PIECES): vol.Any(
            None, [vol.Any(SCHEMA_PIECE, vol.Coerce(str))]
        ),
        vol.Optional(ATTR_COUT): vol.Any(None, vol.Coerce(float)),
        vol.Optional(ATTR_GARAGE): vol.Any(None, vol.Coerce(str)),
        vol.Optional(ATTR_NOTES): vol.Any(None, vol.Coerce(str)),
        vol.Optional(ATTR_PROCHAIN_KM): vol.Any(None, vol.Coerce(int)),
        vol.Optional(ATTR_PROCHAIN_DATE): vol.Any(None, vol.Coerce(str)),
    }
)

SCHEMA_SUPPRIMER = vol.Schema({vol.Required(ATTR_ID): vol.Coerce(str)})

SCHEMA_MAJ_KM = vol.Schema(
    {
        vol.Required(ATTR_KM): vol.Coerce(int),
        vol.Optional(ATTR_DATE): vol.Coerce(str),
    }
)

SCHEMA_EXPORTER = vol.Schema(
    {
        vol.Optional(ATTR_FORMAT, default="csv"): vol.In(["csv", "json"]),
        vol.Optional(ATTR_NOM_FICHIER): vol.Coerce(str),
    }
)

SCHEMA_MAJ_VEHICULE = vol.Schema(
    {
        vol.Optional(ATTR_NOM): vol.Coerce(str),
        vol.Optional(ATTR_MARQUE): vol.Coerce(str),
        vol.Optional(ATTR_MODELE): vol.Coerce(str),
        vol.Optional(ATTR_ANNEE): vol.Any(None, vol.Coerce(int)),
        vol.Optional(ATTR_VIN): vol.Coerce(str),
        vol.Optional(ATTR_MOTEUR): vol.Coerce(str),
        vol.Optional(ATTR_IMMATRICULATION): vol.Coerce(str),
    }
)

SCHEMA_DEFINIR_POSTE = vol.Schema(
    {
        vol.Required(ATTR_POSTE): vol.Coerce(str),
        vol.Optional(ATTR_NOM): vol.Coerce(str),
        vol.Optional(ATTR_KM): vol.Any(None, vol.Coerce(int)),
        vol.Optional(ATTR_MOIS): vol.Any(None, vol.Coerce(int)),
        vol.Optional(ATTR_ICONE): vol.Coerce(str),
        vol.Optional(ATTR_ACTIF): vol.Coerce(bool),
    }
)

SERVICES: dict[str, Any] = {
    SERVICE_ENREGISTRER: SCHEMA_ENREGISTRER,
    SERVICE_MODIFIER: SCHEMA_MODIFIER,
    SERVICE_SUPPRIMER: SCHEMA_SUPPRIMER,
    SERVICE_MAJ_KM: SCHEMA_MAJ_KM,
    SERVICE_EXPORTER: SCHEMA_EXPORTER,
    SERVICE_MAJ_VEHICULE: SCHEMA_MAJ_VEHICULE,
    SERVICE_DEFINIR_POSTE: SCHEMA_DEFINIR_POSTE,
}


def get_coordinator(hass: HomeAssistant):
    """Renvoie le coordinateur de l'unique véhicule configuré."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return entry.runtime_data
    raise HomeAssistantError(
        "Aucun carnet véhicule chargé : ajoute l'intégration via Paramètres → "
        "Appareils et services."
    )


async def async_setup_services(hass: HomeAssistant) -> None:
    """Enregistre les services (une seule fois)."""
    if hass.services.has_service(DOMAIN, SERVICE_ENREGISTRER):
        return

    async def _enregistrer(call: ServiceCall) -> None:
        coordinator = get_coordinator(hass)
        try:
            await coordinator.async_enregistrer(dict(call.data))
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err

    async def _modifier(call: ServiceCall) -> None:
        coordinator = get_coordinator(hass)
        data = dict(call.data)
        identifiant = data.pop(ATTR_ID)
        try:
            await coordinator.async_modifier(identifiant, data)
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err

    async def _supprimer(call: ServiceCall) -> None:
        coordinator = get_coordinator(hass)
        try:
            await coordinator.async_supprimer(call.data[ATTR_ID])
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err

    async def _maj_km(call: ServiceCall) -> None:
        coordinator = get_coordinator(hass)
        await coordinator.async_maj_km(call.data[ATTR_KM], call.data.get(ATTR_DATE))

    async def _exporter(call: ServiceCall) -> dict[str, Any]:
        coordinator = get_coordinator(hass)
        try:
            return await coordinator.async_exporter(
                call.data.get(ATTR_FORMAT, "csv"),
                call.data.get(ATTR_NOM_FICHIER),
            )
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err

    async def _maj_vehicule(call: ServiceCall) -> None:
        coordinator = get_coordinator(hass)
        await coordinator.async_maj_profil(dict(call.data))

    async def _definir_poste(call: ServiceCall) -> None:
        coordinator = get_coordinator(hass)
        try:
            await coordinator.async_definir_poste(dict(call.data))
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err

    hass.services.async_register(
        DOMAIN, SERVICE_ENREGISTRER, _enregistrer, schema=SCHEMA_ENREGISTRER
    )
    hass.services.async_register(
        DOMAIN, SERVICE_MODIFIER, _modifier, schema=SCHEMA_MODIFIER
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SUPPRIMER, _supprimer, schema=SCHEMA_SUPPRIMER
    )
    hass.services.async_register(DOMAIN, SERVICE_MAJ_KM, _maj_km, schema=SCHEMA_MAJ_KM)
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORTER,
        _exporter,
        schema=SCHEMA_EXPORTER,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_MAJ_VEHICULE, _maj_vehicule, schema=SCHEMA_MAJ_VEHICULE
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DEFINIR_POSTE, _definir_poste, schema=SCHEMA_DEFINIR_POSTE
    )


def async_unload_services(hass: HomeAssistant) -> None:
    """Retire les services quand plus aucun carnet n'est chargé."""
    if hass.config_entries.async_entries(DOMAIN):
        return
    for service in SERVICES:
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)
