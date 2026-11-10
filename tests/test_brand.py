"""Tests des images de marque : HA les sert sur /api/brands/integration/vehicule/…"""

from __future__ import annotations

from pathlib import Path

RACINE = Path(__file__).parent.parent / "custom_components" / "vehicule"
MARQUE = RACINE / "brand"

ATTENDUES = {
    "icon.png": 256,
    "icon@2x.png": 512,
    "dark_icon.png": 256,
    "dark_icon@2x.png": 512,
}


def _entete_png(chemin: Path) -> tuple[int, int, int]:
    """(largeur, hauteur, type de couleur) lus dans l'en-tête IHDR."""
    data = chemin.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{chemin.name} n'est pas un PNG"
    largeur = int.from_bytes(data[16:20], "big")
    hauteur = int.from_bytes(data[20:24], "big")
    type_couleur = data[25]
    return largeur, hauteur, type_couleur


def test_images_de_marque_presentes_et_conformes():
    for nom, taille in ATTENDUES.items():
        chemin = MARQUE / nom
        assert chemin.is_file(), f"image de marque manquante : {nom}"
        largeur, hauteur, type_couleur = _entete_png(chemin)
        assert (largeur, hauteur) == (taille, taille), f"{nom} doit être {taille}×{taille}"
        # 4 = niveaux de gris + alpha, 6 = RVB + alpha : fond transparent exigé.
        assert type_couleur in (4, 6), f"{nom} doit avoir un canal alpha"
        assert chemin.stat().st_size > 2000, f"{nom} semble vide"
