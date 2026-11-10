# Véhicule — Carnet d'entretien pour Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Tests](https://github.com/guillian77/ha-vehicule/actions/workflows/tests.yml/badge.svg)](https://github.com/guillian77/ha-vehicule/actions/workflows/tests.yml)
[![Release](https://img.shields.io/github/v/release/guillian77/ha-vehicule)](https://github.com/guillian77/ha-vehicule/releases)

Intégration personnalisée : journal d'entretien d'un véhicule, échéances calculées
automatiquement, rappels, calendrier et panneau dédié dans la barre latérale.

Conçue pour une BMW 325i E90 (N52B25) mais entièrement paramétrable : les postes
d'entretien et leurs intervalles sont des données, pas du code.

## Fonctionnalités

- **Journal** : interventions datées avec kilométrage, pièces (nom, quantité, référence),
  coût (optionnel), garage et notes.
- **Échéances** : calcul à partir de l'intervalle en km et/ou en mois de chaque poste
  (vidange 15 000 km / 12 mois par défaut), au premier des deux atteint.
- **États** : `ok`, `a_prevoir` (≤ 2 000 km ou ≤ 30 j), `depasse`, `inconnu`.
- **Calendrier** : `calendar.vehicule_echeances_d_entretien` alimenté automatiquement.
- **Panneau** `Véhicule` (barre latérale) : Accueil, Échéances, Journal, Pièces, Coûts, Réglages.
  Responsive, thème clair/sombre de Home Assistant, aucune dépendance externe (pas de CDN).
- **Export** : CSV (séparateur `;`, BOM UTF-8 pour Excel FR) et JSON complet.

## Stockage et sauvegardes

Tout vit dans le dossier de configuration :

```
/config/vehicule/
  profil.json           # véhicule + postes et intervalles
  interventions.json    # journal complet
  interventions.json.bak / profil.json.bak
  exports/              # CSV / JSON générés à la demande
```

`/config` étant inclus dans les sauvegardes Home Assistant (**complètes** et
partielles « dossier de configuration »), le carnet suit automatiquement vos
sauvegardes. Le capteur binaire `Intégrité du carnet` signale tout fichier absent
ou illisible.

Écritures atomiques (fichier temporaire + `os.replace`) et copie `.bak` avant
chaque écriture : une coupure ne corrompt pas le journal. Un JSON illisible est
déplacé en `.corrompu-<horodatage>` au lieu d'être écrasé.

## Installation

### HACS (recommandé)

1. HACS → Intégrations → menu ⋮ → *Dépôts personnalisés*.
2. Ajouter `https://github.com/guillian77/ha-vehicule`, catégorie **Integration**.
3. Chercher « Véhicule — Carnet d'entretien », installer la version proposée.
4. Redémarrer Home Assistant, puis Paramètres → Appareils et services → *Ajouter une
   intégration* → **Véhicule — Carnet d'entretien**.

Les mises à jour apparaissent ensuite dans HACS (une release GitHub = une version).

### Manuelle

Copier `custom_components/vehicule/` dans `/config/custom_components/`, redémarrer.

### Configuration

Paramètres → Appareils et services → *Ajouter une intégration* → **Véhicule — Carnet
d'entretien**. Renseigner nom, marque, modèle, année, VIN, moteur et kilométrage.
Un seul carnet par instance.

## Entités

| Entité | Rôle |
|---|---|
| `sensor.*_kilometrage` | Kilométrage courant (+ date du relevé) |
| `sensor.*_<poste>_km_restants` | Km restants avant l'échéance |
| `sensor.*_<poste>_etat` | `ok` / `a_prevoir` / `depasse` / `inconnu` |
| `sensor.*_<poste>_jours_restants` | Jours restants (désactivé par défaut) |
| `sensor.*_prochaine_echeance` | Poste le plus urgent |
| `sensor.*_derniere_intervention` | Date et détails de la dernière intervention |
| `calendar.*_echeances_d_entretien` | Échéances datées |
| `binary_sensor.*_integrite_du_carnet` | `on` si un fichier manque ou est illisible |

## Services

| Service | Description |
|---|---|
| `vehicule.enregistrer_intervention` | Ajoute une intervention, calcule l'échéance suivante |
| `vehicule.modifier_intervention` | Corrige une intervention (`id`) |
| `vehicule.supprimer_intervention` | Supprime une intervention (`id`) |
| `vehicule.maj_km` | Met à jour le kilométrage courant |
| `vehicule.exporter` | Écrit un CSV ou JSON, renvoie le chemin (`return_response`) |
| `vehicule.maj_vehicule` | Modifie l'identité du véhicule |
| `vehicule.definir_poste` | Crée/ajuste un poste et ses intervalles |

Exemple :

```yaml
action: vehicule.enregistrer_intervention
data:
  type: vidange
  date: "2026-11-07"
  km: 129277
  cout: 68.40
  garage: fait maison
  pieces:
    - nom: Huile BMW LL-01 5W-30
      qte: 6.5
      ref: "83212390556"
```

Événements bus émis : `vehicule_intervention` (ajout / modification / suppression)
et `vehicule_km`.

## Automatisations types

```yaml
# Rappel 1 000 km avant l'échéance
trigger:
  - platform: numeric_state
    entity_id: sensor.bmw_325i_e90_vidange_moteur_km_restants
    below: 1000
action:
  - service: notify.mobile_app_phone
    data:
      message: "Vidange à prévoir : {{ states('sensor.bmw_325i_e90_vidange_moteur_km_restants') }} km"
```

## Développement

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements_test.txt home-assistant-frontend
pytest
```

Les tests couvrent les calculs (échéances, seuils, statistiques), le stockage
(atomicité, quarantaine, export), les services, le calendrier, l'API websocket du
panneau et l'enregistrement réel du panneau (frontend + chemin statique).

## Licence

MIT.
