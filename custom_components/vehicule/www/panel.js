/**
 * Panneau « Véhicule » — carnet d'entretien pour Home Assistant.
 *
 * Élément natif (aucune dépendance externe, aucun CDN) : tout le rendu et les
 * styles vivent dans ce fichier, servi par l'intégration depuis
 * /vehicule_panel/panel.js.
 *
 * Pages : Accueil, Échéances, Journal, Pièces, Coûts, Réglages.
 */

const ETATS = {
  ok: { label: "OK", classe: "ok", icone: "mdi:check-circle-outline" },
  a_prevoir: { label: "À prévoir", classe: "prevoir", icone: "mdi:clock-alert-outline" },
  depasse: { label: "Dépassé", classe: "depasse", icone: "mdi:alert-circle" },
  inconnu: { label: "Inconnu", classe: "inconnu", icone: "mdi:help-circle-outline" },
};

const ONGLETS = [
  { id: "accueil", titre: "Accueil", icone: "mdi:view-dashboard-outline" },
  { id: "echeances", titre: "Échéances", icone: "mdi:calendar-clock" },
  { id: "journal", titre: "Journal", icone: "mdi:book-clock-outline" },
  { id: "pieces", titre: "Pièces", icone: "mdi:cog-outline" },
  { id: "couts", titre: "Coûts", icone: "mdi:cash-multiple" },
  { id: "reglages", titre: "Réglages", icone: "mdi:tune" },
];

const STYLE = `
  :host {
    display: block;
    height: 100%;
    background: var(--primary-background-color, #fafafa);
    color: var(--primary-text-color, #212121);
    font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
    overflow-y: auto;
  }
  * { box-sizing: border-box; }
  .page { max-width: 1100px; margin: 0 auto; padding: 16px 16px 48px; }

  .entete-globale {
    position: sticky; top: 0; z-index: 5;
    background: var(--app-header-background-color, var(--card-background-color, #fff));
    border-bottom: 1px solid var(--divider-color, rgba(0,0,0,.12));
  }
  header.barre {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 16px;
  }
  header.barre h1 {
    font-size: 20px; font-weight: 500; margin: 0; flex: 1;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .km-pastille {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 10px; border-radius: 999px;
    background: var(--secondary-background-color, rgba(0,0,0,.05));
    font-size: 14px; font-variant-numeric: tabular-nums;
  }
  button.menu {
    border: none; background: none; color: inherit; cursor: pointer;
    padding: 6px; border-radius: 50%; display: inline-flex;
  }
  button.menu:hover { background: var(--secondary-background-color, rgba(0,0,0,.06)); }

  nav.onglets {
    display: flex; gap: 4px; overflow-x: auto; scrollbar-width: none;
    padding: 0 16px;
    background: inherit;
  }
  nav.onglets::-webkit-scrollbar { display: none; }
  nav.onglets button {
    flex: 0 0 auto; border: none; background: none; cursor: pointer;
    color: var(--secondary-text-color, #666);
    padding: 10px 12px; font-size: 14px; font-weight: 500;
    border-bottom: 2px solid transparent;
    display: inline-flex; align-items: center; gap: 6px;
  }
  nav.onglets button[aria-selected="true"] {
    color: var(--primary-color, #03a9f4);
    border-bottom-color: var(--primary-color, #03a9f4);
  }

  .grille { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
  .grille > .carte { min-width: 0; }
  .carte {
    min-width: 0;
    background: var(--card-background-color, #fff);
    border-radius: var(--ha-card-border-radius, 12px);
    box-shadow: var(--ha-card-box-shadow, 0 1px 3px rgba(0,0,0,.08));
    padding: 14px 16px;
  }
  .carte h2, .carte h3 { margin: 0 0 8px; font-weight: 500; }
  .carte h2 { font-size: 18px; }
  .carte h3 { font-size: 15px; color: var(--secondary-text-color); }
  .valeur { font-size: 28px; font-weight: 300; font-variant-numeric: tabular-nums; }
  .valeur small { font-size: 14px; font-weight: 400; color: var(--secondary-text-color); }
  .libelle { font-size: 13px; color: var(--secondary-text-color); }
  .rangee { display: flex; align-items: center; gap: 10px; }
  .espace { flex: 1; }
  .muted { color: var(--secondary-text-color); }
  .petit { font-size: 12px; }

  .badge {
    flex: 0 0 auto;
    display: inline-flex; align-items: center; gap: 4px;
    padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 600;
    white-space: nowrap;
  }
  .badge.ok { background: rgba(67,160,71,.15); color: #2e7d32; }
  .badge.prevoir { background: rgba(251,140,0,.18); color: #e65100; }
  .badge.depasse { background: rgba(229,57,53,.15); color: #c62828; }
  .badge.inconnu { background: rgba(120,120,120,.15); color: var(--secondary-text-color); }
  @media (prefers-color-scheme: dark) {
    .badge.ok { color: #81c784; }
    .badge.prevoir { color: #ffb74d; }
    .badge.depasse { color: #e57373; }
  }

  .jauge { height: 6px; border-radius: 3px; background: var(--divider-color, rgba(0,0,0,.12)); overflow: hidden; margin: 8px 0 4px; }
  .jauge > span { display: block; height: 100%; border-radius: 3px; transition: width .3s ease; }
  .jauge > span.ok { background: #43a047; }
  .jauge > span.prevoir { background: #fb8c00; }
  .jauge > span.depasse { background: #e53935; }
  .jauge > span.inconnu { background: #9e9e9e; }

  .liste { display: flex; flex-direction: column; }
  .ligne {
    display: flex; align-items: center; gap: 12px; padding: 10px 0;
    border-bottom: 1px solid var(--divider-color, rgba(0,0,0,.08));
  }
  .ligne:last-child { border-bottom: none; }
  .ligne .titre-ligne { font-weight: 500; }
  .ligne .sous { font-size: 12px; color: var(--secondary-text-color); margin-top: 2px; }
  .ligne .droite { text-align: right; font-variant-numeric: tabular-nums; }

  button.action {
    border: 1px solid var(--divider-color, rgba(0,0,0,.2));
    background: transparent; color: var(--primary-text-color);
    border-radius: 8px; padding: 6px 12px; cursor: pointer; font-size: 13px;
    display: inline-flex; align-items: center; gap: 6px;
  }
  button.action:hover { background: var(--secondary-background-color, rgba(0,0,0,.05)); }
  button.action.primaire {
    background: var(--primary-color, #03a9f4); color: var(--text-primary-color, #fff);
    border-color: transparent; font-weight: 500;
  }
  button.action.danger { color: var(--error-color, #c62828); border-color: currentColor; }
  button.action:disabled { opacity: .5; cursor: not-allowed; }
  button.icone { border: none; background: none; cursor: pointer; color: var(--secondary-text-color); padding: 6px; border-radius: 50%; }
  button.icone:hover { background: var(--secondary-background-color, rgba(0,0,0,.06)); }

  .entete-section { display: flex; align-items: center; gap: 12px; margin: 22px 0 10px; }
  .entete-section h2 { font-size: 17px; font-weight: 500; margin: 0; flex: 1; }

  .vide {
    text-align: center; padding: 40px 16px; color: var(--secondary-text-color);
  }
  .vide ha-icon { --mdc-icon-size: 40px; opacity: .6; }

  .champs { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
  label.champ { display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: var(--secondary-text-color); }
  label.champ.wide { grid-column: 1 / -1; }
  .champ.wide { grid-column: 1 / -1; display: flex; flex-direction: column; gap: 4px; }
  .champ .etiquette { font-size: 13px; color: var(--secondary-text-color, #727272); }
  .segments { display: inline-flex; gap: 6px; flex-wrap: wrap; }
  .segment {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 8px 14px; border-radius: 999px; cursor: pointer; font: inherit;
    border: 1px solid var(--divider-color, rgba(0,0,0,.16));
    background: var(--card-background-color, #fff); color: var(--primary-text-color);
  }
  .segment ha-icon { --mdc-icon-size: 18px; }
  .segment.actif {
    background: var(--primary-color, #03a9f4); border-color: transparent; color: #fff;
  }
  input, select, textarea {
    font: inherit; color: inherit; padding: 8px 10px; border-radius: 8px;
    border: 1px solid var(--divider-color, rgba(0,0,0,.25));
    background: var(--card-background-color, #fff); width: 100%;
  }
  input:focus, select:focus, textarea:focus {
    outline: none; border-color: var(--primary-color, #03a9f4);
    box-shadow: 0 0 0 1px var(--primary-color, #03a9f4);
  }
  textarea { min-height: 64px; resize: vertical; }
  .barre-outils { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 12px; }
  .barre-outils input, .barre-outils select { width: auto; min-width: 130px; }

  .pieces-editeur .pieces-entete, .pieces-editeur .piece-ligne {
    display: grid; grid-template-columns: 1.5fr 68px 1.9fr 80px 74px 28px;
    gap: 8px; align-items: center;
  }
  .pieces-editeur .pieces-entete {
    font-size: 11px; text-transform: uppercase; letter-spacing: .03em;
    color: var(--secondary-text-color, #727272); margin-bottom: 6px;
  }
  .pieces-editeur .pieces-entete span:last-child, .pieces-editeur .pieces-entete .droite {
    text-align: right;
  }
  .pieces-editeur .piece-ligne { margin-bottom: 8px; }
  .pieces-editeur .piece-ligne .total-piece {
    font-size: 13px; text-align: right; font-variant-numeric: tabular-nums;
    color: var(--secondary-text-color, #727272);
  }
  .pieces-editeur .total-pieces { text-align: right; font-size: 13px; margin: 4px 0 0; }

  .overlay {
    position: fixed; inset: 0; z-index: 20; background: rgba(0,0,0,.45);
    display: flex; align-items: center; justify-content: center; padding: 16px;
  }
  .boite {
    background: var(--card-background-color, #fff); color: var(--primary-text-color);
    border-radius: 16px; width: min(760px, 100%); max-height: 90vh; overflow-y: auto;
    padding: 20px; box-shadow: 0 12px 40px rgba(0,0,0,.3);
  }
  .boite h2 { margin: 0 0 4px; font-size: 20px; font-weight: 500; }
  .boite .pied { display: flex; justify-content: flex-end; gap: 8px; margin-top: 18px;
    position: sticky; bottom: -20px; padding: 12px 0 4px; background: var(--card-background-color, #fff); }

  .barre-stat { display: flex; align-items: center; gap: 10px; padding: 6px 0; }
  .barre-stat .fond { flex: 1; height: 10px; border-radius: 5px; background: var(--divider-color, rgba(0,0,0,.1)); overflow: hidden; }
  .barre-stat .fond > span { display: block; height: 100%; background: var(--primary-color, #03a9f4); border-radius: 5px; }
  .barre-stat .montant { width: 90px; text-align: right; font-variant-numeric: tabular-nums; font-size: 13px; }

  .info-encadre {
    display: flex; gap: 10px; align-items: flex-start; padding: 12px 14px;
    border-radius: 10px; background: rgba(3,169,244,.08);
    font-size: 13px; line-height: 1.45;
  }
  .info-encadre.warn { background: rgba(251,140,0,.12); }

  table.mini { width: 100%; border-collapse: collapse; font-size: 13px; }
  table.mini th, table.mini td { text-align: left; padding: 6px 4px; border-bottom: 1px solid var(--divider-color, rgba(0,0,0,.08)); }
  table.mini th { color: var(--secondary-text-color); font-weight: 500; }
  table.mini td.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }

  .toast {
    position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%);
    background: var(--primary-text-color, #212121); color: var(--card-background-color, #fff);
    padding: 10px 18px; border-radius: 999px; font-size: 14px; z-index: 30;
    box-shadow: 0 6px 24px rgba(0,0,0,.3); max-width: 90vw;
  }

  @media (max-width: 600px) {
    .page { padding: 12px 10px 40px; }
    .valeur { font-size: 24px; }
    .pieces-editeur .pieces-entete { display: none; }
    .pieces-editeur .piece-ligne { grid-template-columns: 1fr 58px; }
    .pieces-editeur .piece-ligne input.ref,
    .pieces-editeur .piece-ligne input.prix { grid-column: 1 / 2; }
    .pieces-editeur .piece-ligne .total-piece { grid-column: 2 / 3; text-align: right; }
    header.barre h1 { font-size: 17px; }
  }
`;

