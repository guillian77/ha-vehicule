"""Capteur binaire de contrôle de l'intégrité du carnet et de sa sauvegarde."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta

from .entity import CarnetEntity

SCAN_INTERVAL = timedelta(hours=6)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    entity = IntegriteCarnetSensor(coordinator)
    async_add_entities([entity])

    async def _refresh(_now=None) -> None:
        await entity.async_update()
        entity.async_write_ha_state()

    entry.async_on_unload(async_track_time_interval(hass, _refresh, SCAN_INTERVAL))


class IntegriteCarnetSensor(CarnetEntity, BinarySensorEntity):
    """ON = problème détecté sur les fichiers du carnet.

    Le carnet vit dans `/config/vehicule`, donc il est emporté par les
    sauvegardes Home Assistant (complètes et « dossier de configuration »).
    Ce capteur vérifie que les fichiers sont bien présents et lisibles.
    """

    _attr_name = "Intégrité du carnet"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:file-check"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_integrite"
        self._etat: dict = {"ok": True, "erreurs": []}

    @property
    def is_on(self) -> bool:
        return not self._etat.get("ok", True)

    @property
    def icon(self) -> str:
        return "mdi:file-alert" if self.is_on else "mdi:file-check"

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "dossier": self._etat.get("dossier"),
            "profil": self._etat.get("profil"),
            "interventions": self._etat.get("interventions"),
            "erreurs": self._etat.get("erreurs", []),
            "sauvegarde": "incluse dans /config",
        }

    async def async_update(self) -> None:
        self._etat = await self.coordinator.storage.async_check()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        await self.async_update()
