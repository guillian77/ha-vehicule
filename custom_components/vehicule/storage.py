"""Stockage fichier JSON du carnet (écriture atomique + copie de sécurité)."""

from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    DATA_FOLDER,
    DEFAULT_POSTES,
    EXPORTS_FOLDER,
    INTERVENTIONS_FILE,
    PROFIL_FILE,
    SCHEMA_VERSION,
)

_LOGGER = logging.getLogger(__name__)


def profil_par_defaut(vehicule: dict[str, Any] | None = None) -> dict[str, Any]:
    """Profil initial : véhicule vierge + postes d'entretien standard."""
    base = {
        "nom": "",
        "marque": "",
        "modele": "",
        "annee": None,
        "vin": "",
        "moteur": "",
        "immatriculation": "",
        "km_actuel": None,
        "km_maj": None,
    }
    if vehicule:
        base.update({k: v for k, v in vehicule.items() if v is not None})
    return {
        "schema": SCHEMA_VERSION,
        "vehicule": base,
        "postes": [dict(poste) for poste in DEFAULT_POSTES],
    }


def interventions_par_defaut() -> dict[str, Any]:
    return {"schema": SCHEMA_VERSION, "interventions": []}


class CarnetStorage:
    """Lecture/écriture des fichiers du carnet dans `/config/vehicule`."""

    def __init__(self, hass: HomeAssistant, folder: str | None = None) -> None:
        self._hass = hass
        self.folder = Path(folder or hass.config.path(DATA_FOLDER))
        self.profil_path = self.folder / PROFIL_FILE
        self.interventions_path = self.folder / INTERVENTIONS_FILE
        self.exports_path = self.folder / EXPORTS_FOLDER

    # ------------------------------------------------------------------ IO
    def _ensure_dirs(self) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        self.exports_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _read_json(path: Path) -> Any:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        """Écriture atomique : fichier temporaire dans le même dossier."""
        path.parent.mkdir(parents=True, exist_ok=True)
        backup = path.with_suffix(path.suffix + ".bak")
        if path.exists():
            try:
                shutil.copy2(path, backup)
            except OSError as err:  # pragma: no cover - disque plein / droits
                _LOGGER.warning("Copie de sécurité impossible pour %s : %s", path, err)

        fd, tmp = tempfile.mkstemp(
            dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def _quarantine(self, path: Path) -> None:
        """Met de côté un fichier illisible plutôt que de le perdre."""
        try:
            from homeassistant.util import dt as dt_util

            stamp = dt_util.utcnow().strftime("%Y%m%d-%H%M%S")
        except Exception:  # pragma: no cover - contexte de test minimal
            stamp = "corrupt"
        cible = path.with_name(f"{path.name}.corrompu-{stamp}")
        try:
            path.rename(cible)
            _LOGGER.error(
                "Fichier illisible déplacé en %s ; un nouveau fichier a été créé", cible
            )
        except OSError as err:  # pragma: no cover
            _LOGGER.error("Fichier illisible et non déplaçable : %s (%s)", path, err)

    # -------------------------------------------------------------- lecture
    async def async_load(self) -> tuple[dict[str, Any], list[dict]]:
        """Charge profil + journal, en créant les fichiers si absents."""
        return await self._hass.async_add_executor_job(self._load_sync)

    def _load_sync(self) -> tuple[dict[str, Any], list[dict]]:
        self._ensure_dirs()
        profil = self._load_profil()
        interventions = self._load_interventions()
        return profil, interventions

    def _load_profil(self) -> dict[str, Any]:
        if not self.profil_path.exists():
            profil = profil_par_defaut()
            self._write_json(self.profil_path, profil)
            return profil
        try:
            data = self._read_json(self.profil_path)
        except (json.JSONDecodeError, OSError) as err:
            _LOGGER.error("profil.json illisible : %s", err)
            self._quarantine(self.profil_path)
            data = profil_par_defaut()
            self._write_json(self.profil_path, data)
            return data

        if not isinstance(data, dict):
            data = profil_par_defaut()
        data.setdefault("schema", SCHEMA_VERSION)
        data.setdefault("postes", [dict(p) for p in DEFAULT_POSTES])
        vehicule = data.setdefault("vehicule", {})
        vehicule.setdefault("nom", "")
        vehicule.setdefault("km_actuel", None)
        return data

    def _load_interventions(self) -> list[dict]:
        if not self.interventions_path.exists():
            data = interventions_par_defaut()
            self._write_json(self.interventions_path, data)
            return []
        try:
            data = self._read_json(self.interventions_path)
        except (json.JSONDecodeError, OSError) as err:
            _LOGGER.error("interventions.json illisible : %s", err)
            self._quarantine(self.interventions_path)
            self._write_json(self.interventions_path, interventions_par_defaut())
            return []

        items = data.get("interventions", []) if isinstance(data, dict) else []
        return [item for item in items if isinstance(item, dict)]

    # ------------------------------------------------------------- écriture
    async def async_save_profil(self, profil: dict[str, Any]) -> None:
        await self._hass.async_add_executor_job(self._save_profil_sync, profil)

    def _save_profil_sync(self, profil: dict[str, Any]) -> None:
        self._ensure_dirs()
        self._write_json(self.profil_path, profil)

    async def async_save_interventions(self, interventions: list[dict]) -> None:
        await self._hass.async_add_executor_job(
            self._save_interventions_sync, interventions
        )

    def _save_interventions_sync(self, interventions: list[dict]) -> None:
        self._ensure_dirs()
        self._write_json(
            self.interventions_path,
            {
                "schema": SCHEMA_VERSION,
                "interventions": interventions,
            },
        )

    # -------------------------------------------------------------- export
    async def async_export(self, filename: str, content: str) -> str:
        """Écrit un fichier d'export et renvoie son chemin absolu."""
        return await self._hass.async_add_executor_job(
            self._export_sync, filename, content
        )

    def _export_sync(self, filename: str, content: str) -> str:
        self._ensure_dirs()
        safe = "".join(c for c in filename if c.isalnum() or c in "._-") or "export.txt"
        target = self.exports_path / safe
        with target.open("w", encoding="utf-8") as handle:
            handle.write(content)
        return str(target)

    # ------------------------------------------------------------- contrôle
    def _check_sync(self) -> dict[str, Any]:
        """Vérifie l'intégrité des fichiers (cible du binary_sensor)."""
        etat = {
            "ok": True,
            "dossier": str(self.folder),
            "profil": self.profil_path.exists(),
            "interventions": self.interventions_path.exists(),
            "erreurs": [],
        }
        for path, cle in (
            (self.profil_path, "profil"),
            (self.interventions_path, "interventions"),
        ):
            if not path.exists():
                etat["ok"] = False
                etat["erreurs"].append(f"{cle} absent")
                continue
            try:
                with path.open("r", encoding="utf-8") as handle:
                    json.load(handle)
            except (json.JSONDecodeError, OSError) as err:
                etat["ok"] = False
                etat["erreurs"].append(f"{cle} illisible : {err}")
        if not os.access(self.folder, os.W_OK):
            etat["ok"] = False
            etat["erreurs"].append("dossier non inscriptible")
        return etat

    async def async_check(self) -> dict[str, Any]:
        return await self._hass.async_add_executor_job(self._check_sync)