const esc = (valeur) =>
  String(valeur ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));

const nombre = (valeur, decimales = 0) => {
  if (valeur === null || valeur === undefined || Number.isNaN(Number(valeur))) return "—";
  return Number(valeur).toLocaleString("fr-FR", {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
  });
};

const km = (valeur) => (valeur === null || valeur === undefined ? "—" : `${nombre(valeur)} km`);
const euros = (valeur) =>
  valeur === null || valeur === undefined ? "—" : `${nombre(valeur, 2)} €`;

const dateFr = (iso) => {
  if (!iso) return "—";
  const [a, m, j] = String(iso).slice(0, 10).split("-");
  return j && m && a ? `${j}/${m}/${a}` : String(iso);
};

const aujourdhui = () => new Date().toISOString().slice(0, 10);

// Identifiant stable d'un poste créé à la volée (accents et espaces normalisés).
const slugId = (texte) =>
  String(texte ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 48);

const POSTE_LIBRE = "__libre__";

const ICONES_POSTE = [
  { id: "mdi:wrench", nom: "Clé (générique)" },
  { id: "mdi:oil", nom: "Huile" },
  { id: "mdi:air-filter", nom: "Filtre" },
  { id: "mdi:car-brake-alert", nom: "Freins" },
  { id: "mdi:tire", nom: "Pneus" },
  { id: "mdi:battery-charging", nom: "Batterie / masse" },
  { id: "mdi:flash", nom: "Allumage" },
  { id: "mdi:water", nom: "Liquide" },
  { id: "mdi:car-cog", nom: "Mécanique" },
  { id: "mdi:magnify-scan", nom: "Diagnostic" },
];

const etatDe = (valeur) => ETATS[valeur] || ETATS.inconnu;

const intervalleTexte = (poste) => {
  const parties = [];
  if (poste.intervalle_km) parties.push(`${nombre(poste.intervalle_km)} km`);
  if (poste.intervalle_mois) {
    parties.push(poste.intervalle_km ? `${poste.intervalle_mois} mois` : `tous les ${poste.intervalle_mois} mois`);
  }
  return parties.length ? parties.join(" · ") : "selon usure";
};

const pourcentage = (poste) => {
  const intervalle = poste.intervalle_km;
  const derniere = poste.derniere;
  if (intervalle && derniere && derniere.km != null && poste.donnees?.km_actuel != null) {
    const utilise = poste.donnees.km_actuel - derniere.km;
    return Math.max(0, Math.min(100, (utilise / intervalle) * 100));
  }
  if (poste.intervalle_mois && derniere?.date && poste.prochain_date) {
    const debut = new Date(derniere.date).getTime();
    const fin = new Date(poste.prochain_date).getTime();
    if (fin > debut) {
      return Math.max(0, Math.min(100, ((Date.now() - debut) / (fin - debut)) * 100));
    }
  }
  if (poste.etat === "depasse") return 100;
  return 0;
};

class VehiculePanel extends HTMLElement {
  constructor() {
    super();
    this._shadow = this.attachShadow({ mode: "open" });
    this._onglet = "accueil";
    this._data = null;
    this._chargement = true;
    this._erreur = null;
    this._narrow = false;
    this._dialogue = null; // {modele, pieces:[], intervention?}
    this._filtres = { type: "all", annee: "all", statut: "all", q: "" };
    this._occupe = false;
    this._shadow.addEventListener("click", (evt) => this._onClick(evt));
    this._shadow.addEventListener("submit", (evt) => this._onSubmit(evt));
    this._shadow.addEventListener("input", (evt) => this._onInput(evt));
    this._shadow.addEventListener("change", (evt) => this._onInput(evt));
  }

  // ----------------------------------------------------------- propriétés
  set hass(hass) {
    const premier = !this._hass;
    this._hass = hass;
    if (premier) this._charger();
    else if (!this._data) this._render();
  }

  set narrow(valeur) {
    this._narrow = !!valeur;
    if (this._data) this._render();
  }

  set panel(valeur) {
    this._panel = valeur;
  }

