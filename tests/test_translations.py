"""Vérifie que les traductions couvrent bien les clés de strings.json."""

from __future__ import annotations

import json
from pathlib import Path

DOSSIER = Path(__file__).parent.parent / "custom_components" / "vehicule"


def _clés(donnees, prefixe=""):
    sortie = set()
    if isinstance(donnees, dict):
        for cle, valeur in donnees.items():
            chemin = f"{prefixe}.{cle}" if prefixe else cle
            if isinstance(valeur, (dict, list)):
                sortie |= _clés(valeur, chemin)
            else:
                sortie.add(chemin)
    return sortie


def test_traductions_alignees_sur_strings():
    base = _clés(json.loads((DOSSIER / "strings.json").read_text(encoding="utf-8")))
    for langue in ("fr", "en"):
        fichier = DOSSIER / "translations" / f"{langue}.json"
        traductions = _clés(json.loads(fichier.read_text(encoding="utf-8")))
        manquantes = base - traductions
        assert not manquantes, f"{langue}.json incomplet : {sorted(manquantes)}"


def test_services_declares_partout():
    import sys

    sys.path.insert(0, str(DOSSIER.parent.parent))
    from custom_components.vehicule import services as module_services

    services_yaml = (DOSSIER / "services.yaml").read_text(encoding="utf-8")
    for nom in module_services.SERVICES:
        assert f"{nom}:" in services_yaml, f"{nom} absent de services.yaml"
