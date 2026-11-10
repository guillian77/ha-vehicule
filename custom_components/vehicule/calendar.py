"""Calendrier des échéances d'entretien."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .calcul import parse_date
from .const import ETA_DEPASSE, ETA_INCONNU, ETA_OK, ETA_PREVOIR
from .entity import CarnetEntity

_LOGGER = logging.getLogger(__name__)

LIBELLES_ETAT = {
    ETA_DEPASSE: "à faire depuis",
    ETA_PREVOIR: "à prévoir",
    ETA_OK: "prévu",
    ETA_INCONNU: "inconnu",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([VehiculeCalendar(entry.runtime_data)])


class VehiculeCalendar(CarnetEntity, CalendarEntity):
    """Échéances datées du carnet (une par poste)."""

    _attr_name = "Échéances d'entretien"
    _attr_icon = "mdi:car-wrench"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_echeances"

    # ------------------------------------------------------------ interne
    def _events(self) -> list[tuple[date, CalendarEvent]]:
        resultat: list[tuple[date, CalendarEvent]] = []
        for item in self.coordinator.data.get("echeances", []):
            jour = parse_date(item.get("prochain_date"))
            if jour is None:
                continue
            libelle = LIBELLES_ETAT.get(item.get("etat"), "")
            details = [f"État : {item.get('etat')}"]
            if item.get("prochain_km") is not None:
                details.append(f"Échéance à {item['prochain_km']} km")
            if item.get("km_restants") is not None:
                details.append(f"{item['km_restants']} km restants")
            if item.get("derniere"):
                derniere = item["derniere"]
                details.append(
                    f"Dernière intervention : {derniere.get('date')} "
                    f"à {derniere.get('km')} km"
                )
            resultat.append(
                (
                    jour,
                    CalendarEvent(
                        start=jour,
                        end=jour + timedelta(days=1),
                        summary=f"{item['nom']} ({libelle})",
                        description=" · ".join(details),
                    ),
                )
            )
        resultat.sort(key=lambda paire: paire[0])
        return resultat

    # --------------------------------------------------------------- API
    @property
    def event(self) -> CalendarEvent | None:
        today = dt_util.now().date()
        evenements = self._events()
        for _, event in evenements:
            fin = event.end
            if isinstance(fin, datetime):
                fin = fin.date()
            if fin > today:
                return event
        return evenements[-1][1] if evenements else None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        debut = start_date.date() if isinstance(start_date, datetime) else start_date
        fin = end_date.date() if isinstance(end_date, datetime) else end_date
        resultat = []
        for jour, event in self._events():
            if debut <= jour <= fin:
                resultat.append(event)
        return resultat