  set route(valeur) {
    this._route = valeur;
    const chemin = valeur?.path;
    if (chemin && ONGLETS.some((o) => o.id === chemin) && chemin !== this._onglet) {
      this._onglet = chemin;
      if (this._data) this._render();
    }
  }

  disconnectedCallback() {
    clearTimeout(this._minuteurToast);
  }

  // -------------------------------------------------------------- données
  async _charger() {
    this._chargement = true;
    try {
      this._data = await this._hass.callWS({ type: "vehicule/data" });
      this._erreur = null;
    } catch (err) {
      this._erreur = err?.message || String(err);
    } finally {
      this._chargement = false;
      this._render();
    }
  }

  async _appelerService(service, data = {}) {
    if (this._occupe) return null;
    this._occupe = true;
    try {
      const resultat = await this._hass.callService("vehicule", service, data);
      await this._charger();
      return resultat;
    } catch (err) {
      this._toast(`Erreur : ${err?.message || err}`);
      return null;
    } finally {
      this._occupe = false;
    }
  }

  _toast(message) {
    this.dispatchEvent(
      new CustomEvent("hass-notification", {
        detail: { message },
        bubbles: true,
        composed: true,
      })
    );
    const existant = this._shadow.querySelector(".toast");
    if (existant) existant.remove();
    const noeud = document.createElement("div");
    noeud.className = "toast";
    noeud.textContent = message;
    this._shadow.appendChild(noeud);
    clearTimeout(this._minuteurToast);
    this._minuteurToast = setTimeout(() => noeud.remove(), 3000);
  }

  _allerOnglet(id) {
    this._onglet = id;
    this._render();
    // Navigation interne : on ne touche pas à l'historique du routeur HA.
    this.scrollTop = 0;
  }

  // ------------------------------------------------------------ dialogue
  _ouvrirDialogue(intervention = null, typePredefini = null) {
    const postes = this._data?.postes || [];
    const vehicule = this._data?.vehicule || {};
    const connus = postes.map((p) => p.id);
    const typeDefaut =
      typePredefini && connus.includes(typePredefini)
        ? typePredefini
        : postes[0]?.id || "vidange";
    const base = intervention || {
      date: aujourdhui(),
      km: vehicule.km_actuel ?? "",
      type: typeDefaut,
    };
    // Une intervention dont le poste n'existe plus (ou saisi librement) reste
    // modifiable : on la présente avec son libellé d'origine.
    const libre = !!intervention && !connus.includes(intervention.type);
    this._dialogue = {
      modele: true,
      edition: !!intervention,
      form: {
        id: intervention?.id || null,
        statut: intervention?.statut || "fait",
        type: libre ? POSTE_LIBRE : base.type || "vidange",
        type_original: intervention?.type || null,
        nom_libre: libre ? intervention.nom || "" : "",
        date: base.date || aujourdhui(),
        km: base.km ?? "",
        cout: intervention?.cout ?? "",
        garage: intervention?.garage || "",
        notes: intervention?.notes || "",
        // Vide par défaut : l'échéance reste recalculée automatiquement.
        prochain_km: "",
        prochain_date: "",
        suggere_km: intervention?.prochain?.km ?? "",
        suggere_date: intervention?.prochain?.date || "",
      },
      cout_auto: "",
      pieces: (intervention?.pieces || []).map((p) => ({
        nom: p.nom || "",
        qte: p.qte ?? "",
        ref: p.ref || "",
        prix: p.prix ?? "",
      })),
    };
    if (!this._dialogue.pieces.length) {
      this._dialogue.pieces.push({ nom: "", qte: "", ref: "" });
    }
    this._render();
    this._majTotalPieces();
  }

  /** Recalcule les totaux de pièces et propose le coût global. */
  _majTotalPieces() {
    if (!this._dialogue) return;
    const lignes = [...this._shadow.querySelectorAll(".piece-ligne")];
    let total = 0;
    let chiffre = false;
    for (const ligne of lignes) {
      const prixBrut = String(ligne.querySelector('[name="piece_prix"]')?.value ?? "").trim();
      const qteBrute = String(ligne.querySelector('[name="piece_qte"]')?.value ?? "").trim();
      const qte = qteBrute === "" ? 1 : Number(qteBrute);
      const valeur = prixBrut === "" || !Number.isFinite(Number(prixBrut))
        ? null
        : Number(prixBrut) * (Number.isFinite(qte) ? qte : 1);
      if (valeur !== null) {
        total += valeur;
        chiffre = true;
      }
      const cellule = ligne.querySelector(".total-piece");
      if (cellule) cellule.textContent = valeur === null ? "" : euros(valeur);
    }

    const suggestion = chiffre ? total.toFixed(2) : "";
    const champ = this._shadow.querySelector('[name="cout"]');
    if (champ) {
      const actuel = String(champ.value || "").trim();
      if (actuel === "" || actuel === this._dialogue.cout_auto) champ.value = suggestion;
      this._dialogue.form.cout = champ.value;
    }
    this._dialogue.cout_auto = suggestion;
    const resume = this._shadow.querySelector(".total-pieces");
    if (resume) resume.textContent = chiffre ? `Pièces : ${euros(total)}` : "";
  }

  _fermerDialogue() {
    this._dialogue = null;
    this._render();
  }

  _lireFormulaire() {
    if (!this._dialogue) return;
    const lire = (nom) => this._shadow.querySelector(`[name="${nom}"]`)?.value ?? "";
    const form = this._dialogue.form;
    form.type = lire("type");
    form.nom_libre = lire("nom_libre");
    form.date = lire("date");
    form.km = lire("km");
    form.cout = lire("cout");
    form.garage = lire("garage");
    form.notes = lire("notes");
    form.prochain_km = lire("prochain_km");
    form.prochain_date = lire("prochain_date");

    const lignes = [...this._shadow.querySelectorAll(".piece-ligne")];
    this._dialogue.pieces = lignes.map((ligne) => ({
      nom: ligne.querySelector('[name="piece_nom"]')?.value || "",
      qte: ligne.querySelector('[name="piece_qte"]')?.value || "",
      ref: ligne.querySelector('[name="piece_ref"]')?.value || "",
      prix: ligne.querySelector('[name="piece_prix"]')?.value || "",
    }));
  }

  async _enregistrerDialogue() {
    this._lireFormulaire();
    const { form, pieces, edition } = this._dialogue;

    // Poste libre : le libellé saisi devient le nom et sert à l'identifiant.
    let type = form.type;
    let nom = null;
    if (type === POSTE_LIBRE) {
      nom = (form.nom_libre || "").trim();
      if (!nom) {
        this._toast("Indique le libellé de l'intervention");
        this._shadow.querySelector('[name="nom_libre"]')?.focus();
        return;
      }
      type = (edition && form.type_original) || slugId(nom) || "intervention";
    }

    const donnees = {
      type,
      statut: form.statut === "a_faire" ? "a_faire" : "fait",
      date: form.date || aujourdhui(),
      notes: form.notes || null,
      garage: form.garage || null,
      pieces: pieces.filter((p) => p.nom).map((p) => ({
        nom: p.nom,
        qte: p.qte === "" ? null : Number(p.qte),
        ref: p.ref || null,
        prix: p.prix === "" || p.prix === null ? null : Number(p.prix),
      })),
    };
    if (nom) donnees.nom = nom;
    if (form.km !== "" && form.km !== null) donnees.km = Number(form.km);
    if (form.cout !== "" && form.cout !== null) donnees.cout = Number(form.cout);
    if (form.prochain_km !== "") donnees.prochain_km = Number(form.prochain_km);
    if (form.prochain_date !== "") donnees.prochain_date = form.prochain_date;

    const service = edition ? "modifier_intervention" : "enregistrer_intervention";
    if (edition) donnees.id = form.id;
    const resultat = await this._appelerService(service, donnees);
    if (resultat !== null) {
      this._dialogue = null;
      this._toast(edition ? "Intervention mise à jour" : "Intervention enregistrée");
      this._render();
    }
  }

