"""Tests du stockage JSON (atomicité, quarantaine, export)."""

from __future__ import annotations

import json

from custom_components.vehicule.storage import CarnetStorage


async def test_creation_automatique_des_fichiers(hass):
    store = CarnetStorage(hass)
    profil, interventions = await store.async_load()

    assert store.profil_path.exists()
    assert store.interventions_path.exists()
    assert store.exports_path.is_dir()
    assert profil["vehicule"]["nom"] == ""
    assert interventions == []
    assert len(profil["postes"]) >= 10

    # Le dossier est bien sous /config : il suit les sauvegardes HA.
    assert str(store.folder) == hass.config.path("vehicule")


async def test_ecriture_atomique_et_copie_de_securite(hass):
    store = CarnetStorage(hass)
    profil, interventions = await store.async_load()

    profil["vehicule"]["km_actuel"] = 130000
    await store.async_save_profil(profil)

    sauvegarde = store.profil_path.with_suffix(".json.bak")
    assert sauvegarde.exists()

    await store.async_save_profil(profil)
    relu = json.loads(store.profil_path.read_text(encoding="utf-8"))
    assert relu["vehicule"]["km_actuel"] == 130000


async def test_fichier_corrompu_mis_en_quarantaine(hass):
    store = CarnetStorage(hass)
    await store.async_load()

    store.interventions_path.write_text("{pas du json", encoding="utf-8")
    interventions = await store._hass.async_add_executor_job(store._load_interventions)

    assert interventions == []
    quarantaines = list(store.folder.glob("interventions.json.corrompu-*"))
    assert len(quarantaines) == 1
    assert json.loads(store.interventions_path.read_text(encoding="utf-8")) == {
        "schema": 1,
        "interventions": [],
    }


async def test_export_ecrit_le_fichier(hass):
    store = CarnetStorage(hass)
    await store.async_load()

    chemin = await store.async_export("essai.csv", "date;km\n2026-11-07;129277\n")
    assert chemin.endswith("essai.csv")
    assert "129277" in (store.exports_path / "essai.csv").read_text(encoding="utf-8")


async def test_export_nom_fichier_assaini(hass):
    store = CarnetStorage(hass)
    await store.async_load()

    chemin = await store.async_export("../../etc/passwd", "x")
    assert "/etc/" not in chemin
    assert "etcpasswd" in chemin


async def test_controle_integrite(hass):
    store = CarnetStorage(hass)
    await store.async_load()
    etat = await store.async_check()
    assert etat["ok"] is True
    assert etat["erreurs"] == []

    store.profil_path.unlink()
    etat = await store.async_check()
    assert etat["ok"] is False
    assert any("profil" in err for err in etat["erreurs"])
