"""Tests de l'API websocket utilisée par le panneau."""

from __future__ import annotations


async def test_ws_data_renvoie_letat_complet(hass, entry, hass_ws_client):
    client = await hass_ws_client(hass)
    await client.send_json({"id": 10, "type": "vehicule/data"})
    reponse = await client.receive_json()

    assert reponse["success"] is True
    resultat = reponse["result"]
    assert resultat["vehicule"]["nom"] == "BMW 325i E90"
    assert resultat["vehicule"]["km_actuel"] == 129277
    assert isinstance(resultat["echeances"], list)
    assert len(resultat["echeances"]) >= 10
    assert resultat["dossier"].endswith("/vehicule")
    assert resultat["exports"].endswith("/vehicule/exports")
    assert "stats" in resultat


async def test_ws_data_reflete_les_services(hass, entry, hass_ws_client):
    from custom_components.vehicule.const import DOMAIN

    await hass.services.async_call(
        DOMAIN,
        "enregistrer_intervention",
        {"type": "vidange", "date": "2026-11-07", "km": 129277, "cout": 60},
        blocking=True,
    )
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json({"id": 11, "type": "vehicule/data"})
    resultat = (await client.receive_json())["result"]

    assert len(resultat["interventions"]) == 1
    assert resultat["stats"]["total"] == 60
    vidange = next(e for e in resultat["echeances"] if e["id"] == "vidange")
    assert vidange["km_restants"] == 15000


async def test_ws_reload_relit_le_disque(hass, entry, hass_ws_client):
    import json
    from pathlib import Path

    chemin = Path(hass.config.path("vehicule")) / "interventions.json"
    charge = json.loads(chemin.read_text(encoding="utf-8"))
    charge["interventions"].append(
        {
            "id": "manuel-1",
            "date": "2026-01-15",
            "km": 125000,
            "type": "vidange",
            "nom": "Vidange moteur",
            "pieces": [],
            "cout": None,
            "garage": None,
            "notes": "ajout à la main",
            "prochain": {"km": 140000, "date": "2027-01-15"},
        }
    )
    chemin.write_text(json.dumps(charge), encoding="utf-8")

    client = await hass_ws_client(hass)
    await client.send_json({"id": 12, "type": "vehicule/reload"})
    reponse = await client.receive_json()
    assert reponse["success"] is True

    await client.send_json({"id": 13, "type": "vehicule/data"})
    resultat = (await client.receive_json())["result"]
    assert resultat["interventions"][0]["id"] == "manuel-1"