  // --------------------------------------------------------------- rendu
  _render() {
    if (this._chargement && !this._data) {
      this._shadow.innerHTML = `<style>${STYLE}</style>
        <div class="page vide"><p>Chargement du carnet…</p></div>`;
      return;
    }

    if (this._erreur) {
      this._shadow.innerHTML = `<style>${STYLE}</style>
        <div class="page">
          <div class="carte" style="border-left:4px solid var(--error-color,#c62828)">
            <h2>Carnet indisponible</h2>
            <p class="muted">${esc(this._erreur)}</p>
            <button class="action primaire" data-action="recharger">Réessayer</button>
          </div>
        </div>`;
      return;
    }

    const vehicule = this._data.vehicule || {};
    const nom = vehicule.nom || "Véhicule";
    const kmActuel = vehicule.km_actuel;

    this._shadow.innerHTML = `
      <style>${STYLE}</style>
      <div class="entete-globale">
      <header class="barre">
        ${this._narrow ? `<button class="menu" data-action="menu" aria-label="Menu"><ha-icon icon="mdi:menu"></ha-icon></button>` : ""}
        <h1>${esc(nom)}</h1>
        <span class="km-pastille"><ha-icon icon="mdi:counter"></ha-icon>${km(kmActuel)}</span>
      </header>
      <nav class="onglets" role="tablist">
        ${ONGLETS.map((onglet) => `
          <button role="tab" data-action="onglet" data-onglet="${onglet.id}"
            aria-selected="${this._onglet === onglet.id}">
            <ha-icon icon="${onglet.icone}"></ha-icon>${onglet.titre}
          </button>`).join("")}
      </nav>
      </div>
      <div class="page">${this._renduOnglet()}</div>
      ${this._dialogue ? this._renduDialogue() : ""}
    `;
  }

  _renduOnglet() {
    switch (this._onglet) {
      case "echeances": return this._renduEcheances();
      case "journal": return this._renduJournal();
      case "pieces": return this._renduPieces();
      case "couts": return this._renduCouts();
      case "reglages": return this._renduReglages();
      default: return this._renduAccueil();
    }
  }

