"""Calculs purs : échéances, états, statistiques.

Aucune dépendance à Home Assistant ici, pour rester testable isolément.
"""

from __future__ import annotations

import calendar as _calendar
from datetime import date, datetime, timedelta
from typing import Any

from .const import (
    ETA_DEPASSE,
    ETA_INCONNU,
    ETA_OK,
    ETA_PREVOIR,
    SEUIL_JOURS,
    SEUIL_KM,
)

ISO = "%Y-%m-%d"


# --------------------------------------------------------------------------
# Dates
# --------------------------------------------------------------------------
def parse_date(value: Any) -> date | None:
    """Convertit une date ISO (ou datetime) en `date`, sinon None."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value)[:10], ISO).date()
    except (ValueError, TypeError):
        return None


def to_iso(value: date | datetime | str | None) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    parsed = parse_date(value)
    return parsed.isoformat() if parsed else None


def add_months(value: date, months: int) -> date:
    """Ajoute des mois en restant sur le même jour (borné en fin de mois)."""
    year = value.year + (value.month - 1 + months) // 12
    month = (value.month - 1 + months) % 12 + 1
    day = min(value.day, _calendar.monthrange(year, month)[1])
    return date(year, month, day)


def jours_restants(target: date | None, today: date) -> int | None:
    if target is None:
        return None
    return (target - today).days


# --------------------------------------------------------------------------
# Postes et échéances
# --------------------------------------------------------------------------
def poste_by_id(postes: list[dict], poste_id: str) -> dict | None:
    for poste in postes:
        if poste.get("id") == poste_id:
            return poste
    return None


def poste_label(postes: list[dict], poste_id: str) -> str:
    poste = poste_by_id(postes, poste_id)
    return poste["nom"] if poste else poste_id


def compute_prochain(
    poste: dict | None,
    date_ref: date | None,
    km_ref: int | None,
    *,
    prochain_km: int | None = None,
    prochain_date: date | str | None = None,
) -> dict | None:
    """Calcule l'échéance suivante à partir des intervalles du poste.

    Les valeurs explicites (`prochain_km`, `prochain_date`) ont priorité.
    """
    resultat: dict[str, Any] = {}
    intervalle_km = poste.get("km") if poste else None
    intervalle_mois = poste.get("mois") if poste else None

    if prochain_km is not None:
        resultat["km"] = int(prochain_km)
    elif intervalle_km and km_ref is not None:
        resultat["km"] = int(km_ref) + int(intervalle_km)

    date_explicite = parse_date(prochain_date) if prochain_date else None
    if date_explicite:
        resultat["date"] = date_explicite.isoformat()
    elif intervalle_mois and date_ref is not None:
        resultat["date"] = add_months(date_ref, int(intervalle_mois)).isoformat()

    return resultat or None


def derniere_intervention(
    interventions: list[dict], poste_id: str
) -> dict | None:
    """Dernière intervention enregistrée pour un poste (date puis km)."""
    candidates = [item for item in interventions if item.get("type") == poste_id]
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (
            parse_date(item.get("date")) or date.min,
            int(item.get("km") or 0),
        )
    )
    return candidates[-1]


def echeance_poste(
    poste: dict,
    interventions: list[dict],
    km_actuel: int | None,
    today: date,
) -> dict[str, Any]:
    """État complet d'un poste : prochaine échéance et alertes."""
    derniere = derniere_intervention(interventions, poste["id"])
    prochain = (derniere or {}).get("prochain")
    if not prochain:
        # Repli : échéance recalculée si le journal a été édité à la main.
        prochain = compute_prochain(
            poste,
            parse_date((derniere or {}).get("date")),
            (derniere or {}).get("km"),
        )

    km_cible = None
    date_cible = None
    if prochain:
        km_cible = prochain.get("km")
        date_cible = parse_date(prochain.get("date"))

    km_restants = None
    if km_cible is not None and km_actuel is not None:
        km_restants = int(km_cible) - int(km_actuel)

    jours = jours_restants(date_cible, today)

    if derniere is None:
        etat = ETA_INCONNU
    elif (km_restants is not None and km_restants <= 0) or (
        jours is not None and jours < 0
    ):
        etat = ETA_DEPASSE
    elif (km_restants is not None and km_restants <= SEUIL_KM) or (
        jours is not None and jours <= SEUIL_JOURS
    ):
        etat = ETA_PREVOIR
    elif km_restants is None and jours is None:
        etat = ETA_INCONNU
    else:
        etat = ETA_OK

    return {
        "id": poste["id"],
        "nom": poste.get("nom", poste["id"]),
        "icone": poste.get("icone"),
        "actif": bool(poste.get("actif", True)),
        "intervalle_km": poste.get("km"),
        "intervalle_mois": poste.get("mois"),
        "derniere": derniere,
        "prochain_km": km_cible,
        "prochain_date": date_cible.isoformat() if date_cible else None,
        "km_restants": km_restants,
        "jours_restants": jours,
        "etat": etat,
    }


