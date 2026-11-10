"""Capteurs du carnet : kilométrage, échéances par poste, synthèse."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    ETA_DEPASSE,
    ETA_INCONNU,
    ETA_OK,
    ETA_PREVOIR,
)
from .entity import CarnetEntity

_LOGGER = logging.getLogger(__name__)

ICONES_ETAT = {
    ETA_DEPASSE: "mdi:alert-circle",
    ETA_PREVOIR: "mdi:clock-alert-outline",
    ETA_OK: "mdi:check-circle-outline",
    ETA_INCONNU: "mdi:help-circle-outline",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        KmActuelSensor(coordinator),
        ProchaineEcheanceSensor(coordinator),
        DerniereInterventionSensor(coordinator),
        InterventionsAFaireSensor(coordinator),
    ]

    entites_existantes: set[str] = set()

    def _postes_suivis() -> list[str]:
        return [
            poste["id"]
            for poste in coordinator.data.get("echeances", [])
            if poste.get("intervalle_km") or poste.get("intervalle_mois")
        ]

    def _ajouter_postes(poste_ids: list[str]) -> None:
        """Crée les capteurs des postes ajoutés après l'installation."""
        nouveaux = [
            poste_id
            for poste_id in poste_ids
            if poste_id not in entites_existantes
            and coordinator.echeance(poste_id) is not None
        ]
        if not nouveaux:
            return
        entites_existantes.update(nouveaux)
        async_add_entities(
            [entite for poste_id in nouveaux for entite in _entites_poste(coordinator, poste_id)]
        )

    entites_existantes.update(_postes_suivis())
    entities.extend(
        entite
        for poste_id in entites_existantes
        for entite in _entites_poste(coordinator, poste_id)
    )
    async_add_entities(entities)
    coordinator.ajouter_entites_poste = _ajouter_postes


def _entites_poste(coordinator, poste_id: str) -> list[SensorEntity]:
    return [
        KmRestantsSensor(coordinator, poste_id),
        EtatPosteSensor(coordinator, poste_id),
        JoursRestantsSensor(coordinator, poste_id),
    ]


class _PosteEntity(CarnetEntity):
    """Base commune aux capteurs d'un poste d'entretien."""

    _suffixe = ""

    def __init__(self, coordinator, poste_id: str) -> None:
        super().__init__(coordinator)
        self.poste_id = poste_id
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{poste_id}"

    @property
    def echeance(self) -> dict:
        return self.coordinator.echeance(self.poste_id) or {}

    @property
    def nom_poste(self) -> str:
        return self.echeance.get("nom") or self.poste_id

    @property
    def name(self) -> str:
        """Suit le libellé du poste, y compris après un renommage."""
        return f"{self.nom_poste} {self._suffixe}".strip()

    def _attributs_communs(self) -> dict:
        data = self.echeance
        derniere = data.get("derniere") or {}
        prochain = derniere.get("prochain") or {}
        km_actuel = self.coordinator.km_actuel
        km_depuis = None
        if derniere.get("km") is not None and km_actuel is not None:
            km_depuis = int(km_actuel) - int(derniere.get("km"))
        return {
            "poste": self.poste_id,
            "etat": data.get("etat"),
            "prochain_km": data.get("prochain_km"),
            "prochain_date": data.get("prochain_date"),
            "km_restants": data.get("km_restants"),
            "jours_restants": data.get("jours_restants"),
            "km_depuis_derniere": km_depuis,
            "derniere_date": derniere.get("date"),
            "derniere_km": derniere.get("km"),
            "derniere_intervention": derniere.get("id"),
            "intervalle_km": data.get("intervalle_km"),
            "intervalle_mois": data.get("intervalle_mois"),
            "echeance_imposee": bool(
                prochain and derniere.get("prochain") is not None
            ),
        }


class KmActuelSensor(CarnetEntity, SensorEntity):
    """Kilométrage courant du véhicule."""

    _attr_unique_id = "km_actuel"
    _attr_name = "Kilométrage"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_km_actuel"

    @property
    def native_value(self):
        return self.coordinator.km_actuel

    @property
    def extra_state_attributes(self):
        vehicule = self.coordinator.data.get("vehicule", {})
        return {
            "km_maj": vehicule.get("km_maj"),
            "vin": vehicule.get("vin"),
            "moteur": vehicule.get("moteur"),
            "annee": vehicule.get("annee"),
            "immatriculation": vehicule.get("immatriculation"),
            "dossier": str(self.coordinator.storage.folder),
        }


class KmRestantsSensor(_PosteEntity, SensorEntity):
    """Kilomètres restants avant l'échéance d'un poste."""

    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    _suffixe = "km restants"

    def __init__(self, coordinator, poste_id: str) -> None:
        super().__init__(coordinator, poste_id)

    @property
    def native_value(self):
        return self.echeance.get("km_restants")

    @property
    def icon(self):
        return ICONES_ETAT.get(self.echeance.get("etat"), "mdi:road-variant")

    @property
    def extra_state_attributes(self):
        return self._attributs_communs()