  // ------------------------------------------------------------- accueil
  _renduAccueil() {
    const { echeances = [], stats = {}, interventions = [], vehicule = {} } =
      this._data;
    const alertes = echeances.filter((e) => e.etat === "depasse" || e.etat === "a_prevoir");
    const prochaine = this._data.prochaine_alerte;
    const aFaire = this._data.a_faire || [];
    const realisees = interventions.filter((item) => (item.statut || "fait") === "fait");
    const dernieres = realisees.slice(0, 4);

    if (!interventions.length) {
      return `
        ${this._cartouches(0)}
        <div class="carte" style="margin-top:14px">
          <div class="vide">
            <ha-icon icon="mdi:car-wrench"></ha-icon>
            <h2>Aucune intervention enregistrée</h2>
            <p class="muted">Commence par saisir un kilométrage, puis enregistre ta première intervention.
            Les échéances se calculent automatiquement à partir des intervalles du profil.</p>
            <button class="action primaire" data-action="nouvelle">Enregistrer une intervention</button>
          </div>
        </div>`;
    }

    return `
      ${this._cartouches(alertes.length)}
      ${aFaire.length ? `
        <div class="entete-section"><h2>À faire</h2>
          <span class="badge inconnu">${aFaire.length}</span></div>
        <div class="carte"><div class="liste">
          ${aFaire.map((item) => `
            <div class="ligne">
              <ha-icon icon="mdi:clipboard-text-clock-outline"></ha-icon>
              <div style="flex:1;min-width:0">
                <div class="titre-ligne">${esc(item.nom || item.type)}</div>
                <div class="sous">${item.date ? `prévu le ${dateFr(item.date)}` : "sans date"}${
                  item.km != null ? ` · ${km(item.km)}` : ""
                }${item.garage ? ` · ${esc(item.garage)}` : ""}</div>
              </div>
              <button class="action primaire" data-action="marquer-fait" data-id="${esc(item.id)}">Fait</button>
            </div>`).join("")}
        </div></div>` : ""}
      ${prochaine ? `
        <div class="carte" style="margin-top:14px;border-left:4px solid ${
          prochaine.etat === "depasse" ? "var(--error-color,#c62828)" : "var(--warning-color,#fb8c00)"
        }">
          <div class="rangee">
            <ha-icon icon="${esc(prochaine.icone || "mdi:wrench")}"></ha-icon>
            <div style="flex:1">
              <div class="libelle">Prochaine échéance</div>
              <h2 style="margin:2px 0 0">${esc(prochaine.nom)}</h2>
            </div>
            <span class="badge ${etatDe(prochaine.etat).classe}">${etatDe(prochaine.etat).label}</span>
          </div>
          <div class="rangee" style="margin-top:12px;gap:24px">
            <div>
              <div class="valeur">${prochaine.km_restants != null
                ? `${nombre(prochaine.km_restants)} <small>km restants</small>`
                : prochaine.jours_restants != null
                  ? `${nombre(prochaine.jours_restants)} <small>jours</small>`
                  : esc(dateFr(prochaine.prochain_date))}</div>
              <div class="petit muted">${
                prochaine.prochain_date ? `Échéance le ${dateFr(prochaine.prochain_date)}` : ""
              }${prochaine.prochain_km ? ` · à ${km(prochaine.prochain_km)}` : ""}${
                prochaine.km_restants != null &&
                prochaine.jours_restants != null &&
                prochaine.jours_restants < 0
                  ? ` · dépassée de ${nombre(-prochaine.jours_restants)} j`
                  : ""
              }</div>
            </div>
          </div>
          <div class="jauge"><span class="${etatDe(prochaine.etat).classe}" style="width:${pourcentage({
            ...prochaine,
            donnees: { km_actuel: vehicule.km_actuel },
          }).toFixed(0)}%"></span></div>
          <div class="rangee" style="margin-top:12px">
            <button class="action primaire" data-action="nouvelle" data-type="${esc(prochaine.id)}">Marquer comme fait</button>
            <button class="action" data-action="onglet" data-onglet="echeances">Tout voir</button>
          </div>
        </div>` : ""}

      ${alertes.length ? `
        <div class="entete-section"><h2>À prévoir</h2>
          <span class="badge ${alertes.some((a) => a.etat === "depasse") ? "depasse" : "prevoir"}">
            ${alertes.length} poste${alertes.length > 1 ? "s" : ""}</span></div>
        <div class="carte"><div class="liste">
          ${alertes.slice(0, 5).map((item) => this._ligneEcheance(item, false)).join("")}
        </div></div>` : ""}

      <div class="entete-section"><h2>Dernières interventions</h2>
        <button class="action" data-action="onglet" data-onglet="journal">Journal</button></div>
      <div class="carte"><div class="liste">
        ${dernieres.map((item) => `
          <div class="ligne">
            <ha-icon icon="${esc((this._data.postes || []).find((p) => p.id === item.type)?.icone || "mdi:wrench")}"></ha-icon>
            <div style="flex:1">
              <div class="titre-ligne">${esc(item.nom || item.type)}</div>
              <div class="sous">${dateFr(item.date)}${item.km != null ? ` · ${km(item.km)}` : ""}${
                item.garage ? ` · ${esc(item.garage)}` : ""
              }</div>
            </div>
            <div class="droite">${item.cout != null ? euros(item.cout) : `<span class="muted petit">coût n.c.</span>`}</div>
          </div>`).join("")}
      </div></div>

      <p class="petit muted" style="margin-top:18px">
        ${stats.total ? `Total dépensé : ${euros(stats.total)} · ` : ""}${interventions.length} intervention(s) enregistrée(s)
      </p>
    `;
  }

  _cartouches(nbAlertes) {
    const { stats = {}, vehicule = {}, echeances = [] } = this._data;
    const suivis = echeances.length;
    return `
      <div class="grille">
        <div class="carte">
          <h3>Kilométrage</h3>
          <div class="valeur">${km(vehicule.km_actuel)}</div>
          <div class="rangee" style="margin-top:8px">
            <span class="petit muted">${vehicule.km_maj ? `relevé le ${dateFr(vehicule.km_maj)}` : "jamais relevé"}</span>
            <span class="espace"></span>
            <button class="action" data-action="maj-km">Mettre à jour</button>
          </div>
        </div>
        <div class="carte">
          <h3>Alertes</h3>
          <div class="valeur">${nbAlertes} <small>poste${nbAlertes > 1 ? "s" : ""}</small></div>
          <div class="petit muted">${suivis} poste(s) suivis</div>
        </div>
        <div class="carte">
          <h3>Dépenses</h3>
          <div class="valeur">${euros(stats.total || 0)}</div>
          <div class="petit muted">${stats.sans_cout ? `${stats.sans_cout} intervention(s) sans coût` : "toutes interventions chiffrées"}</div>
        </div>
      </div>`;
  }

  // ----------------------------------------------------------- échéances
  _ligneEcheance(item, avecBouton = true) {
    const etat = etatDe(item.etat);
    const reste = [];
    if (item.km_restants != null) {
      reste.push(`${nombre(item.km_restants)} km`);
    }
    if (item.jours_restants != null) {
      reste.push(`${nombre(item.jours_restants)} j`);
    }
    return `
      <div class="ligne">
        <ha-icon icon="${esc(item.icone || "mdi:wrench")}"></ha-icon>
        <div style="flex:1">
          <div class="titre-ligne">${esc(item.nom)}</div>
          <div class="sous">
            ${item.derniere
              ? `Dernière : ${dateFr(item.derniere.date)}${item.derniere.km != null ? ` · ${km(item.derniere.km)}` : ""}`
              : "Aucune intervention enregistrée"}
            ${item.prochain_date ? ` → ${dateFr(item.prochain_date)}` : ""}
          </div>
        </div>
        <div class="droite">
          <span class="badge ${etat.classe}">${etat.label}</span>
          <div class="petit muted">${reste.length ? reste.join(" · ") : "—"}</div>
        </div>
        ${avecBouton ? `<button class="icone" title="Enregistrer une intervention"
          data-action="nouvelle" data-type="${esc(item.id)}"><ha-icon icon="mdi:plus"></ha-icon></button>` : ""}
      </div>`;
  }

  _renduEcheances() {
    const { echeances = [], vehicule = {} } = this._data;
    if (!echeances.length) {
      return `<div class="carte vide">Aucun poste suivi.</div>`;
    }
    return `
      <div class="entete-section"><h2>Postes suivis</h2>
        <button class="action primaire" data-action="nouvelle">Nouvelle intervention</button></div>
      <div class="grille">
        ${echeances.map((item) => {
          const etat = etatDe(item.etat);
          const prog = pourcentage({ ...item, donnees: { km_actuel: vehicule.km_actuel } });
          return `
          <div class="carte">
            <div class="rangee">
              <ha-icon icon="${esc(item.icone || "mdi:wrench")}"></ha-icon>
              <div style="flex:1">
                <div class="titre-ligne">${esc(item.nom)}</div>
                <div class="sous">${intervalleTexte(item)}</div>
              </div>
              <span class="badge ${etat.classe}">${etat.label}</span>
            </div>
            <div class="jauge"><span class="${etat.classe}" style="width:${prog.toFixed(0)}%"></span></div>
            <div class="rangee">
              <div>
                <div class="valeur" style="font-size:22px">${item.km_restants != null
                  ? `${nombre(item.km_restants)} <small>km</small>`
                  : item.jours_restants != null
                    ? `${nombre(item.jours_restants)} <small>j</small>`
                    : "—"}</div>
                <div class="petit muted">${
                  item.prochain_date ? `Échéance ${dateFr(item.prochain_date)}` : "sans date"
                }${item.prochain_km ? ` · ${km(item.prochain_km)}` : ""}</div>
              </div>
              <span class="espace"></span>
              <button class="action" data-action="nouvelle" data-type="${esc(item.id)}">Fait</button>
            </div>
            <div class="petit muted" style="margin-top:8px">
              ${item.derniere ? `Dernière : ${dateFr(item.derniere.date)}${item.derniere.km != null ? ` à ${km(item.derniere.km)}` : ""}` : "Jamais enregistré"}
            </div>
          </div>`;
        }).join("")}
      </div>`;
  }

  // -------------------------------------------------------------- journal
  _renduJournal() {
    const { interventions = [], postes = [] } = this._data;
    const annees = [...new Set(interventions.map((i) => String(i.date || "").slice(0, 4)))]
      .filter(Boolean)
      .sort()
      .reverse();
    const q = this._filtres.q.trim().toLowerCase();
    const filtrees = interventions.filter((item) => {
      const statut = item.statut || "fait";
      if (this._filtres.statut !== "all" && statut !== this._filtres.statut) return false;
      if (this._filtres.type !== "all" && item.type !== this._filtres.type) return false;
      if (this._filtres.annee !== "all" && String(item.date || "").slice(0, 4) !== this._filtres.annee) return false;
      if (!q) return true;
      const texte = [item.nom, item.garage, item.notes, ...(item.pieces || []).map((p) => p.nom)]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return texte.includes(q);
    });

    return `
      <div class="barre-outils">
        <select name="filtre-type" data-filtre="type">
          <option value="all">Tous les postes</option>
          ${postes.map((p) => `<option value="${esc(p.id)}" ${this._filtres.type === p.id ? "selected" : ""}>${esc(p.nom)}</option>`).join("")}
          ${[...new Set(interventions
            .filter((item) => !postes.some((p) => p.id === item.type))
            .map((item) => item.type))].map((type) => {
            const libelle = interventions.find((item) => item.type === type)?.nom || type;
            return `<option value="${esc(type)}" ${this._filtres.type === type ? "selected" : ""}>${esc(libelle)}</option>`;
          }).join("")}
        </select>
        <select name="filtre-statut" data-filtre="statut">
          <option value="all">Tous les statuts</option>
          <option value="a_faire" ${this._filtres.statut === "a_faire" ? "selected" : ""}>À faire</option>
          <option value="fait" ${this._filtres.statut === "fait" ? "selected" : ""}>Réalisées</option>
        </select>
        <select name="filtre-annee" data-filtre="annee">
          <option value="all">Toutes les années</option>
          ${annees.map((a) => `<option value="${a}" ${this._filtres.annee === a ? "selected" : ""}>${a}</option>`).join("")}
        </select>
        <input type="search" name="filtre-q" data-filtre="q" placeholder="Rechercher…" value="${esc(this._filtres.q)}">
        <span class="espace"></span>
        <button class="action primaire" data-action="nouvelle">+ Intervention</button>
      </div>
      ${!interventions.length
        ? `<div class="carte vide"><ha-icon icon="mdi:book-clock-outline"></ha-icon>
             <p>Aucune intervention pour l'instant.</p>
             <button class="action primaire" data-action="nouvelle">Enregistrer la première</button></div>`
        : `<div class="carte"><div class="liste">
            ${filtrees.length ? filtrees.map((item) => this._ligneJournal(item, postes)).join("")
              : `<div class="vide petit">Aucun résultat avec ces filtres.</div>`}
          </div></div>`}
    `;
  }

  _ligneJournal(item, postes) {
    const icone = postes.find((p) => p.id === item.type)?.icone || "mdi:wrench";
    const pieces = (item.pieces || []).map((p) => p.nom).filter(Boolean);
    return `
      <div class="ligne">
        <ha-icon icon="${esc(icone)}"></ha-icon>
        <div style="flex:1;min-width:0">
          <div class="titre-ligne">${esc(item.nom || item.type)}${
            (item.statut || "fait") === "a_faire"
              ? ` <span class="badge inconnu" style="margin-left:6px">À faire</span>`
              : ""
          }</div>
          <div class="sous">
            ${dateFr(item.date)}${item.km != null ? ` · ${km(item.km)}` : ""}${
              item.garage ? ` · ${esc(item.garage)}` : ""
            }
          </div>
          ${pieces.length ? `<div class="petit muted" style="margin-top:2px">${esc(pieces.join(" · "))}</div>` : ""}
          ${item.notes ? `<div class="petit muted" style="margin-top:2px;white-space:pre-wrap">${esc(item.notes)}</div>` : ""}
        </div>
        <div class="droite">
          ${item.cout != null ? euros(item.cout) : `<span class="petit muted">—</span>`}
        </div>
        ${(item.statut || "fait") === "a_faire"
          ? `<button class="action primaire" data-action="marquer-fait" data-id="${esc(item.id)}">Fait</button>`
          : ""}
        <button class="icone" title="Modifier" data-action="editer" data-id="${esc(item.id)}">
          <ha-icon icon="mdi:pencil"></ha-icon></button>
        <button class="icone" title="Supprimer" data-action="supprimer" data-id="${esc(item.id)}" data-nom="${esc(item.nom || item.type)}">
          <ha-icon icon="mdi:delete-outline"></ha-icon></button>
      </div>`;
  }

  // --------------------------------------------------------------- pièces
  _renduPieces() {
    const { interventions = [] } = this._data;
    const catalogue = new Map();
    for (const item of interventions) {
      for (const piece of item.pieces || []) {
        if (!piece?.nom) continue;
        const cle = `${piece.nom}||${piece.ref || ""}`.toLowerCase();
        const entree = catalogue.get(cle) || {
          nom: piece.nom,
          ref: piece.ref,
          quantite: 0,
          passages: 0,
          depense: 0,
          chiffree: false,
          dernier_prix: null,
          derniere: null,
        };
        const quantitePiece = Number(piece.qte) || 1;
        entree.quantite += quantitePiece;
        entree.passages += 1;
        const prix = piece.prix === null || piece.prix === undefined ? NaN : Number(piece.prix);
        if (Number.isFinite(prix)) {
          entree.depense += prix * quantitePiece;
          entree.chiffree = true;
          entree.dernier_prix = prix;
        }
        if (!entree.derniere || String(item.date) > String(entree.derniere.date)) {
          entree.derniere = { date: item.date, km: item.km, poste: item.nom || item.type };
        }
        catalogue.set(cle, entree);
      }
    }
    const pieces = [...catalogue.values()].sort(
      (a, b) => String(b.derniere?.date || "").localeCompare(String(a.derniere?.date || ""))
    );

    if (!pieces.length) {
      return `<div class="carte vide"><ha-icon icon="mdi:cog-outline"></ha-icon>
        <p>Aucune pièce enregistrée. Ajoute-les lors d'une intervention.</p></div>`;
    }

    return `
      <div class="entete-section"><h2>Pièces utilisées</h2>
        <span class="badge inconnu">${pieces.length}</span></div>
      <div class="carte"><div class="liste">
        ${pieces.map((piece) => `
          <div class="ligne">
            <ha-icon icon="mdi:cog-outline"></ha-icon>
            <div style="flex:1">
              <div class="titre-ligne">${esc(piece.nom)}</div>
              <div class="sous">
                ${piece.passages} passage(s)${piece.quantite ? ` · qté totale ${nombre(piece.quantite, 2)}` : ""}${
                  piece.ref ? ` · réf. ${esc(piece.ref)}` : ""
                }${piece.chiffree ? ` · dernier prix ${euros(piece.dernier_prix)}/u` : ""}
              </div>
              ${piece.chiffree ? `<div class="sous" style="margin-top:2px">Total dépensé : ${euros(piece.depense)}</div>` : ""}
              ${piece.derniere ? `<div class="petit muted">Dernier : ${dateFr(piece.derniere.date)}${
                piece.derniere.km != null ? ` à ${km(piece.derniere.km)}` : ""
              } (${esc(piece.derniere.poste)})</div>` : ""}
            </div>
          </div>`).join("")}
      </div></div>`;
  }

  // ---------------------------------------------------------------- coûts
  _renduCouts() {
    const { stats = {}, interventions = [], postes = [] } = this._data;
    if (!interventions.length) {
      return `<div class="carte vide"><ha-icon icon="mdi:cash-multiple"></ha-icon>
        <p>Pas encore de dépense enregistrée.</p></div>`;
    }
    const annees = Object.entries(stats.par_annee || {}).sort((a, b) => a[0].localeCompare(b[0]));
    const maxAnnee = Math.max(...annees.map(([, v]) => Number(v) || 0), 1);
    const types = Object.entries(stats.par_type || {})
      .map(([id, valeur]) => ({
        id,
        nom: postes.find((p) => p.id === id)?.nom
          || interventions.find((item) => item.type === id)?.nom
          || id,
        ...valeur,
      }))
      .sort((a, b) => Number(b.total) - Number(a.total));
    const maxType = Math.max(...types.map((t) => Number(t.total) || 0), 1);

    return `
      <div class="grille">
        <div class="carte"><h3>Total</h3><div class="valeur">${euros(stats.total || 0)}</div>
          <div class="petit muted">${interventions.length} intervention(s)</div></div>
        <div class="carte"><h3>Coût au km</h3><div class="valeur">${
          stats.cout_par_km != null ? `${nombre(stats.cout_par_km * 100, 2)} <small>c€/km</small>` : "—"
        }</div>
          <div class="petit muted">${stats.km_couverts ? `sur ${km(stats.km_couverts)}` : "pas assez de données"}</div></div>
        <div class="carte"><h3>Sans coût</h3><div class="valeur">${stats.sans_cout || 0}</div>
          <div class="petit muted">intervention(s) non chiffrée(s)</div></div>
      </div>

      <div class="entete-section"><h2>Par année</h2></div>
      <div class="carte">
        ${annees.map(([annee, montant]) => `
          <div class="barre-stat">
            <span class="petit" style="width:52px">${annee}</span>
            <div class="fond"><span style="width:${Math.round((Number(montant) / maxAnnee) * 100)}%"></span></div>
            <span class="montant">${euros(montant)}</span>
          </div>`).join("")}
      </div>

      <div class="entete-section"><h2>Par poste</h2></div>
      <div class="carte">
        ${types.map((type) => `
          <div class="barre-stat">
            <span class="petit" style="width:130px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(type.nom)}</span>
            <div class="fond"><span style="width:${Math.round((Number(type.total) / maxType) * 100)}%"></span></div>
            <span class="montant">${euros(type.total)} <span class="muted">(${type.count})</span></span>
          </div>`).join("")}
      </div>
      <p class="petit muted" style="margin-top:12px">
        ${stats.premiere_date ? `Du ${dateFr(stats.premiere_date)} au ${dateFr(stats.derniere_date)}. ` : ""}
        Le coût au km ne compte que les interventions chiffrées.
      </p>`;
  }

  // -------------------------------------------------------------- réglages
  _renduReglages() {
    const { vehicule = {}, postes = [], dossier, exports } = this._data;
    return `
      <div class="entete-section"><h2>Véhicule</h2></div>
      <form class="carte" id="form-vehicule">
        <div class="champs">
          <label class="champ">Nom<input name="nom" value="${esc(vehicule.nom || "")}"></label>
          <label class="champ">Marque<input name="marque" value="${esc(vehicule.marque || "")}"></label>
          <label class="champ">Modèle<input name="modele" value="${esc(vehicule.modele || "")}"></label>
          <label class="champ">Année<input name="annee" type="number" min="1900" max="2100" value="${esc(vehicule.annee ?? "")}"></label>
          <label class="champ">Moteur<input name="moteur" value="${esc(vehicule.moteur || "")}"></label>
          <label class="champ">VIN (7 derniers)<input name="vin" value="${esc(vehicule.vin || "")}"></label>
          <label class="champ">Immatriculation<input name="immatriculation" value="${esc(vehicule.immatriculation || "")}"></label>
        </div>
        <div class="pied" style="display:flex;justify-content:flex-end;margin-top:14px">
          <button class="action primaire" type="submit">Enregistrer</button>
        </div>
      </form>

      <div class="entete-section"><h2>Kilométrage</h2></div>
      <form class="carte" id="form-km">
        <div class="champs">
          <label class="champ">Kilométrage actuel
            <input name="km" type="number" min="0" step="1" value="${esc(vehicule.km_actuel ?? "")}">
          </label>
          <label class="champ">Date du relevé
            <input name="date" type="date" value="${esc(vehicule.km_maj || aujourdhui())}">
          </label>
        </div>
        <div style="display:flex;justify-content:flex-end;margin-top:14px">
          <button class="action primaire" type="submit">Mettre à jour</button>
        </div>
      </form>

      <div class="entete-section"><h2>Intervalles d'entretien</h2>
        <span class="petit muted">0 = non suivi</span></div>
      <div class="carte">
        <table class="mini">
          <thead><tr><th>Poste</th><th>km</th><th>mois</th><th>Suivi</th><th></th></tr></thead>
          <tbody>
            ${postes.map((poste) => `
              <tr data-poste="${esc(poste.id)}">
                <td><input class="petit nom" name="poste_nom" value="${esc(poste.nom)}"
                  style="width:100%;min-width:140px" aria-label="Nom du poste"></td>
                <td><input class="petit" name="poste_km" type="number" min="0" step="1000"
                  value="${esc(poste.km ?? "")}" style="width:90px"></td>
                <td><input class="petit" name="poste_mois" type="number" min="0" step="1"
                  value="${esc(poste.mois ?? "")}" style="width:70px"></td>
                <td><input type="checkbox" name="poste_actif" ${poste.actif !== false ? "checked" : ""}></td>
                <td><button class="action" type="button" data-action="sauver-poste"
                  data-poste="${esc(poste.id)}">OK</button></td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>

      <div class="entete-section"><h2>Ajouter un poste</h2>
        <span class="petit muted">Créé avec ses intervalles</span></div>
      <form class="carte" id="form-nouveau-poste">
        <div class="champs">
          <label class="champ">Libellé
            <input name="poste_nom" placeholder="Ex. Tresse de masse, recherche de panne…" autocomplete="off">
          </label>
          <label class="champ">Intervalle (km)
            <input name="poste_km" type="number" min="0" step="1000" placeholder="Facultatif">
          </label>
          <label class="champ">Intervalle (mois)
            <input name="poste_mois" type="number" min="0" step="1" placeholder="Facultatif">
          </label>
          <label class="champ">Icône
            <select name="poste_icone">
              ${ICONES_POSTE.map((entree) => `<option value="${esc(entree.id)}">${esc(entree.nom)}</option>`).join("")}
            </select>
          </label>
        </div>
        <p class="petit muted" style="margin:10px 0 0">
          Sans intervalle, le poste sert uniquement de libellé dans le journal.
        </p>
        <div style="display:flex;justify-content:flex-end;margin-top:12px">
          <button class="action primaire" type="submit">Créer le poste</button>
        </div>
      </form>

      <div class="entete-section"><h2>Export et sauvegarde</h2></div>
      <div class="carte">
        <div class="rangee" style="flex-wrap:wrap;gap:8px">
          <button class="action" data-action="exporter" data-format="csv">Exporter en CSV</button>
          <button class="action" data-action="exporter" data-format="json">Exporter en JSON</button>
          <button class="action" data-action="reload-disk">Relire les fichiers</button>
        </div>
        <div class="info-encadre" style="margin-top:14px">
          <ha-icon icon="mdi:shield-check-outline"></ha-icon>
          <div>
            Les données vivent dans <code>${esc(dossier || "/config/vehicule")}</code>,
            donc dans le dossier de configuration : elles sont incluses dans les sauvegardes
            Home Assistant (complètes et partielles « configuration »).
            Les exports sont écrits dans <code>${esc(exports || "/config/vehicule/exports")}</code>.
          </div>
        </div>
      </div>`;
  }

  // ------------------------------------------------------------- dialogue
  _renduDialogue() {
    const { form, pieces, edition } = this._dialogue;
    const postes = this._data?.postes || [];
    return `
      <div class="overlay" data-action="fermer-fond">
        <form class="boite" id="form-intervention">
          <h2>${edition ? "Modifier l'intervention" : "Nouvelle intervention"}</h2>
          <p class="petit muted" style="margin-top:0">
            ${form.statut === "a_faire"
              ? "Intervention planifiée : elle n'ouvre pas de nouvelle échéance tant qu'elle n'est pas marquée comme faite."
              : "La prochaine échéance est calculée depuis l'intervalle du poste."}
          </p>
          <div class="champs">
            <div class="champ wide">
              <span class="etiquette">Statut</span>
              <div class="segments">
                <button type="button" class="segment ${form.statut === "a_faire" ? "" : "actif"}"
                  data-action="statut" data-statut="fait">
                  <ha-icon icon="mdi:check-circle-outline"></ha-icon> Réalisée</button>
                <button type="button" class="segment ${form.statut === "a_faire" ? "actif" : ""}"
                  data-action="statut" data-statut="a_faire">
                  <ha-icon icon="mdi:clipboard-text-clock-outline"></ha-icon> À faire</button>
              </div>
            </div>
            <label class="champ">Poste
              <select name="type">
                ${postes.map((p) => `<option value="${esc(p.id)}" ${form.type === p.id ? "selected" : ""}>${esc(p.nom)}</option>`).join("")}
                <option value="${POSTE_LIBRE}" ${form.type === POSTE_LIBRE ? "selected" : ""}>Autre (saisie libre)…</option>
              </select>
            </label>
            ${form.type === POSTE_LIBRE
              ? `<label class="champ">Libellé de l'intervention
                  <input name="nom_libre" list="postes-libres" autocomplete="off"
                    placeholder="Ex. Tresse de masse, appoint d'huile…"
                    value="${esc(form.nom_libre || "")}"></label>`
              : ""}
            <datalist id="postes-libres">
              ${[...new Set((this._data?.interventions || [])
                .filter((item) => !postes.some((p) => p.id === item.type))
                .map((item) => item.nom)
                .filter(Boolean))].map((libelle) => `<option value="${esc(libelle)}"></option>`).join("")}
            </datalist>
            <label class="champ">${form.statut === "a_faire" ? "Date prévue" : "Date"}
              <input name="date" type="date" value="${esc(form.date || aujourdhui())}"></label>
            <label class="champ">${form.statut === "a_faire" ? "Km cible" : "Kilométrage"}
              <input name="km" type="number" min="0" value="${esc(form.km ?? "")}"></label>
            <label class="champ">Coût total (optionnel)
              <input name="cout" type="number" min="0" step="0.01" value="${esc(form.cout ?? "")}">
              <span class="petit muted total-pieces"></span>
            </label>
            <label class="champ">Garage / intervenant<input name="garage" value="${esc(form.garage || "")}"></label>
            <label class="champ wide">Notes<textarea name="notes">${esc(form.notes || "")}</textarea></label>
          </div>

          <h3 style="margin:16px 0 8px;font-size:14px">Pièces</h3>
          <div class="pieces-editeur">
            <div class="pieces-entete">
              <span>Désignation</span><span>Qté</span><span>Référence</span>
              <span>P.U. €</span><span class="droite">Total</span><span></span>
            </div>
            ${pieces.map((piece, index) => `
              <div class="piece-ligne" data-index="${index}">
                <input name="piece_nom" placeholder="Désignation" value="${esc(piece.nom)}">
                <input name="piece_qte" type="number" step="0.1" min="0" placeholder="Qté" value="${esc(piece.qte ?? "")}">
                <input class="ref" name="piece_ref" placeholder="Référence" value="${esc(piece.ref || "")}">
                <input class="prix" name="piece_prix" type="number" step="0.01" min="0" placeholder="P.U. €" value="${esc(piece.prix ?? "")}">
                <span class="total-piece"></span>
                <button class="icone" type="button" data-action="retirer-piece" data-index="${index}" title="Retirer">
                  <ha-icon icon="mdi:close"></ha-icon></button>
              </div>`).join("")}
            <button class="action" type="button" data-action="ajouter-piece">+ Ajouter une pièce</button>
          </div>

          ${form.statut === "a_faire" ? "" : `<details style="margin-top:16px">
            <summary class="petit muted" style="cursor:pointer">Forcer l'échéance suivante (optionnel)</summary>
            <p class="petit muted" style="margin:8px 0 0">
              Laisse vide pour laisser calculer à partir de l'intervalle du poste${
                form.suggere_km || form.suggere_date
                  ? ` — actuellement ${form.suggere_km ? km(form.suggere_km) : ""}${
                      form.suggere_km && form.suggere_date ? " / " : ""
                    }${form.suggere_date ? dateFr(form.suggere_date) : ""}`
                  : ""
              }.
            </p>
            <div class="champs" style="margin-top:10px">
              <label class="champ">Prochain km<input name="prochain_km" type="number" min="0" value="${esc(form.prochain_km ?? "")}"></label>
              <label class="champ">Prochaine date<input name="prochain_date" type="date" value="${esc(form.prochain_date || "")}"></label>
            </div>
          </details>`}

          <div class="pied">
            <button class="action" type="button" data-action="fermer">Annuler</button>
            <button class="action primaire" type="submit">${edition ? "Enregistrer" : "Ajouter"}</button>
          </div>
        </form>
      </div>`;
  }

  // ------------------------------------------------------------- gestion
  _onClick(evt) {
    const cible = evt.target.closest?.("[data-action]");
    if (!cible) return;
    const action = cible.dataset.action;

    // Clic sur le fond de l'overlay uniquement.
    if (action === "fermer-fond" && evt.target !== cible) return;

    switch (action) {
      case "onglet":
        this._allerOnglet(cible.dataset.onglet);
        break;
      case "menu":
        this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true }));
        break;
      case "recharger":
        this._charger();
        break;
      case "nouvelle":
        this._ouvrirDialogue(null, cible.dataset.type || null);
        break;
      case "editer": {
        const item = (this._data.interventions || []).find((i) => i.id === cible.dataset.id);
        if (item) this._ouvrirDialogue(item);
        break;
      }
      case "supprimer":
        this._supprimer(cible.dataset.id, cible.dataset.nom);
        break;
      case "maj-km":
        this._allerOnglet("reglages");
        break;
      case "fermer":
        this._fermerDialogue();
        break;
      case "fermer-fond":
        this._fermerDialogue();
        break;
      case "ajouter-piece":
        this._lireFormulaire();
        this._dialogue.pieces.push({ nom: "", qte: "", ref: "" });
        this._render();
        this._majTotalPieces();
        this._shadow.querySelector('.piece-ligne:last-of-type input')?.focus();
        break;
      case "retirer-piece":
        this._lireFormulaire();
        this._dialogue.pieces.splice(Number(cible.dataset.index), 1);
        if (!this._dialogue.pieces.length) this._dialogue.pieces.push({ nom: "", qte: "", ref: "" });
        this._render();
        this._majTotalPieces();
        break;
      case "sauver-poste":
        this._sauverPoste(cible.dataset.poste);
        break;
      case "statut":
        this._lireFormulaire();
        this._dialogue.form.statut = cible.dataset.statut === "a_faire" ? "a_faire" : "fait";
        this._render();
        this._majTotalPieces();
        break;
      case "marquer-fait":
        this._marquerFait(cible.dataset.id);
        break;
      case "exporter":
        this._exporter(cible.dataset.format);
        break;
      case "reload-disk":
        this._relireDisque();
        break;
      default:
        break;
    }
  }

  _onInput(evt) {
    const champ = evt.target;

    // Dans le dialogue : le changement de poste affiche/cache la saisie libre.
    if (this._dialogue) {
      if (champ?.name === "type") {
        this._lireFormulaire();
        this._render();
        this._shadow.querySelector('[name="nom_libre"]')?.focus();
        return;
      }
      if (champ?.name === "nom_libre") {
        this._dialogue.form.nom_libre = champ.value;
        return;
      }
      if (champ?.name === "piece_prix" || champ?.name === "piece_qte") {
        this._lireFormulaire();
        this._majTotalPieces();
        return;
      }
    }

    if (!champ?.dataset?.filtre) return;
    const cle = champ.dataset.filtre;
    if (cle === "q") {
      this._filtres.q = champ.value;
      clearTimeout(this._minuteurRecherche);
      this._minuteurRecherche = setTimeout(() => {
        const position = champ.selectionStart;
        this._render();
        const nouveau = this._shadow.querySelector('[data-filtre="q"]');
        nouveau?.focus();
        nouveau?.setSelectionRange?.(position, position);
      }, 250);
      return;
    }
    this._filtres[cle] = champ.value;
    this._render();
  }

  async _onSubmit(evt) {
    const formulaire = evt.target;
    if (!formulaire?.id) return;
    evt.preventDefault();

    if (formulaire.id === "form-intervention") {
      await this._enregistrerDialogue();
      return;
    }

    if (formulaire.id === "form-km") {
      const valeur = formulaire.querySelector('[name="km"]')?.value;
      const date = formulaire.querySelector('[name="date"]')?.value;
      if (valeur === "" || valeur === null) {
        this._toast("Kilométrage vide");
        return;
      }
      const ok = await this._appelerService("maj_km", {
        km: Number(valeur),
        ...(date ? { date } : {}),
      });
      if (ok !== null) this._toast("Kilométrage mis à jour");
      return;
    }

    if (formulaire.id === "form-nouveau-poste") {
      const lire = (nom) => formulaire.querySelector(`[name="${nom}"]`)?.value ?? "";
      const nom = lire("poste_nom").trim();
      if (!nom) {
        this._toast("Indique le libellé du poste");
        formulaire.querySelector('[name="poste_nom"]')?.focus();
        return;
      }
      const posteId = slugId(nom);
      if (!posteId) {
        this._toast("Libellé invalide");
        return;
      }
      if ((this._data?.postes || []).some((p) => p.id === posteId)) {
        this._toast(`Le poste « ${nom} » existe déjà`);
        return;
      }
      const kmValeur = lire("poste_km");
      const moisValeur = lire("poste_mois");
      const ok = await this._appelerService("definir_poste", {
        poste: posteId,
        nom,
        km: kmValeur === "" ? null : Number(kmValeur),
        mois: moisValeur === "" ? null : Number(moisValeur),
        icone: lire("poste_icone") || "mdi:wrench",
        actif: true,
      });
      if (ok !== null) {
        formulaire.reset();
        this._toast("Poste créé");
      }
      return;
    }

    if (formulaire.id === "form-vehicule") {
      const lire = (nom) => formulaire.querySelector(`[name="${nom}"]`)?.value ?? "";
      const annee = lire("annee");
      const donnees = {
        nom: lire("nom"),
        marque: lire("marque"),
        modele: lire("modele"),
        moteur: lire("moteur"),
        vin: lire("vin"),
        immatriculation: lire("immatriculation"),
      };
      if (annee) donnees.annee = Number(annee);
      const ok = await this._appelerService("maj_vehicule", donnees);
      if (ok !== null) this._toast("Véhicule mis à jour");
    }
  }

  async _supprimer(id, nom) {
    if (!window.confirm(`Supprimer « ${nom || id} » du journal ?\nCette action est définitive.`)) {
      return;
    }
    const ok = await this._appelerService("supprimer_intervention", { id });
    if (ok !== null) this._toast("Intervention supprimée");
  }

  async _marquerFait(id) {
    const ok = await this._appelerService("marquer_fait", { id });
    if (ok !== null) this._toast("Intervention marquée comme faite");
  }

  async _sauverPoste(posteId) {
    const ligne = [...this._shadow.querySelectorAll("tr[data-poste]")].find(
      (tr) => tr.dataset.poste === posteId
    );
    if (!ligne) return;
    const kmValeur = ligne.querySelector('[name="poste_km"]')?.value;
    const moisValeur = ligne.querySelector('[name="poste_mois"]')?.value;
    const actif = ligne.querySelector('[name="poste_actif"]')?.checked;
    const nomValeur = (ligne.querySelector('[name="poste_nom"]')?.value || "").trim();
    const donnees = {
      poste: posteId,
      km: kmValeur === "" ? null : Number(kmValeur),
      mois: moisValeur === "" ? null : Number(moisValeur),
      actif: !!actif,
    };
    // Le libellé reste facultatif : un champ vidé ne renomme rien.
    if (nomValeur) donnees.nom = nomValeur;
    const ok = await this._appelerService("definir_poste", donnees);
    if (ok !== null) this._toast(nomValeur ? "Poste et libellé enregistrés" : "Intervalle enregistré");
  }

  async _exporter(format) {
    try {
      const resultat = await this._hass.callService(
        "vehicule",
        "exporter",
        { format },
        undefined,
        true,
        true
      );
      const chemin = resultat?.response?.chemin || resultat?.chemin;
      this._toast(chemin ? `Export écrit : ${chemin}` : "Export terminé");
    } catch (err) {
      this._toast(`Export impossible : ${err?.message || err}`);
    }
  }

  async _relireDisque() {
    try {
      await this._hass.callWS({ type: "vehicule/reload" });
      await this._charger();
      this._toast("Fichiers relus");
    } catch (err) {
      this._toast(`Relecture impossible : ${err?.message || err}`);
    }
  }
}

customElements.define("vehicule-panel", VehiculePanel);
