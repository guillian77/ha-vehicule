"""Entités de base du carnet d'entretien."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, VERSION
from .coordinator import CarnetCoordinator


class CarnetEntity(CoordinatorEntity[CarnetCoordinator]):
    """Entité rattachée au véhicule."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CarnetCoordinator) -> None:
        super().__init__(coordinator)
        self.entry = coordinator.entry

    @property
    def device_info(self) -> DeviceInfo:
        vehicule = self.coordinator.data.get("vehicule", {})
        modele = " ".join(
            part for part in (vehicule.get("marque"), vehicule.get("modele")) if part
        )
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=vehicule.get("nom") or "Véhicule",
            manufacturer=vehicule.get("marque") or None,
            model=modele or vehicule.get("moteur") or None,
            serial_number=vehicule.get("vin") or None,
            sw_version=VERSION,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and bool(self.coordinator.data)
