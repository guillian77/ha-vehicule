"""Tests des calculs purs (sans Home Assistant)."""

from __future__ import annotations

from datetime import date

from custom_components.vehicule.calcul import (
    add_months,
    compute_prochain,
    echeance_poste,
    echeances,
    parse_date,
    prochaine_alerte,
    statistiques,
)

POSTE = {"id": "vidange", "nom": "Vidange moteur", "km": 15000, "mois": 12, "actif": True}


def test_add_months_borne_fin_de_mois():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2026, 11, 7), 12) == date(2027, 11, 7)
    assert add_months(date(2026, 12, 15), 1) == date(2027, 1, 15)


def test_parse_date():
    assert parse_date("2026-11-07") == date(2026, 11, 7)
    assert parse_date("") is None
    assert parse_date("bidon") is None


def test_compute_prochain_km_et_date():
    prochain = compute_prochain(POSTE, date(2026, 11, 7), 129277)
    assert prochain == {"km": 144277, "date": "2027-11-07"}


def test_compute_prochain_valeurs_imposees():
    prochain = compute_prochain(
        POSTE,
        date(2026, 11, 7),
        129277,
        prochain_km=150000,
        prochain_date="2027-06-01",
    )
    assert prochain == {"km": 150000, "date": "2027-06-01"}


def test_compute_prochain_poste_sans_intervalle():
    assert compute_prochain({"id": "pneus"}, date(2026, 11, 7), 129277) is None


def test_echeance_sans_historique():
    resultat = echeance_poste(POSTE, [], 129277, date(2026, 11, 10))
    assert resultat["etat"] == "inconnu"
    assert resultat["derniere"] is None
    assert resultat["km_restants"] is None


def test_echeance_ok_puis_a_prevoir_puis_depasse():
    intervention = {
        "id": "2026-11-07-vidange",
        "date": "2026-11-07",
        "km": 129277,
        "type": "vidange",
        "prochain": {"km": 144277, "date": "2027-11-07"},
    }

    etat = lambda km: echeance_poste(  # noqa: E731
        POSTE, [intervention], km, date(2026, 11, 10)
    )["etat"]

    assert etat(129277) == "ok"
    assert etat(140000) == "ok"  # 4 277 km restants
    assert etat(142500) == "a_prevoir"  # 1 777 km restants < seuil 2 000
    assert etat(145000) == "depasse"


def test_echeance_date_depassee():
    intervention = {
        "id": "x",
        "date": "2025-01-01",
        "km": 100000,
        "type": "vidange",
        "prochain": {"km": 115000, "date": "2026-01-01"},
    }
    resultat = echeance_poste(POSTE, [intervention], 101000, date(2026, 11, 10))
    assert resultat["etat"] == "depasse"
    assert resultat["jours_restants"] < 0


def test_echeance_recalculee_si_prochain_absent():
    intervention = {
        "id": "x",
        "date": "2026-11-07",
        "km": 129277,
        "type": "vidange",
    }
    resultat = echeance_poste(POSTE, [intervention], 129277, date(2026, 11, 10))
    assert resultat["prochain_km"] == 144277
    assert resultat["prochain_date"] == "2027-11-07"


def test_tri_des_echeances():
    postes = [
        {"id": "vidange", "nom": "Vidange", "km": 15000, "mois": 12},
        {"id": "bougies", "nom": "Bougies", "km": 100000, "mois": 120},
    ]
    interventions = [
        {"id": "a", "date": "2025-01-01", "km": 20000, "type": "vidange",
         "prochain": {"km": 35000, "date": "2026-01-01"}},
        {"id": "b", "date": "2026-11-01", "km": 129000, "type": "bougies",
         "prochain": {"km": 229000, "date": "2036-11-01"}},
    ]
    liste = echeances(postes, interventions, 129277, date(2026, 11, 10))
    assert [item["id"] for item in liste] == ["vidange", "bougies"]
    assert liste[0]["etat"] == "depasse"


def test_prochaine_alerte():
    postes = [{"id": "a", "nom": "A", "km": 1000, "mois": None}]
    interventions = [
        {"id": "1", "date": "2026-01-01", "km": 1000, "type": "a",
         "prochain": {"km": 2000}},
    ]
    liste = echeances(postes, interventions, 2500, date(2026, 11, 10))
    alerte = prochaine_alerte(liste)
    assert alerte["id"] == "a"


def test_statistiques():
    interventions = [
        {"id": "1", "date": "2025-05-01", "km": 120000, "type": "vidange", "cout": 80.0},
        {"id": "2", "date": "2026-11-07", "km": 129277, "type": "vidange", "cout": "68.40"},
        {"id": "3", "date": "2026-06-15", "km": 125000, "type": "plaquettes_avant"},
    ]
    stats = statistiques(interventions, 129300)
    assert stats["total"] == 148.4
    assert stats["sans_cout"] == 1
    assert stats["par_annee"] == {"2025": 80.0, "2026": 68.4}
    assert stats["par_type"]["vidange"]["count"] == 2
    assert stats["par_type"]["vidange"]["total"] == 148.4
    assert stats["km_couverts"] == 9300
    assert round(stats["cout_par_km"], 4) == round(148.4 / 9300, 4)
