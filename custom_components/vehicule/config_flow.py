"""Configuration du carnet véhicule (une seule instance)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_ANNEE,
    CONF_IMMATRICULATION,
    CONF_KM_ACTUEL,
    CONF_MARQUE,
    CONF_MODELE,
    CONF_MOTEUR,
    CONF_NOM,
    CONF_VIN,
    DEFAULT_NOM,
    DOMAIN,
    VERSION,
)

SCHEMA_VEHICULE = vol.Schema(
    {
        vol.Required(CONF_NOM, default="BMW 325i E90"): cv.string,
        vol.Optional(CONF_MARQUE, default="BMW"): cv.string,
        vol.Optional(CONF_MODELE, default="325i E90"): cv.string,
        vol.Optional(CONF_ANNEE): vol.All(vol.Coerce(int), vol.Range(min=1900, max=2100)),
        vol.Optional(CONF_VIN): cv.string,
        vol.Optional(CONF_MOTEUR, default="N52B25"): cv.string,
        vol.Optional(CONF_IMMATRICULATION): cv.string,
        vol.Optional(CONF_KM_ACTUEL): vol.All(vol.Coerce(int), vol.Range(min=0)),
    }
)


class VehiculeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ajoute le carnet d'un véhicule."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            titre = user_input.get(CONF_NOM) or DEFAULT_NOM
            return self.async_create_entry(title=titre, data=user_input)

        return self.async_show_form(step_id="user", data_schema=SCHEMA_VEHICULE)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        return VehiculeOptionsFlow()


class VehiculeOptionsFlow(OptionsFlow):
    """Modifie l'identité du véhicule."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        vehicule = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_NOM, default=vehicule.get(CONF_NOM, DEFAULT_NOM)
                ): cv.string,
                vol.Optional(
                    CONF_MARQUE, default=vehicule.get(CONF_MARQUE, "")
                ): cv.string,
                vol.Optional(
                    CONF_MODELE, default=vehicule.get(CONF_MODELE, "")
                ): cv.string,
                vol.Optional(
                    CONF_ANNEE,
                    default=vehicule.get(CONF_ANNEE) or vol.UNDEFINED,
                ): vol.All(vol.Coerce(int), vol.Range(min=1900, max=2100)),
                vol.Optional(CONF_VIN, default=vehicule.get(CONF_VIN, "")): cv.string,
                vol.Optional(
                    CONF_MOTEUR, default=vehicule.get(CONF_MOTEUR, "")
                ): cv.string,
                vol.Optional(
                    CONF_IMMATRICULATION,
                    default=vehicule.get(CONF_IMMATRICULATION, ""),
                ): cv.string,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


__all__ = ["VehiculeConfigFlow", "VehiculeOptionsFlow", "VERSION"]
