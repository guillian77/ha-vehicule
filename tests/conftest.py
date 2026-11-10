"""Fixtures partagées pour les tests du carnet véhicule."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from custom_components.vehicule.const import DOMAIN

DATA_BASE = {
    "nom": "BMW 325i E90",
    "marque": "BMW",
    "modele": "325i E90",
    "annee": 2006,
    "vin": "0NA4336",
    "moteur": "N52B25",
    "immatriculation": "",
    "km_actuel": 129277,
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Charge custom_components/vehicule."""
    yield


@pytest.fixture(autouse=True)
async def carnet_isole(hass):
    """Isole les fichiers du carnet entre les tests (config partagée)."""
    dossier = Path(hass.config.path(DOMAIN))
    shutil.rmtree(dossier, ignore_errors=True)
    yield
    shutil.rmtree(dossier, ignore_errors=True)


@pytest.fixture
async def entry(hass):
    """Crée et charge la config entry du véhicule."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(domain=DOMAIN, data=dict(DATA_BASE), title="BMW 325i E90")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    yield entry
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


@pytest.fixture
def coordinator(entry):
    return entry.runtime_data