def echeances(
    postes: list[dict],
    interventions: list[dict],
    km_actuel: int | None,
    today: date,
) -> list[dict]:
    """Échéances de tous les postes suivis, triées par urgence."""
    items = [
        echeance_poste(poste, interventions, km_actuel, today)
        for poste in postes
        if poste.get("actif", True)
    ]
    items.sort(key=lambda item: _gravite(item))
    for index, item in enumerate(items):
        item["urgence"] = index
    return items


def _gravite(item: dict) -> tuple:
    """Clé de tri : dépassé d'abord, puis le plus proche."""
    rang = {
        ETA_DEPASSE: 0,
        ETA_PREVOIR: 1,
        ETA_OK: 2,
        ETA_INCONNU: 3,
    }.get(item.get("etat"), 4)
    km = item.get("km_restants")
    jours = item.get("jours_restants")
    return (rang, km if km is not None else 10**9, jours if jours is not None else 10**9)


# --------------------------------------------------------------------------
# Statistiques
# --------------------------------------------------------------------------
def statistiques(interventions: list[dict], km_actuel: int | None) -> dict[str, Any]:
    """Totaux par année et par poste, coût moyen au km."""
    total = 0.0
    sans_cout = 0
    par_annee: dict[str, float] = {}
    par_type: dict[str, dict[str, Any]] = {}

    for item in interventions:
        cout = item.get("cout")
        if cout in (None, ""):
            sans_cout += 1
        else:
            try:
                montant = float(cout)
            except (TypeError, ValueError):
                sans_cout += 1
                montant = None
            if montant is not None:
                total += montant
                annee = str(item.get("date", ""))[:4] or "inconnue"
                par_annee[annee] = round(par_annee.get(annee, 0.0) + montant, 2)

        type_id = item.get("type") or "autre"
        entree = par_type.setdefault(type_id, {"count": 0, "total": 0.0})
        entree["count"] += 1
        if item.get("cout") not in (None, ""):
            try:
                entree["total"] = round(entree["total"] + float(item["cout"]), 2)
            except (TypeError, ValueError):
                pass

    km_couverts = None
    dates = [parse_date(item.get("date")) for item in interventions]
    dates = [d for d in dates if d]
    kms = [int(item["km"]) for item in interventions if item.get("km") is not None]
    if kms and km_actuel is not None:
        km_couverts = max(km_actuel - min(kms), 0) or None

    return {
        "total": round(total, 2),
        "sans_cout": sans_cout,
        "par_annee": dict(sorted(par_annee.items())),
        "par_type": dict(sorted(par_type.items())),
        "cout_par_km": round(total / km_couverts, 4) if km_couverts else None,
        "km_couverts": km_couverts,
        "premiere_date": min(dates).isoformat() if dates else None,
        "derniere_date": max(dates).isoformat() if dates else None,
    }


def prochaine_alerte(echeances_liste: list[dict]) -> dict | None:
    """Échéance la plus urgente (utile pour le capteur global)."""
    for item in echeances_liste:
        if item.get("etat") in (ETA_DEPASSE, ETA_PREVOIR):
            return item
    return echeances_liste[0] if echeances_liste else None


def fusionner_parcours(interventions: list[dict]) -> list[dict]:
    """Journal trié du plus récent au plus ancien."""
    def _cle(item: dict):
        return (
            parse_date(item.get("date")) or date.min,
            int(item.get("km") or 0),
        )

    return sorted(interventions, key=_cle, reverse=True)


def jours_depuis(value: str | None, today: date) -> int | None:
    parsed = parse_date(value)
    if parsed is None:
        return None
    return (today - parsed).days


def dans_n_jours(n: int, today: date) -> str:
    return (today + timedelta(days=n)).isoformat()
