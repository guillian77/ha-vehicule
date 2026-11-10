"""Constantes de l'intégration Véhicule — Carnet d'entretien."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "vehicule"
VERSION = "0.4.3"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.CALENDAR,
]

# --- Stockage -------------------------------------------------------------
# Dossier sous /config : inclus dans le backup complet ET dans le backup
# partiel « dossier de configuration ».
DATA_FOLDER = DOMAIN
PROFIL_FILE = "profil.json"
INTERVENTIONS_FILE = "interventions.json"
EXPORTS_FOLDER = "exports"
SCHEMA_VERSION = 1

# --- Config entry ---------------------------------------------------------
CONF_NOM = "nom"
CONF_MARQUE = "marque"
CONF_MODELE = "modele"
CONF_ANNEE = "annee"
CONF_VIN = "vin"
CONF_MOTEUR = "moteur"
CONF_IMMATRICULATION = "immatriculation"
CONF_KM_ACTUEL = "km_actuel"

DEFAULT_NOM = "Véhicule"

# --- Seuils d'alerte ------------------------------------------------------
SEUIL_KM = 2000
SEUIL_JOURS = 30

ETA_OK = "ok"
ETA_PREVOIR = "a_prevoir"
ETA_DEPASSE = "depasse"
ETA_INCONNU = "inconnu"

# --- Postes d'entretien ---------------------------------------------------
# km = None -> pas d'intervalle kilométrique, mois = None -> pas d'intervalle
# temporel. Un poste sans aucun intervalle n'apparaît que dans le journal.
DEFAULT_POSTES: list[dict] = [
    {
        "id": "vidange",
        "nom": "Vidange moteur",
        "km": 15000,
        "mois": 12,
        "icone": "mdi:oil",
        "actif": True,
    },
    {
        "id": "filtre_habitacle",
        "nom": "Filtre d'habitacle",
        "km": 30000,
        "mois": 24,
        "icone": "mdi:air-filter",
        "actif": True,
    },
    {
        "id": "filtre_air",
        "nom": "Filtre à air",
        "km": 45000,
        "mois": 48,
        "icone": "mdi:air-purifier",
        "actif": True,
    },
    {
        "id": "filtre_carburant",
        "nom": "Filtre à carburant",
        "km": 60000,
        "mois": 60,
        "icone": "mdi:gas-station",
        "actif": True,
    },
    {
        "id": "bougies",
        "nom": "Bougies d'allumage",
        "km": 100000,
        "mois": 120,
        "icone": "mdi:flash",
        "actif": True,
    },
    {
        "id": "liquide_frein",
        "nom": "Liquide de frein",
        "km": None,
        "mois": 24,
        "icone": "mdi:car-brake-alert",
        "actif": True,
    },
    {
        "id": "liquide_refroidissement",
        "nom": "Liquide de refroidissement",
        "km": 60000,
        "mois": 48,
        "icone": "mdi:thermometer-water",
        "actif": True,
    },
    {
        "id": "courroie_accessoire",
        "nom": "Courroie d'accessoire",
        "km": 90000,
        "mois": 72,
        "icone": "mdi:belt",
        "actif": True,
    },
    {
        "id": "plaquettes_avant",
        "nom": "Plaquettes avant",
        "km": 40000,
        "mois": 36,
        "icone": "mdi:car-brake-hold",
        "actif": True,
    },
    {
        "id": "plaquettes_arriere",
        "nom": "Plaquettes arrière",
        "km": 50000,
        "mois": 36,
        "icone": "mdi:car-brake-hold",
        "actif": True,
    },
    {
        "id": "pneus",
        "nom": "Pneus",
        "km": None,
        "mois": None,
        "icone": "mdi:tire",
        "actif": True,
    },
    {
        "id": "controle_technique",
        "nom": "Contrôle technique",
        "km": None,
        "mois": 24,
        "icone": "mdi:clipboard-check",
        "actif": True,
    },
]

# --- Services -------------------------------------------------------------
SERVICE_ENREGISTRER = "enregistrer_intervention"
SERVICE_MODIFIER = "modifier_intervention"
SERVICE_SUPPRIMER = "supprimer_intervention"
SERVICE_MAJ_KM = "maj_km"
SERVICE_EXPORTER = "exporter"
SERVICE_MAJ_VEHICULE = "maj_vehicule"
SERVICE_DEFINIR_POSTE = "definir_poste"
SERVICE_MARQUER_FAIT = "marquer_fait"

ATTR_POSTE = "poste"
ATTR_NOM = "nom"
ATTR_MARQUE = "marque"
ATTR_MODELE = "modele"
ATTR_ANNEE = "annee"
ATTR_VIN = "vin"
ATTR_MOTEUR = "moteur"
ATTR_IMMATRICULATION = "immatriculation"
ATTR_ICONE = "icone"
ATTR_ACTIF = "actif"
ATTR_MOIS = "mois"

ATTR_ID = "id"
ATTR_TYPE = "type"
ATTR_DATE = "date"
ATTR_KM = "km"
ATTR_PIECES = "pieces"
ATTR_COUT = "cout"
ATTR_GARAGE = "garage"
ATTR_NOTES = "notes"
ATTR_PROCHAIN_KM = "prochain_km"
ATTR_PROCHAIN_DATE = "prochain_date"
ATTR_STATUT = "statut"
ATTR_FORMAT = "format"
ATTR_NOM_FICHIER = "nom_fichier"

# --- Statut d'une intervention -------------------------------------------
# Une intervention « à faire » est une intention : elle vit dans le journal
# mais ne compte ni dans les échéances, ni dans les coûts, ni dans les pièces.
STATUT_FAIT = "fait"
STATUT_A_FAIRE = "a_faire"
STATUTS = (STATUT_FAIT, STATUT_A_FAIRE)

EVENT_INTERVENTION = f"{DOMAIN}_intervention"
EVENT_KM = f"{DOMAIN}_km"