class JoursRestantsSensor(_PosteEntity, SensorEntity):
    """Jours restants avant l'échéance (désactivé par défaut)."""

    _attr_entity_registry_enabled_default = False
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _suffixe = "jours restants"

    def __init__(self, coordinator, poste_id: str) -> None:
        super().__init__(coordinator, poste_id)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{poste_id}_jours"

    @property
    def native_value(self):
        return self.echeance.get("jours_restants")

    @property
    def icon(self):
        return ICONES_ETAT.get(self.echeance.get("etat"), "mdi:calendar-clock")

    @property
    def extra_state_attributes(self):
        return self._attributs_communs()


class EtatPosteSensor(_PosteEntity, SensorEntity):
    """État synthétique d'un poste : ok / à prévoir / dépassé / inconnu."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [ETA_OK, ETA_PREVOIR, ETA_DEPASSE, ETA_INCONNU]
    _attr_translation_key = "etat_poste"
    _suffixe = "état"

    def __init__(self, coordinator, poste_id: str) -> None:
        super().__init__(coordinator, poste_id)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{poste_id}_etat"

    @property
    def native_value(self):
        return self.echeance.get("etat") or ETA_INCONNU

    @property
    def icon(self):
        return ICONES_ETAT.get(self.echeance.get("etat"), "mdi:help-circle-outline")

    @property
    def extra_state_attributes(self):
        return self._attributs_communs()


class ProchaineEcheanceSensor(CarnetEntity, SensorEntity):
    """Poste le plus urgent, avec son échéance."""

    _attr_name = "Prochaine échéance"
    _attr_icon = "mdi:calendar-alert"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_prochaine_echeance"

    @property
    def native_value(self):
        alerte = self.coordinator.data.get("prochaine_alerte")
        return alerte.get("nom") if alerte else None

    @property
    def extra_state_attributes(self):
        alerte = self.coordinator.data.get("prochaine_alerte") or {}
        return {
            "poste": alerte.get("id"),
            "etat": alerte.get("etat"),
            "km_restants": alerte.get("km_restants"),
            "jours_restants": alerte.get("jours_restants"),
            "prochain_km": alerte.get("prochain_km"),
            "prochain_date": alerte.get("prochain_date"),
            "nb_alertes": sum(
                1
                for item in self.coordinator.data.get("echeances", [])
                if item.get("etat") in (ETA_DEPASSE, ETA_PREVOIR)
            ),
        }


class DerniereInterventionSensor(CarnetEntity, SensorEntity):
    """Date de la dernière intervention réalisée."""

    _attr_name = "Dernière intervention"
    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:wrench-clock"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_derniere_intervention"

    @property
    def _realisees(self) -> list[dict]:
        from .const import STATUT_FAIT

        return [
            item
            for item in self.coordinator.data.get("interventions") or []
            if str(item.get("statut") or STATUT_FAIT) == STATUT_FAIT
        ]

    @property
    def native_value(self):
        interventions = self._realisees
        from .calcul import parse_date

        return parse_date(interventions[0].get("date")) if interventions else None

    @property
    def extra_state_attributes(self):
        interventions = self._realisees
        if not interventions:
            return {"nombre_interventions": 0}
        derniere = interventions[0]
        return {
            "nombre_interventions": len(interventions),
            "intervention": derniere.get("nom"),
            "type": derniere.get("type"),
            "km": derniere.get("km"),
            "notes": derniere.get("notes"),
            "total_depense": self.coordinator.data.get("stats", {}).get("total"),
        }


class InterventionsAFaireSensor(CarnetEntity, SensorEntity):
    """Nombre d'interventions planifiées mais pas encore réalisées."""

    _attr_name = "À faire"
    _attr_icon = "mdi:clipboard-text-clock-outline"
    _attr_native_unit_of_measurement = "interventions"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_a_faire"

    @property
    def _a_faire(self) -> list[dict]:
        return self.coordinator.data.get("a_faire") or []

    @property
    def native_value(self) -> int:
        return len(self._a_faire)

    @property
    def extra_state_attributes(self) -> dict:
        items = self._a_faire
        prochaines = sorted(
            (item for item in items if item.get("date")),
            key=lambda item: str(item.get("date")),
        )
        return {
            "interventions": [item.get("nom") or item.get("type") for item in items],
            "identifiants": [item.get("id") for item in items],
            "prochaine_date": prochaines[0].get("date") if prochaines else None,
            "prochaine": (prochaines[0].get("nom") or prochaines[0].get("type"))
            if prochaines
            else None,
        }
