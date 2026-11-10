"""Coordinateur : source de vérité du carnet, chargée en mémoire."""

from __future__ import annotations

import csv
import io
import logging
from datetime import date
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .calcul import (
    compute_prochain,
    echeances,
    fusionner_parcours,
    parse_date,
    poste_by_id,
    poste_label,
    prochaine_alerte,
    statistiques,
)
from .const import (
    DOMAIN,
    EVENT_INTERVENTION,
    EVENT_KM,
    VERSION,
)
from .storage import CarnetStorage

_LOGGER = logging.getLogger(__name__)


class CarnetCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Charge, modifie et persiste le carnet d'entretien."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None)
        self.entry = entry
        self.storage = CarnetStorage(hass)
        self.profil: dict[str, Any] = {}
        self.interventions: list[dict] = []
        self.derniere_erreur: str | None = None

    # ---------------------------------------------------------------- init
    async def async_load(self) -> None:
        self.profil, self.interventions = await self.storage.async_load()
        self.data = self.snapshot()

    async def _async_update_data(self) -> dict[str, Any]:
        return self.snapshot()

    # ------------------------------------------------------------- lecture
    @property
    def vehicule(self) -> dict[str, Any]:
        return self.profil.setdefault("vehicule", {})

    @property
    def postes(self) -> list[dict]:
        return self.profil.setdefault("postes", [])

    @property
    def km_actuel(self) -> int | None:
        km = self.vehicule.get("km_actuel")
        try:
            return int(km) if km is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def today(self) -> date:
        return dt_util.now().date()

    def snapshot(self) -> dict[str, Any]:
        """État complet exposé aux entités, au panneau et aux services."""
        jour = self.today
        liste = echeances(self.postes, self.interventions, self.km_actuel, jour)
        return {
            "version": VERSION,
            "vehicule": dict(self.vehicule),
            "postes": [dict(poste) for poste in self.postes],
            "interventions": fusionner_parcours(self.interventions),
            "echeances": liste,
            "prochaine_alerte": prochaine_alerte(liste),
            "stats": statistiques(self.interventions, self.km_actuel),
            "today": jour.isoformat(),
        }

    def echeance(self, poste_id: str) -> dict[str, Any] | None:
        for item in self.data.get("echeances", []):
            if item["id"] == poste_id:
                return item
        return None

    # ------------------------------------------------------------ mutations
    def _new_id(self, date_str: str, poste_id: str) -> str:
        base = f"{date_str}-{poste_id}"
        existants = {item.get("id") for item in self.interventions}
        if base not in existants:
            return base
        index = 2
        while f"{base}-{index}" in existants:
            index += 1
        return f"{base}-{index}"

    def _normaliser_pieces(self, pieces: Any) -> list[dict]:
        if not pieces:
            return []
        if isinstance(pieces, dict):
            pieces = [pieces]
        resultat = []
        for item in pieces:
            if isinstance(item, str):
                resultat.append({"nom": item, "qte": None, "ref": None, "prix": None})
            elif isinstance(item, dict):
                resultat.append(
                    {
                        "nom": str(item.get("nom", "")).strip(),
                        "qte": item.get("qte"),
                        "ref": item.get("ref"),
                        "prix": self._normaliser_prix(item.get("prix")),
                    }
                )
        return [item for item in resultat if item["nom"]]

    @staticmethod
    def _normaliser_prix(prix: Any) -> float | None:
        """Prix unitaire d'une pièce, arrondi au centime."""
        if prix in (None, "", "None"):
            return None
        try:
            valeur = float(prix)
        except (TypeError, ValueError):
            return None
        return round(valeur, 2) if valeur >= 0 else None

    @classmethod
    def _total_pieces(cls, pieces: list[dict]) -> float | None:
        """Somme des prix unitaires × quantités des pièces chiffrées."""
        total = 0.0
        trouve = False
        for piece in pieces:
            prix = piece.get("prix")
            if prix is None:
                continue
            qte = piece.get("qte")
            quantite = 1.0
            if qte not in (None, ""):
                try:
                    quantite = float(qte)
                except (TypeError, ValueError):
                    quantite = 1.0
            total += float(prix) * quantite
            trouve = True
        return round(total, 2) if trouve else None

    def _normaliser_cout(self, cout: Any) -> float | None:
        if cout in (None, "", "None"):
            return None
        try:
            return round(float(cout), 2)
        except (TypeError, ValueError):
            return None

    async def async_enregistrer(self, data: dict[str, Any]) -> dict[str, Any]:
        poste_id = str(data.get("type", "")).strip()
        if not poste_id:
            raise ValueError("Le champ 'type' est obligatoire")
        jour = parse_date(data.get("date")) or self.today
        km = data.get("km")
        if km in (None, ""):
            km = self.km_actuel
        km = int(km) if km not in (None, "") else None

        poste = poste_by_id(self.postes, poste_id)
        nom = str(data.get("nom") or "").strip() or (poste or {}).get("nom") or poste_id
        prochain = compute_prochain(
            poste,
            jour,
            km,
            prochain_km=data.get("prochain_km"),
            prochain_date=data.get("prochain_date"),
        )

        pieces = self._normaliser_pieces(data.get("pieces"))
        cout = self._normaliser_cout(data.get("cout"))
        if cout is None:
            # Pas de coût global saisi : on retombe sur la somme des pièces.
            cout = self._total_pieces(pieces)

        intervention = {
            "id": self._new_id(jour.isoformat(), poste_id),
            "date": jour.isoformat(),
            "km": km,
            "type": poste_id,
            "nom": nom,
            "pieces": pieces,
            "cout": cout,
            "garage": str(data.get("garage") or "").strip() or None,
            "notes": str(data.get("notes") or "").strip() or None,
            "prochain": prochain,
            "cree": dt_util.utcnow().isoformat(),
        }
        self.interventions.append(intervention)

        # Le kilométrage connu suit l'intervention la plus haute.
        if km is not None and (self.km_actuel is None or km > self.km_actuel):
            self.vehicule["km_actuel"] = km
            self.vehicule["km_maj"] = jour.isoformat()

        await self._async_commit()
        self.hass.bus.async_fire(
            EVENT_INTERVENTION,
            {"action": "ajout", "intervention": intervention, "vehicule": dict(self.vehicule)},
        )
        return intervention

    async def async_modifier(self, intervention_id: str, data: dict[str, Any]) -> dict:
        cible = next(
            (item for item in self.interventions if item.get("id") == intervention_id),
            None,
        )
        if cible is None:
            raise ValueError(f"Intervention inconnue : {intervention_id}")

        for champ in ("garage", "notes"):
            if champ in data:
                cible[champ] = str(data.get(champ) or "").strip() or None
        if "cout" in data:
            cible["cout"] = self._normaliser_cout(data.get("cout"))
        if "pieces" in data:
            cible["pieces"] = self._normaliser_pieces(data.get("pieces"))
            if "cout" not in data:
                cible["cout"] = self._total_pieces(cible["pieces"])
        if data.get("date"):
            cible["date"] = (parse_date(data["date"]) or self.today).isoformat()
        if "km" in data:
            cible["km"] = int(data["km"]) if data.get("km") not in (None, "") else None
        if data.get("type"):
            cible["type"] = str(data["type"]).strip()
            cible["nom"] = poste_label(self.postes, cible["type"])
        if data.get("nom"):
            cible["nom"] = str(data["nom"]).strip()

        # Recalcul de l'échéance, sauf si l'utilisateur la fixe explicitement.
        if data.get("prochain_km") is not None or data.get("prochain_date"):
            cible["prochain"] = compute_prochain(
                poste_by_id(self.postes, cible["type"]),
                parse_date(cible.get("date")),
                cible.get("km"),
                prochain_km=data.get("prochain_km"),
                prochain_date=data.get("prochain_date"),
            )
        elif any(champ in data for champ in ("type", "date", "km")):
            cible["prochain"] = compute_prochain(
                poste_by_id(self.postes, cible["type"]),
                parse_date(cible.get("date")),
                cible.get("km"),
            )
        cible["modifie"] = dt_util.utcnow().isoformat()

        await self._async_commit()
        self.hass.bus.async_fire(
            EVENT_INTERVENTION,
            {"action": "modification", "intervention": cible, "vehicule": dict(self.vehicule)},
        )
        return cible

    async def async_supprimer(self, intervention_id: str) -> dict:
        cible = next(
            (item for item in self.interventions if item.get("id") == intervention_id),
            None,
        )
        if cible is None:
            raise ValueError(f"Intervention inconnue : {intervention_id}")
        self.interventions = [
            item for item in self.interventions if item.get("id") != intervention_id
        ]
        await self._async_commit()
        self.hass.bus.async_fire(
            EVENT_INTERVENTION, {"action": "suppression", "intervention": cible}
        )
        return cible

    async def async_maj_km(self, km: int, jour: Any = None) -> dict[str, Any]:
        valeur = int(km)
        self.vehicule["km_actuel"] = valeur
        self.vehicule["km_maj"] = (parse_date(jour) or self.today).isoformat()
        await self._async_commit()
        self.hass.bus.async_fire(
            EVENT_KM,
            {"km": valeur, "date": self.vehicule["km_maj"]},
        )
        return dict(self.vehicule)

    async def async_maj_profil(self, data: dict[str, Any]) -> dict[str, Any]:
        for cle in (
            "nom",
            "marque",
            "modele",
            "annee",
            "vin",
            "moteur",
            "immatriculation",
        ):
            if cle in data and data[cle] is not None:
                self.vehicule[cle] = data[cle]
        await self._async_commit()
        return dict(self.vehicule)

    async def async_definir_poste(self, data: dict[str, Any]) -> dict[str, Any]:
        poste_id = str(data.get("poste") or data.get("type") or "").strip()
        if not poste_id:
            raise ValueError("Le champ 'poste' est obligatoire")
        poste = poste_by_id(self.postes, poste_id)
        if poste is None:
            poste = {
                "id": poste_id,
                "nom": str(data.get("nom") or poste_id),
                "km": None,
                "mois": None,
                "icone": data.get("icone") or "mdi:wrench",
                "actif": True,
            }
            self.postes.append(poste)
        if "nom" in data and data["nom"]:
            poste["nom"] = str(data["nom"])
            # Un renommage suit aussi l'historique : sinon le journal garde
            # l'ancien libellé pour toutes les interventions déjà saisies.
            for intervention in self.interventions:
                if intervention.get("type") == poste_id:
                    intervention["nom"] = poste["nom"]
        for cle in ("km", "mois"):
            if cle in data:
                valeur = data.get(cle)
                poste[cle] = int(valeur) if valeur not in (None, "", 0, "0") else None
        if "icone" in data and data["icone"]:
            poste["icone"] = data["icone"]
        if "actif" in data:
            poste["actif"] = bool(data["actif"])
        await self._async_commit()
        self._synchroniser_postes()
        return dict(poste)

    def _synchroniser_postes(self) -> None:
        """Demande au capteur de créer les entités des postes nouvellement suivis."""
        callback = getattr(self, "ajouter_entites_poste", None)
        if callback is None:
            return
        suivis = [
            item["id"]
            for item in self.data.get("echeances", [])
            if item.get("intervalle_km") or item.get("intervalle_mois")
        ]
        callback(suivis)

    async def _async_commit(self) -> None:
        await self.storage.async_save_profil(self.profil)
        await self.storage.async_save_interventions(self.interventions)
        self.data = self.snapshot()
        self.async_set_updated_data(self.data)

    # --------------------------------------------------------------- export
    async def async_exporter(
        self, fmt: str = "csv", nom_fichier: str | None = None
    ) -> dict[str, Any]:
        fmt = (fmt or "csv").lower()
        stamp = self.today.isoformat()
        if fmt == "json":
            contenu = _dump_json(
                {
                    "schema": self.profil.get("schema", 1),
                    "exporte": dt_util.utcnow().isoformat(),
                    "profil": self.profil,
                    "interventions": fusionner_parcours(self.interventions),
                    "stats": statistiques(self.interventions, self.km_actuel),
                }
            )
            nom = nom_fichier or f"carnet-{stamp}.json"
        elif fmt == "csv":
            contenu = self._csv()
            nom = nom_fichier or f"interventions-{stamp}.csv"
        else:
            raise ValueError("Format d'export inconnu (csv ou json)")

        chemin = await self.storage.async_export(nom, contenu)
        _LOGGER.debug("Export %s écrit dans %s", fmt, chemin)
        return {
            "format": fmt,
            "chemin": chemin,
            "dossier": str(self.storage.exports_path),
            "nom_fichier": nom,
            "octets": len(contenu.encode("utf-8")),
        }

    def _csv(self) -> str:
        buffer = io.StringIO()
        buffer.write("\ufeff")  # BOM : ouverture correcte dans Excel FR
        writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
        writer.writerow(
            [
                "id",
                "date",
                "km",
                "type",
                "poste",
                "pièces",
                "coût pièces (€)",
                "coût (€)",
                "garage",
                "notes",
                "prochain km",
                "prochaine date",
            ]
        )
        for item in fusionner_parcours(self.interventions):
            pieces = " | ".join(
                _format_piece(piece) for piece in item.get("pieces") or []
            )
            prochain = item.get("prochain") or {}
            total_pieces = self._total_pieces(item.get("pieces") or [])
            writer.writerow(
                [
                    item.get("id", ""),
                    item.get("date", ""),
                    item.get("km", ""),
                    item.get("type", ""),
                    item.get("nom", ""),
                    pieces,
                    "" if total_pieces is None else f"{total_pieces:.2f}",
                    "" if item.get("cout") in (None, "") else f"{item['cout']:.2f}",
                    item.get("garage") or "",
                    item.get("notes") or "",
                    prochain.get("km", ""),
                    prochain.get("date", ""),
                ]
            )
        return buffer.getvalue()

    # -------------------------------------------------------------- charger
    @callback
    def async_recharger_depuis_disque(self) -> None:
        """Force une relecture (utile après édition manuelle du JSON)."""
        self.hass.async_create_task(self._async_reload_from_disk())

    async def async_reload_from_disk(self) -> None:
        """Relit les fichiers JSON (après édition manuelle)."""
        self.profil, self.interventions = await self.storage.async_load()
        self.data = self.snapshot()
        self.async_set_updated_data(self.data)

    # Alias interne conservé pour compatibilité ascendante.
    _async_reload_from_disk = async_reload_from_disk


def _format_piece(piece: dict) -> str:
    nom = piece.get("nom", "")
    qte = piece.get("qte")
    ref = piece.get("ref")
    prix = piece.get("prix")
    texte = nom
    if qte not in (None, ""):
        texte = f"{nom} x{qte}"
    if ref:
        texte = f"{texte} ({ref})"
    if prix is not None:
        texte = f"{texte} {prix:.2f} €/u"
    return texte


def _dump_json(payload: Any) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


__all__ = ["CarnetCoordinator"]
