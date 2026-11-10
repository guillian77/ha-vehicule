"""Tests d'intégration : entités, services, calendrier, persistance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from homeassistant.exceptions import ServiceValidationError

from custom_components.vehicule.const import DOMAIN


def _entites(hass, suffixe: str, domaine: str = "sensor"):
    return [
        etat
        for etat in hass.states.async_all(domaine)
        if etat.entity_id.endswith(suffixe)
    ]


def _sensor_poste(hass, poste: str, fin: str):
    for etat in hass.states.async_all("sensor"):
        if etat.attributes.get("poste") == poste and etat.entity_id.endswith(fin):
            return etat
    return None


async def test_setup_cree_les_entites(entry, hass):
    assert entry.state.name == "LOADED"
    assert entry.runtime_data is not None

    km_sensor = _entites(hass, "_kilometrage")
    assert len(km_sensor) == 1
    assert km_sensor[0].state == "129277"

    etats = [e for e in hass.states.async_all("sensor") if e.entity_id.endswith("_etat")]
    assert len(etats) >= 10
    # Aucune intervention : tout est « inconnu ».
    assert {e.state for e in etats} == {"inconnu"}

    integrite = _entites(hass, "_integrite_du_carnet", "binary_sensor")
    assert len(integrite) == 1
    assert integrite[0].state == "off"

    calendriers = hass.states.async_all("calendar")
    assert len(calendriers) == 1


async def test_vehicule_identite_reprise_depuis_config_entry(entry, coordinator):
    vehicule = coordinator.vehicule
    assert vehicule["nom"] == "BMW 325i E90"
    assert vehicule["vin"] == "0NA4336"
    assert vehicule["moteur"] == "N52B25"
    assert vehicule["annee"] == 2006


async def test_enregistrer_intervention_calcule_echeance(entry, hass):
    await hass.services.async_call(
        DOMAIN,
        "enregistrer_intervention",
        {
            "type": "vidange",
            "date": "2026-11-07",
            "km": 129277,
            "cout": 68.4,
            "pieces": [{"nom": "Huile LL-01 5W-30", "qte": 6.5, "ref": "83212390556"}],
            "garage": "fait maison",
            "notes": "filtre changé",
        },
        blocking=True,
    )

    etat = _sensor_poste(hass, "vidange", "_etat")
    assert etat is not None
    assert etat.state == "ok"

    restants = _sensor_poste(hass, "vidange", "_km_restants")
    assert restants.state == "15000"
    assert restants.attributes["prochain_km"] == 144277
    assert restants.attributes["prochain_date"] == "2027-11-07"
    assert restants.attributes["derniere_km"] == 129277

    # Le journal est écrit sur disque.
    journal = json.loads(
        (Path(hass.config.path("vehicule")) / "interventions.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(journal["interventions"]) == 1
    assert journal["interventions"][0]["pieces"][0]["nom"] == "Huile LL-01 5W-30"


async def test_echeance_sans_intervalle_na_pas_de_capteur(entry, hass):
    assert _sensor_poste(hass, "pneus", "_etat") is None


async def test_maj_km_passe_en_a_prevoir_puis_depasse(entry, hass):
    await hass.services.async_call(
        DOMAIN,
        "enregistrer_intervention",
        {"type": "vidange", "date": "2026-11-07", "km": 129277},
        blocking=True,
    )

    await hass.services.async_call(DOMAIN, "maj_km", {"km": 143000}, blocking=True)
    await hass.async_block_till_done()
    assert _sensor_poste(hass, "vidange", "_etat").state == "a_prevoir"

    await hass.services.async_call(DOMAIN, "maj_km", {"km": 145000}, blocking=True)
    await hass.async_block_till_done()
    assert _sensor_poste(hass, "vidange", "_etat").state == "depasse"
    assert _sensor_poste(hass, "vidange", "_km_restants").state == "-723"


async def test_modifier_et_supprimer(entry, hass, coordinator):
    resultat = await coordinator.async_enregistrer(
        {"type": "vidange", "date": "2026-11-07", "km": 129277, "cout": 50}
    )
    identifiant = resultat["id"]

    await hass.services.async_call(
        DOMAIN,
        "modifier_intervention",
        {"id": identifiant, "cout": 75.5, "notes": "corrigé"},
        blocking=True,
    )
    await hass.async_block_till_done()
    modifiee = next(i for i in coordinator.interventions if i["id"] == identifiant)
    assert modifiee["cout"] == 75.5
    assert modifiee["notes"] == "corrigé"

    await hass.services.async_call(
        DOMAIN, "supprimer_intervention", {"id": identifiant}, blocking=True
    )
    await hass.async_block_till_done()
    assert coordinator.interventions == []


async def test_supprimer_inconnu_leve_une_erreur(entry, hass):
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "supprimer_intervention", {"id": "nope"}, blocking=True
        )


async def test_type_obligatoire(entry, hass):
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "enregistrer_intervention", {"type": ""}, blocking=True
        )


async def test_export_csv_et_json(entry, hass, coordinator):
    await coordinator.async_enregistrer(
        {
            "type": "vidange",
            "date": "2026-11-07",
            "km": 129277,
            "cout": 68.4,
            "pieces": [{"nom": "Huile 5W-30", "qte": 6.5}],
        }
    )

    reponse = await hass.services.async_call(
        DOMAIN, "exporter", {"format": "csv"}, blocking=True, return_response=True
    )
    assert reponse["format"] == "csv"
    contenu = open(reponse["chemin"], encoding="utf-8").read()
    assert contenu.startswith("\ufeff")
    assert "129277" in contenu
    assert "Huile 5W-30 x6.5" in contenu

    reponse = await hass.services.async_call(
        DOMAIN, "exporter", {"format": "json"}, blocking=True, return_response=True
    )
    charge = json.load(open(reponse["chemin"], encoding="utf-8"))
    assert charge["interventions"][0]["type"] == "vidange"
    assert charge["profil"]["vehicule"]["nom"] == "BMW 325i E90"


async def test_calendrier_expose_les_echeances(entry, hass):
    await hass.services.async_call(
        DOMAIN,
        "enregistrer_intervention",
        {"type": "vidange", "date": "2026-11-07", "km": 129277},
        blocking=True,
    )
    await hass.async_block_till_done()

    calendrier = hass.states.async_all("calendar")[0]
    debut = hass.states.get(calendrier.entity_id)
    assert debut.attributes["friendly_name"]

    from datetime import datetime, timezone

    from homeassistant.components.calendar import DOMAIN as CALENDAR_DOMAIN

    evenements = await hass.services.async_call(
        CALENDAR_DOMAIN,
        "get_events",
        {
            "entity_id": calendrier.entity_id,
            "start_date_time": datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat(),
            "end_date_time": datetime(2028, 1, 1, tzinfo=timezone.utc).isoformat(),
        },
        blocking=True,
        return_response=True,
    )
    liste = evenements[calendrier.entity_id]["events"]
    assert any("Vidange" in evenement["summary"] for evenement in liste)


async def test_intervention_libre_hors_postes_suivis(entry, hass, coordinator):
    """Une intervention hors postes suivis garde son libellé, sans capteur."""
    await hass.services.async_call(
        DOMAIN,
        "enregistrer_intervention",
        {
            "type": "tresse_de_masse",
            "nom": "Tresse de masse anti-parasite",
            "date": "2026-11-09",
            "km": 129300,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    intervention = coordinator.interventions[-1]
    assert intervention["type"] == "tresse_de_masse"
    assert intervention["nom"] == "Tresse de masse anti-parasite"
    assert intervention["prochain"] is None
    # Aucun poste suivi n'est créé au passage.
    assert all(p["id"] != "tresse_de_masse" for p in coordinator.postes)
    assert not any("tresse" in etat.entity_id for etat in hass.states.async_all("sensor"))


async def test_poste_personnalise_cree_capteurs(entry, hass, coordinator):
    """Un poste créé depuis les réglages obtient ses capteurs sans redémarrage."""
    await hass.services.async_call(
        DOMAIN,
        "definir_poste",
        {
            "poste": "recherche_panne_bst",
            "nom": "Recherche de panne BST",
            "km": 30000,
            "mois": 24,
            "icone": "mdi:magnify-scan",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    poste = next(p for p in coordinator.postes if p["id"] == "recherche_panne_bst")
    assert poste["nom"] == "Recherche de panne BST"
    assert poste["km"] == 30000

    capteurs = [
        etat
        for etat in hass.states.async_all("sensor")
        if (etat.attributes.get("poste") == "recherche_panne_bst")
    ]
    assert capteurs, "les capteurs du poste personnalisé doivent être créés"
    assert any(etat.entity_id.endswith("_etat") for etat in capteurs)


async def test_definir_poste_et_maj_vehicule(entry, hass, coordinator):
    await hass.services.async_call(
        DOMAIN,
        "definir_poste",
        {"poste": "vidange", "km": 20000, "mois": 18},
        blocking=True,
    )
    await hass.async_block_till_done()
    poste = next(p for p in coordinator.postes if p["id"] == "vidange")
    assert poste["km"] == 20000
    assert poste["mois"] == 18

    await hass.services.async_call(
        DOMAIN, "maj_vehicule", {"immatriculation": "AB-123-CD"}, blocking=True
    )
    await hass.async_block_till_done()
    assert coordinator.vehicule["immatriculation"] == "AB-123-CD"


async def test_persistance_apres_rechargement(hass, entry):
    await hass.services.async_call(
        DOMAIN,
        "enregistrer_intervention",
        {"type": "bougies", "date": "2026-10-01", "km": 128000},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = entry.runtime_data
    assert len(coordinator.interventions) == 1
    assert coordinator.interventions[0]["type"] == "bougies"
