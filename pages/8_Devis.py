"""
Page 8 — Générateur de devis professionnel
Sélection métier, grille de tarification, coût de revient, export PDF.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import json
import pandas as pd
from datetime import datetime
from utils import GLOBAL_CSS, render_sidebar, generate_devis_pdf, generate_devis_lots, get_client, check_api_key

st.set_page_config(
    page_title="Devis · ConducteurPro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_sidebar()

st.markdown("""
<style>
.devis-section{background:white;border:1px solid #E2EBF5;border-radius:16px;padding:1.5rem;margin-bottom:1.5rem;box-shadow:0 2px 8px rgba(0,0,0,0.04);}
.metier-card{background:white;border:2px solid #E2EBF5;border-radius:14px;padding:1.2rem;text-align:center;cursor:pointer;transition:all .2s;}
.metier-card:hover,.metier-card.selected{border-color:#1B6CA8;background:#EFF6FF;}
.metier-icon{font-size:2.2rem;}
.cost-row-mat{background:#FFF7ED;border-left:3px solid #F59E0B;}
.cost-row-mo{background:#EFF6FF;border-left:3px solid #1B6CA8;}
.total-box{background:linear-gradient(135deg,#0D3B6E,#1B6CA8);color:white;border-radius:12px;padding:1.2rem 1.5rem;text-align:right;margin-top:1rem;}
.total-box .ttc{font-size:1.6rem;font-weight:800;}
.badge-metier{display:inline-block;background:#EFF6FF;color:#0D3B6E;border:1px solid #93C5FD;border-radius:20px;padding:.2rem .8rem;font-size:.8rem;font-weight:700;}
</style>
""", unsafe_allow_html=True)

# ─── Constantes métiers ────────────────────────────────────────────────────────
METIERS = {
    "🧱 Maçon": {
        "icon": "🧱", "key": "macon",
        "unites": ["m²", "m³", "ml", "Fft", "u"],
        "materiaux_defaut": [
            {"ref": "BLK-200", "designation": "Bloc béton 20cm", "unite": "u", "prix_achat": 2.50, "coeff": 1.15},
            {"ref": "CIM-25", "designation": "Ciment CEM II 25kg", "unite": "sac", "prix_achat": 8.90, "coeff": 1.20},
            {"ref": "SAB-M", "designation": "Sable de maçonnerie (tonne)", "unite": "T", "prix_achat": 45.00, "coeff": 1.10},
            {"ref": "ARG-250", "designation": "Armature HA 250 (kg)", "unite": "kg", "prix_achat": 1.20, "coeff": 1.15},
            {"ref": "HOURD", "designation": "Hourdis 16+4", "unite": "u", "prix_achat": 3.20, "coeff": 1.15},
        ],
        "tarifs_mo": [
            {"poste": "Maçon N3", "taux_horaire": 42.0},
            {"poste": "Chef d'équipe N4", "taux_horaire": 52.0},
            {"poste": "Manœuvre", "taux_horaire": 32.0},
        ]
    },
    "🔧 Plombier": {
        "icon": "🔧", "key": "plombier",
        "unites": ["u", "ml", "Fft", "h"],
        "materiaux_defaut": [
            {"ref": "TUB-16", "designation": "Tube PER 16mm (ml)", "unite": "ml", "prix_achat": 0.85, "coeff": 1.25},
            {"ref": "TUB-20", "designation": "Tube PER 20mm (ml)", "unite": "ml", "prix_achat": 1.10, "coeff": 1.25},
            {"ref": "TUB-CU22", "designation": "Tube cuivre 22mm (ml)", "unite": "ml", "prix_achat": 5.50, "coeff": 1.20},
            {"ref": "BAL-200", "designation": "Ballon eau chaude 200L", "unite": "u", "prix_achat": 380.00, "coeff": 1.30},
            {"ref": "CHAUD", "designation": "Chaudière gaz condensation", "unite": "u", "prix_achat": 1200.00, "coeff": 1.25},
            {"ref": "RAD-500", "designation": "Radiateur acier 500W", "unite": "u", "prix_achat": 85.00, "coeff": 1.30},
            {"ref": "ROBI", "designation": "Robinet thermostatique", "unite": "u", "prix_achat": 18.00, "coeff": 1.35},
        ],
        "tarifs_mo": [
            {"poste": "Plombier N3", "taux_horaire": 48.0},
            {"poste": "Plombier-Chauffagiste N4", "taux_horaire": 58.0},
            {"poste": "Aide-plombier", "taux_horaire": 34.0},
        ]
    },
    "🪟 Carreleur": {
        "icon": "🪟", "key": "carreleur",
        "unites": ["m²", "ml", "Fft", "u"],
        "materiaux_defaut": [
            {"ref": "CARR-60", "designation": "Carrelage 60x60 grès cérame (m²)", "unite": "m²", "prix_achat": 18.00, "coeff": 1.20},
            {"ref": "CARR-30", "designation": "Carrelage sol 30x30 (m²)", "unite": "m²", "prix_achat": 12.00, "coeff": 1.20},
            {"ref": "COLLE", "designation": "Colle carrelage flex C2 (sac 25kg)", "unite": "sac", "prix_achat": 16.50, "coeff": 1.15},
            {"ref": "JOINT", "designation": "Joint carrelage (sac 5kg)", "unite": "sac", "prix_achat": 9.50, "coeff": 1.15},
            {"ref": "BAGUETTE", "designation": "Baguette d'angle alu (ml)", "unite": "ml", "prix_achat": 3.20, "coeff": 1.20},
            {"ref": "TAPIS", "designation": "Bande anti-fracture (ml)", "unite": "ml", "prix_achat": 4.50, "coeff": 1.15},
        ],
        "tarifs_mo": [
            {"poste": "Carreleur N3", "taux_horaire": 44.0},
            {"poste": "Carreleur N4", "taux_horaire": 54.0},
            {"poste": "Aide-carreleur", "taux_horaire": 32.0},
        ]
    },
    "🪚 Charpentier": {
        "icon": "🪚", "key": "charpentier",
        "unites": ["m²", "ml", "m³", "Fft", "u"],
        "materiaux_defaut": [
            {"ref": "CHEV-63", "designation": "Chevron 63x75 (ml)", "unite": "ml", "prix_achat": 3.80, "coeff": 1.15},
            {"ref": "SOLIVE", "designation": "Solive 60x160 (ml)", "unite": "ml", "prix_achat": 6.50, "coeff": 1.15},
            {"ref": "PANNE", "designation": "Panne faîtière 80x80 (ml)", "unite": "ml", "prix_achat": 8.20, "coeff": 1.15},
            {"ref": "VOLIG", "designation": "Voligeage 22mm (m²)", "unite": "m²", "prix_achat": 12.00, "coeff": 1.15},
            {"ref": "CONTREV", "designation": "Contreventement OSB 12mm (m²)", "unite": "m²", "prix_achat": 14.50, "coeff": 1.15},
            {"ref": "TUILE", "designation": "Tuile béton (u)", "unite": "u", "prix_achat": 0.85, "coeff": 1.20},
        ],
        "tarifs_mo": [
            {"poste": "Charpentier N3", "taux_horaire": 46.0},
            {"poste": "Chef d'équipe charpente", "taux_horaire": 56.0},
            {"poste": "Manœuvre", "taux_horaire": 32.0},
        ]
    },
    "⚡ Électricien": {
        "icon": "⚡", "key": "electricien",
        "unites": ["ml", "u", "Fft", "h"],
        "materiaux_defaut": [
            {"ref": "CAB-1.5", "designation": "Câble H07V-U 1,5mm² (ml)", "unite": "ml", "prix_achat": 0.45, "coeff": 1.25},
            {"ref": "CAB-2.5", "designation": "Câble H07V-U 2,5mm² (ml)", "unite": "ml", "prix_achat": 0.65, "coeff": 1.25},
            {"ref": "GAINE", "designation": "Gaine IRL 20mm (ml)", "unite": "ml", "prix_achat": 0.55, "coeff": 1.20},
            {"ref": "TABLEAU", "designation": "Tableau électrique 13 mod.", "unite": "u", "prix_achat": 65.00, "coeff": 1.30},
            {"ref": "PRISE", "designation": "Prise de courant 2P+T", "unite": "u", "prix_achat": 4.50, "coeff": 1.30},
            {"ref": "INTER", "designation": "Interrupteur va-et-vient", "unite": "u", "prix_achat": 5.20, "coeff": 1.30},
            {"ref": "SPOT", "designation": "Spot LED encastré 6W", "unite": "u", "prix_achat": 12.00, "coeff": 1.35},
        ],
        "tarifs_mo": [
            {"poste": "Électricien N3", "taux_horaire": 46.0},
            {"poste": "Électricien N4 chef d'équipe", "taux_horaire": 58.0},
            {"poste": "Aide-électricien", "taux_horaire": 33.0},
        ]
    },
    "🎨 Peintre": {
        "icon": "🎨", "key": "peintre",
        "unites": ["m²", "ml", "Fft", "u"],
        "materiaux_defaut": [
            {"ref": "PEIN-B", "designation": "Peinture blanche intérieure (L)", "unite": "L", "prix_achat": 6.50, "coeff": 1.25},
            {"ref": "SOUS-C", "designation": "Sous-couche universelle (L)", "unite": "L", "prix_achat": 7.80, "coeff": 1.20},
            {"ref": "ENDUIT", "designation": "Enduit de lissage (sac 20kg)", "unite": "sac", "prix_achat": 12.00, "coeff": 1.15},
            {"ref": "FOND", "designation": "Fond durcisseur (L)", "unite": "L", "prix_achat": 9.00, "coeff": 1.20},
            {"ref": "PAPIER", "designation": "Papier peint intissé (rouleau)", "unite": "u", "prix_achat": 18.00, "coeff": 1.30},
        ],
        "tarifs_mo": [
            {"poste": "Peintre N3", "taux_horaire": 40.0},
            {"poste": "Peintre N4", "taux_horaire": 50.0},
            {"poste": "Aide-peintre", "taux_horaire": 30.0},
        ]
    },
    "🏗️ Général / Multi-lots": {
        "icon": "🏗️", "key": "general",
        "unites": ["m²", "m³", "ml", "Fft", "u", "h", "j", "T", "kg"],
        "materiaux_defaut": [],
        "tarifs_mo": [
            {"poste": "Ouvrier qualifié N3", "taux_horaire": 42.0},
            {"poste": "Chef de chantier", "taux_horaire": 55.0},
            {"poste": "Manœuvre", "taux_horaire": 30.0},
        ]
    },
}

# ─── Init session ──────────────────────────────────────────────────────────────
if "devis_entreprise" not in st.session_state:
    st.session_state.devis_entreprise = {
        "nom": "", "siret": "", "adresse": "", "code_postal": "", "ville": "",
        "telephone": "", "email": "", "site": "", "tva_intracommunautaire": "",
        "rcs": "", "mentions": "Devis valable 30 jours. TVA sur les débits. Acompte de 30% à la commande.",
    }

if "devis_metier" not in st.session_state:
    st.session_state.devis_metier = "🏗️ Général / Multi-lots"

if "devis_lignes" not in st.session_state:
    st.session_state.devis_lignes = pd.DataFrame([
        {"designation": "Prestation à renseigner", "unite": "Fft", "quantite": 1.0,
         "prix_unitaire_ht": 0.0, "cout_mat": 0.0, "cout_mo": 0.0, "marge_pct": 30.0},
    ])

if "devis_info" not in st.session_state:
    st.session_state.devis_info = {
        "numero": f"DEV-{datetime.now().strftime('%Y%m%d')}-001",
        "date": datetime.now().strftime("%d/%m/%Y"),
        "validite": "30 jours", "objet": "",
        "client_nom": "", "client_adresse": "", "client_cp": "", "client_ville": "",
        "client_email": "", "client_tel": "",
        "tva_taux": 20.0,
        "conditions_paiement": "30% à la commande, 40% à mi-travaux, 30% à la réception",
        "notes": "",
    }

if "grille_materiaux" not in st.session_state:
    metier = st.session_state.devis_metier
    st.session_state.grille_materiaux = pd.DataFrame(
        METIERS.get(metier, METIERS["🏗️ Général / Multi-lots"])["materiaux_defaut"]
    ) if METIERS.get(metier, {}).get("materiaux_defaut") else pd.DataFrame(
        columns=["ref", "designation", "unite", "prix_achat", "coeff"]
    )

if "grille_mo" not in st.session_state:
    metier = st.session_state.devis_metier
    st.session_state.grille_mo = pd.DataFrame(
        METIERS.get(metier, METIERS["🏗️ Général / Multi-lots"])["tarifs_mo"]
    )

# Import depuis planning
planning_import = st.session_state.pop("devis_from_planning", None)
if planning_import:
    projet = planning_import.get("projet", "")
    localisation = planning_import.get("localisation", "")
    st.session_state.devis_info["objet"] = f"Travaux — {projet} — {localisation}"
    st.success(f"✅ Données importées depuis : {planning_import.get('nom', '')}")

# ─── En-tête ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h2>💰 Générateur de devis professionnel</h2>
    <p>Sélectionnez votre métier · Grille tarifaire · Coût de revient · Export PDF</p>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs([
    "🔨 Métier & Tarifs",
    "🏢 Votre entreprise",
    "👤 Client & Projet",
    "📋 Lignes du devis",
    "💸 Coût de revient",
    "👁️ Aperçu & Export",
    "📦 Tarifs Fournisseurs",
])

# ═══════════════════════════════════════════════════════════════════
# TAB 1 — SÉLECTION MÉTIER & GRILLES
# ═══════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown("### 🔨 Sélectionnez votre métier")

    cols = st.columns(4)
    metier_list = list(METIERS.keys())
    for i, m in enumerate(metier_list):
        with cols[i % 4]:
            selected = st.session_state.devis_metier == m
            bg = "background:#EFF6FF;border-color:#1B6CA8;" if selected else ""
            st.markdown(f"""
            <div class="metier-card" style="{bg}">
                <div class="metier-icon">{METIERS[m]['icon']}</div>
                <div style="font-weight:700;font-size:.9rem;color:#0D3B6E;">{m}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Sélectionner" if not selected else "✅ Sélectionné", key=f"m_{i}", use_container_width=True):
                st.session_state.devis_metier = m
                # Charger les tarifs par défaut de ce métier
                mat_def = METIERS[m]["materiaux_defaut"]
                mo_def = METIERS[m]["tarifs_mo"]
                if mat_def:
                    st.session_state.grille_materiaux = pd.DataFrame(mat_def)
                if mo_def:
                    st.session_state.grille_mo = pd.DataFrame(mo_def)
                st.rerun()

    metier_actuel = st.session_state.devis_metier
    st.markdown(f"**Métier actuel :** <span class='badge-metier'>{metier_actuel}</span>", unsafe_allow_html=True)
    st.markdown("---")

    # ─── Grille matériaux ──────────────────────────────────────────
    st.markdown("#### 🏪 Grille de tarification — Matériaux & Fournitures")
    st.markdown("""
    <div class="info-box">
    Renseignez vos <strong>prix d'achat fournisseur</strong> et le <strong>coefficient de vente</strong>
    (ex : 1.30 = marge de 30%). Le prix de vente HT est calculé automatiquement.
    Ces tarifs sont réutilisés dans le calcul du coût de revient.
    </div>
    """, unsafe_allow_html=True)

    df_mat = st.session_state.grille_materiaux.copy()
    for col in ["ref", "designation", "unite", "prix_achat", "coeff"]:
        if col not in df_mat.columns:
            df_mat[col] = "" if col in ["ref", "designation", "unite"] else 1.0

    df_mat_edit = st.data_editor(
        df_mat,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "ref": st.column_config.TextColumn("Référence", width="small"),
            "designation": st.column_config.TextColumn("Désignation matériau / fourniture", width="large"),
            "unite": st.column_config.SelectboxColumn("Unité", options=["m²","m³","ml","u","kg","T","sac","L","rouleau","Fft"], width="small"),
            "prix_achat": st.column_config.NumberColumn("Prix achat HT (€)", min_value=0, step=0.5, format="%.2f €"),
            "coeff": st.column_config.NumberColumn("Coeff. vente", min_value=1.0, max_value=5.0, step=0.05, format="%.2f",
                                                     help="1.30 = +30% de marge. Prix vente = Prix achat × Coeff."),
        },
        key="editor_mat"
    )
    st.session_state.grille_materiaux = df_mat_edit

    # Aperçu prix de vente
    if not df_mat_edit.empty and "prix_achat" in df_mat_edit.columns:
        df_mat_edit["prix_vente_ht"] = df_mat_edit["prix_achat"].fillna(0) * df_mat_edit["coeff"].fillna(1.0)
        st.markdown("**💡 Prix de vente calculés :**")
        preview = df_mat_edit[["ref", "designation", "unite", "prix_achat", "coeff", "prix_vente_ht"]].copy()
        preview.columns = ["Réf.", "Désignation", "Unité", "P. achat (€)", "Coeff.", "P. vente HT (€)"]
        st.dataframe(preview, use_container_width=True, hide_index=True)

    # Export/import grille
    c1, c2 = st.columns(2)
    with c1:
        grille_json = json.dumps(df_mat_edit.to_dict("records"), ensure_ascii=False, indent=2)
        st.download_button("💾 Exporter ma grille (.json)", data=grille_json.encode(),
                           file_name=f"grille_{metier_actuel.split()[1] if ' ' in metier_actuel else 'general'}.json",
                           mime="application/json", use_container_width=True)
    with c2:
        grille_import = st.file_uploader("📥 Importer une grille sauvegardée", type=["json"], key="grille_import")
        if grille_import:
            try:
                data = json.loads(grille_import.read().decode())
                st.session_state.grille_materiaux = pd.DataFrame(data)
                st.success("✅ Grille importée !")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")

    st.markdown("---")
    # ─── Grille main-d'œuvre ───────────────────────────────────────
    st.markdown("#### 👷 Grille main-d'œuvre")
    df_mo = st.session_state.grille_mo.copy()
    if "poste" not in df_mo.columns:
        df_mo["poste"] = ""
    if "taux_horaire" not in df_mo.columns:
        df_mo["taux_horaire"] = 40.0

    df_mo_edit = st.data_editor(
        df_mo,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "poste": st.column_config.TextColumn("Poste / Qualification", width="large"),
            "taux_horaire": st.column_config.NumberColumn("Taux horaire HT (€/h)", min_value=0, step=1.0, format="%.2f €/h"),
        },
        key="editor_mo"
    )
    st.session_state.grille_mo = df_mo_edit

# ═══════════════════════════════════════════════════════════════════
# TAB 2 — ENTREPRISE
# ═══════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown("### 🏢 Votre en-tête entreprise")
    st.markdown("""<div class="info-box">Ces informations apparaissent sur tous vos devis. Sauvegardez-les pour ne pas les ressaisir.</div>""", unsafe_allow_html=True)

    col_logo, col_infos = st.columns([1, 2])
    with col_logo:
        logo_file = st.file_uploader("🖼️ Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
        if logo_file:
            import base64 as b64mod
            st.session_state["devis_logo"] = b64mod.b64encode(logo_file.read()).decode()
            st.image(b64mod.b64decode(st.session_state["devis_logo"]), width=140)
            st.success("✅ Logo chargé !")
        elif st.session_state.get("devis_logo"):
            import base64 as b64mod
            st.image(b64mod.b64decode(st.session_state["devis_logo"]), width=140, caption="Logo actuel")

    with col_infos:
        e = st.session_state.devis_entreprise
        c1, c2 = st.columns(2)
        with c1:
            e["nom"] = st.text_input("🏢 Nom entreprise *", value=e["nom"], placeholder="MARTIN Maçonnerie SAS", key="ent_nom")
            e["siret"] = st.text_input("SIRET *", value=e["siret"], key="ent_siret")
            e["telephone"] = st.text_input("📞 Téléphone", value=e["telephone"], key="ent_tel")
            e["email"] = st.text_input("📧 Email", value=e["email"], key="ent_email")
        with c2:
            e["adresse"] = st.text_input("📍 Adresse", value=e["adresse"], key="ent_adresse")
            e["code_postal"] = st.text_input("Code postal", value=e["code_postal"], key="ent_cp")
            e["ville"] = st.text_input("Ville", value=e["ville"], key="ent_ville")
            e["site"] = st.text_input("🌐 Site web", value=e["site"], key="ent_site")

    e["rcs"] = st.text_input("RCS", value=e["rcs"], key="ent_rcs")
    e["tva_intracommunautaire"] = st.text_input("N° TVA intra", value=e["tva_intracommunautaire"], key="ent_tva_intra")
    e["mentions"] = st.text_area("Mentions légales", value=e["mentions"], height=70, key="ent_mentions")

    c1, c2 = st.columns(2)
    with c1:
        cfg_export = json.dumps({"entreprise": e, "logo": st.session_state.get("devis_logo", "")}, ensure_ascii=False)
        st.download_button("💾 Sauvegarder mon en-tête", data=cfg_export.encode(),
                           file_name="conducteurpro_entete.json", mime="application/json", use_container_width=True)
    with c2:
        cfg_imp = st.file_uploader("📥 Importer configuration", type=["json"], key="imp_entete")
        if cfg_imp:
            try:
                cfg = json.loads(cfg_imp.read().decode())
                st.session_state.devis_entreprise = cfg.get("entreprise", e)
                if cfg.get("logo"):
                    st.session_state["devis_logo"] = cfg["logo"]
                st.success("✅ Config importée !")
                st.rerun()
            except Exception as ex:
                st.error(f"Erreur : {ex}")

# ═══════════════════════════════════════════════════════════════════
# TAB 3 — CLIENT & PROJET
# ═══════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("### 👤 Client et projet")
    d = st.session_state.devis_info
    c1, c2 = st.columns(2)
    with c1:
        d["numero"] = st.text_input("📑 N° devis", value=d["numero"], key="dev_numero")
        d["date"] = st.text_input("📅 Date", value=d["date"], key="dev_date")
        d["validite"] = st.text_input("⏳ Validité", value=d["validite"], key="dev_validite")
        d["objet"] = st.text_input("📝 Objet des travaux", value=d["objet"],
                                   placeholder="Installation plomberie salle de bain — Lyon 69",
                                   key="dev_objet")
    with c2:
        d["tva_taux"] = st.number_input("TVA (%)", value=float(d["tva_taux"]),
                                         min_value=0.0, max_value=100.0, step=0.5,
                                         help="5.5% amélioration, 10% rénovation, 20% neuf",
                                         key="dev_tva")
        d["conditions_paiement"] = st.text_input("💳 Conditions paiement",
                                                  value=d["conditions_paiement"],
                                                  key="dev_conditions")

    st.markdown("#### 👤 Client")
    c1, c2 = st.columns(2)
    with c1:
        d["client_nom"] = st.text_input("Nom / Raison sociale *", value=d["client_nom"], key="cli_nom")
        d["client_adresse"] = st.text_input("Adresse chantier", value=d["client_adresse"], key="cli_adresse")
        d["client_cp"] = st.text_input("Code postal client", value=d["client_cp"], key="cli_cp")
    with c2:
        d["client_ville"] = st.text_input("Ville client", value=d["client_ville"], key="cli_ville")
        d["client_email"] = st.text_input("Email client", value=d["client_email"], key="cli_email")
        d["client_tel"] = st.text_input("Tél. client", value=d["client_tel"], key="cli_tel")
    d["notes"] = st.text_area("Notes", value=d["notes"], height=80, key="dev_notes")

# ═══════════════════════════════════════════════════════════════════
# TAB 4 — LIGNES DU DEVIS
# ═══════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("### 📋 Lignes du devis")

    c1, c2 = st.columns([1, 3])
    with c1:
        gen_btn = st.button("🤖 Générer les lots IA", use_container_width=True)
    with c2:
        proj_desc = st.text_input("Décrire le projet pour l'IA",
                                   value=st.session_state.devis_info.get("objet", ""),
                                   placeholder="Réfection salle de bain 12m² — Lyon")

    if gen_btn and proj_desc:
        if check_api_key():
            client_ai = get_client()
            with st.spinner("🤖 Génération des lots..."):
                try:
                    metier_hint = f"Métier : {st.session_state.devis_metier}. "
                    lots = generate_devis_lots(metier_hint + proj_desc, client_ai)
                    df_new = pd.DataFrame(lots)
                    for col in ["cout_mat", "cout_mo", "marge_pct"]:
                        df_new[col] = 0.0
                    df_new["marge_pct"] = 30.0
                    st.session_state.devis_lignes = df_new
                    st.success("✅ Lots générés !")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Erreur IA : {ex}")

    metier_conf = METIERS.get(st.session_state.devis_metier, METIERS["🏗️ Général / Multi-lots"])
    unites_metier = metier_conf["unites"]

    df_lignes = st.session_state.devis_lignes.copy()
    for col in ["designation", "unite", "quantite", "prix_unitaire_ht", "cout_mat", "cout_mo", "marge_pct"]:
        if col not in df_lignes.columns:
            df_lignes[col] = "" if col in ["designation", "unite"] else 0.0
    if "marge_pct" in df_lignes.columns:
        df_lignes["marge_pct"] = df_lignes["marge_pct"].fillna(30.0)

    edited = st.data_editor(
        df_lignes,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "designation": st.column_config.TextColumn("Désignation", width="large"),
            "unite": st.column_config.SelectboxColumn("Unité", options=unites_metier, width="small"),
            "quantite": st.column_config.NumberColumn("Qté", min_value=0, step=0.5, width="small"),
            "prix_unitaire_ht": st.column_config.NumberColumn("P.U. HT (€)", min_value=0, step=5.0, format="%.2f €"),
            "cout_mat": st.column_config.NumberColumn("Coût mat. (€)", min_value=0, step=5.0, format="%.2f €",
                                                       help="Coût matériaux HT pour cette ligne"),
            "cout_mo": st.column_config.NumberColumn("Coût MO (€)", min_value=0, step=5.0, format="%.2f €",
                                                      help="Coût main-d'œuvre HT pour cette ligne"),
            "marge_pct": st.column_config.NumberColumn("Marge (%)", min_value=0, max_value=200, step=1.0, format="%.0f%%"),
        },
        key="devis_editor"
    )
    st.session_state.devis_lignes = edited

    # Totaux
    df_calc = edited.copy()
    df_calc["total_ht"] = df_calc["quantite"].fillna(0) * df_calc["prix_unitaire_ht"].fillna(0)
    total_ht = df_calc["total_ht"].sum()
    tva_taux = float(st.session_state.devis_info.get("tva_taux", 20.0))
    tva_montant = total_ht * tva_taux / 100
    total_ttc = total_ht + tva_montant

    _, c_tot = st.columns([3, 1])
    with c_tot:
        st.markdown(f"""
        <div class="total-box">
            <div>Total HT : <strong>{total_ht:,.2f} €</strong></div>
            <div>TVA {tva_taux:.1f}% : <strong>{tva_montant:,.2f} €</strong></div>
            <div class="ttc">Total TTC : {total_ttc:,.2f} €</div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# TAB 5 — COÛT DE REVIENT
# ═══════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("### 💸 Analyse du coût de revient")
    st.markdown("""
    <div class="info-box">
    <strong>Coût de revient</strong> = Total coûts matériaux + Total coûts main-d'œuvre.<br>
    <strong>Marge brute</strong> = Prix de vente HT − Coût de revient.<br>
    Renseignez les coûts MO et matériaux dans l'onglet <strong>"📋 Lignes du devis"</strong>,
    ou saisissez ici le détail par matériau et poste MO.
    </div>
    """, unsafe_allow_html=True)

    col_mat, col_mo = st.columns(2)

    # ─ Détail matériaux ──────────────────────────────────────────
    with col_mat:
        st.markdown("#### 🏪 Détail matériaux utilisés")

        # Suggestion depuis la grille
        grille = st.session_state.grille_materiaux.copy()
        if not grille.empty and "designation" in grille.columns:
            refs = ["— Saisie manuelle —"] + grille["designation"].tolist()
        else:
            refs = ["— Saisie manuelle —"]

        if "detail_mat" not in st.session_state:
            st.session_state.detail_mat = pd.DataFrame(
                columns=["designation", "unite", "quantite", "prix_achat_ht", "total_achat"]
            )

        # Ajouter depuis la grille
        ref_sel = st.selectbox("Ajouter un matériau depuis la grille", refs, key="sel_mat_grille")
        if ref_sel != "— Saisie manuelle —" and not grille.empty:
            row = grille[grille["designation"] == ref_sel].iloc[0]
            qte_add = st.number_input(f"Quantité ({row.get('unite','')})", min_value=0.0, step=0.5, key="qte_add_mat")
            if st.button("➕ Ajouter à la liste", key="btn_add_mat"):
                new_row = pd.DataFrame([{
                    "designation": row.get("designation", ""),
                    "unite": row.get("unite", ""),
                    "quantite": qte_add,
                    "prix_achat_ht": row.get("prix_achat", 0),
                    "total_achat": qte_add * row.get("prix_achat", 0),
                }])
                st.session_state.detail_mat = pd.concat(
                    [st.session_state.detail_mat, new_row], ignore_index=True
                )
                st.rerun()

        df_detail_mat = st.data_editor(
            st.session_state.detail_mat,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "designation": st.column_config.TextColumn("Matériau", width="medium"),
                "unite": st.column_config.TextColumn("Unité", width="small"),
                "quantite": st.column_config.NumberColumn("Qté", min_value=0, step=0.5),
                "prix_achat_ht": st.column_config.NumberColumn("P. achat HT (€)", min_value=0, step=0.5, format="%.2f €"),
                "total_achat": st.column_config.NumberColumn("Total achat HT (€)", disabled=True, format="%.2f €"),
            },
            key="editor_detail_mat"
        )
        df_detail_mat["total_achat"] = df_detail_mat["quantite"].fillna(0) * df_detail_mat["prix_achat_ht"].fillna(0)
        st.session_state.detail_mat = df_detail_mat
        total_mat_achat = df_detail_mat["total_achat"].sum()
        st.markdown(f"**Total coût matériaux : {total_mat_achat:,.2f} €**")

    # ─ Détail MO ─────────────────────────────────────────────────
    with col_mo:
        st.markdown("#### 👷 Détail main-d'œuvre")

        grille_mo = st.session_state.grille_mo.copy()
        if not grille_mo.empty and "poste" in grille_mo.columns:
            postes = ["— Saisie manuelle —"] + grille_mo["poste"].tolist()
        else:
            postes = ["— Saisie manuelle —"]

        if "detail_mo" not in st.session_state:
            st.session_state.detail_mo = pd.DataFrame(
                columns=["poste", "nb_heures", "taux_horaire", "total_mo"]
            )

        poste_sel = st.selectbox("Ajouter un poste depuis la grille", postes, key="sel_mo_grille")
        if poste_sel != "— Saisie manuelle —" and not grille_mo.empty:
            row_mo = grille_mo[grille_mo["poste"] == poste_sel].iloc[0]
            h_add = st.number_input("Nombre d'heures", min_value=0.0, step=0.5, key="h_add_mo")
            if st.button("➕ Ajouter ce poste", key="btn_add_mo"):
                new_mo = pd.DataFrame([{
                    "poste": row_mo.get("poste", ""),
                    "nb_heures": h_add,
                    "taux_horaire": row_mo.get("taux_horaire", 40.0),
                    "total_mo": h_add * row_mo.get("taux_horaire", 40.0),
                }])
                st.session_state.detail_mo = pd.concat(
                    [st.session_state.detail_mo, new_mo], ignore_index=True
                )
                st.rerun()

        df_detail_mo = st.data_editor(
            st.session_state.detail_mo,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "poste": st.column_config.TextColumn("Poste", width="medium"),
                "nb_heures": st.column_config.NumberColumn("Heures", min_value=0, step=0.5),
                "taux_horaire": st.column_config.NumberColumn("Taux (€/h)", min_value=0, step=1.0, format="%.2f €/h"),
                "total_mo": st.column_config.NumberColumn("Total MO HT (€)", disabled=True, format="%.2f €"),
            },
            key="editor_detail_mo"
        )
        df_detail_mo["total_mo"] = df_detail_mo["nb_heures"].fillna(0) * df_detail_mo["taux_horaire"].fillna(0)
        st.session_state.detail_mo = df_detail_mo
        total_mo = df_detail_mo["total_mo"].sum()
        st.markdown(f"**Total coût main-d'œuvre : {total_mo:,.2f} €**")

    # ─ Synthèse coût de revient ───────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📊 Synthèse financière")

    df_vente = st.session_state.devis_lignes.copy()
    df_vente["total_ht"] = df_vente["quantite"].fillna(0) * df_vente["prix_unitaire_ht"].fillna(0)
    ca_ht = df_vente["total_ht"].sum()
    cout_total = total_mat_achat + total_mo
    marge_brute = ca_ht - cout_total
    taux_marge = (marge_brute / ca_ht * 100) if ca_ht > 0 else 0.0
    taux_marque = (marge_brute / cout_total * 100) if cout_total > 0 else 0.0

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("💰 CA devis HT", f"{ca_ht:,.0f} €")
    with col_s2:
        st.metric("📦 Coût de revient", f"{cout_total:,.0f} €",
                  delta=f"Mat: {total_mat_achat:,.0f}€ + MO: {total_mo:,.0f}€",
                  delta_color="off")
    with col_s3:
        color = "normal" if marge_brute >= 0 else "inverse"
        st.metric("📈 Marge brute", f"{marge_brute:,.0f} €", delta=f"{taux_marge:.1f}% du CA", delta_color=color)
    with col_s4:
        st.metric("🎯 Taux de marque", f"{taux_marque:.1f}%",
                  help="Marge / Coût de revient × 100")

    if ca_ht > 0:
        if taux_marge < 15:
            st.markdown("""<div class="warning-box">⚠️ <strong>Marge faible</strong> — Vérifiez vos prix de vente ou réduisez vos coûts.</div>""", unsafe_allow_html=True)
        elif taux_marge > 40:
            st.markdown("""<div class="success-box">✅ <strong>Excellente marge</strong> — Votre devis est bien valorisé.</div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="success-box">✅ <strong>Marge correcte</strong> — Devis équilibré.</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# TAB 6 — APERÇU & EXPORT
# ═══════════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("### 👁️ Aperçu du devis")

    entreprise = st.session_state.devis_entreprise
    devis = st.session_state.devis_info
    df_v = st.session_state.devis_lignes.copy()
    df_v["total_ht"] = df_v["quantite"].fillna(0) * df_v["prix_unitaire_ht"].fillna(0)
    total_ht = df_v["total_ht"].sum()
    tva_taux = float(devis.get("tva_taux", 20.0))
    tva_montant = total_ht * tva_taux / 100
    total_ttc = total_ht + tva_montant

    logo_html = ""
    if st.session_state.get("devis_logo"):
        logo_html = f'<img src="data:image/png;base64,{st.session_state["devis_logo"]}" style="max-height:75px;max-width:170px;object-fit:contain;">'

    lignes_html = ""
    for _, row in df_v.iterrows():
        lignes_html += f"""
        <tr>
            <td style="padding:7px 10px;border-bottom:1px solid #E2EBF5;">{row.get('designation','')}</td>
            <td style="padding:7px 10px;border-bottom:1px solid #E2EBF5;text-align:center;">{row.get('quantite',0):.1f} {row.get('unite','')}</td>
            <td style="padding:7px 10px;border-bottom:1px solid #E2EBF5;text-align:right;">{row.get('prix_unitaire_ht',0):.2f} €</td>
            <td style="padding:7px 10px;border-bottom:1px solid #E2EBF5;text-align:right;font-weight:600;">{row.get('total_ht',0):.2f} €</td>
        </tr>"""

    st.markdown(f"""
    <div style="background:white;border:1px solid #E2EBF5;border-radius:16px;padding:2.5rem;max-width:870px;margin:0 auto;font-family:Arial,sans-serif;font-size:14px;">
        <table style="width:100%;margin-bottom:2rem;"><tr>
            <td style="vertical-align:top;width:45%;">{logo_html}
                <div style="margin-top:.5rem;"><strong style="font-size:1.05rem;color:#0D3B6E;">{entreprise.get('nom','Votre entreprise')}</strong><br>
                <span style="color:#6B7280;font-size:.82rem;">{entreprise.get('adresse','')} {entreprise.get('code_postal','')} {entreprise.get('ville','')}<br>
                {entreprise.get('telephone','')} — {entreprise.get('email','')}<br>SIRET : {entreprise.get('siret','')}</span></div></td>
            <td style="vertical-align:top;text-align:right;">
                <div style="background:#0D3B6E;color:white;display:inline-block;padding:.4rem 1.4rem;border-radius:7px;font-size:1.3rem;font-weight:800;margin-bottom:.4rem;">DEVIS</div><br>
                <strong>N° {devis.get('numero','')}</strong><br>
                <span style="font-size:.82rem;color:#6B7280;">Date : {devis.get('date','')} · Validité : {devis.get('validite','')}</span>
            </td></tr></table>
        <div style="background:#F8FAFF;border:1px solid #E2EBF5;border-radius:8px;padding:.8rem 1rem;margin-bottom:1.2rem;">
            <strong style="color:#0D3B6E;">Client :</strong> <strong>{devis.get('client_nom','')}</strong>
            <span style="color:#6B7280;font-size:.82rem;"> — {devis.get('client_adresse','')} {devis.get('client_cp','')} {devis.get('client_ville','')}</span>
        </div>
        <p><strong>Objet : </strong>{devis.get('objet','')}</p>
        <table style="width:100%;border-collapse:collapse;margin-bottom:1.2rem;">
            <thead><tr style="background:#0D3B6E;color:white;">
                <th style="padding:9px 10px;text-align:left;">Désignation</th>
                <th style="padding:9px 10px;text-align:center;">Qté / Unité</th>
                <th style="padding:9px 10px;text-align:right;">P.U. HT</th>
                <th style="padding:9px 10px;text-align:right;">Total HT</th>
            </tr></thead><tbody>{lignes_html}</tbody></table>
        <table style="width:100%;margin-bottom:1.2rem;"><tr><td></td><td style="width:230px;">
            <table style="width:100%;">
                <tr><td style="color:#6B7280;padding:3px 0;">Total HT :</td><td style="text-align:right;font-weight:600;">{total_ht:,.2f} €</td></tr>
                <tr><td style="color:#6B7280;padding:3px 0;">TVA {tva_taux:.1f}% :</td><td style="text-align:right;font-weight:600;">{tva_montant:,.2f} €</td></tr>
                <tr style="background:#0D3B6E;color:white;">
                    <td style="padding:7px 10px;font-weight:700;border-radius:6px 0 0 6px;">TOTAL TTC :</td>
                    <td style="padding:7px 10px;text-align:right;font-size:1.1rem;font-weight:800;border-radius:0 6px 6px 0;">{total_ttc:,.2f} €</td>
                </tr></table></td></tr></table>
        <div style="font-size:.8rem;color:#6B7280;border-top:1px solid #E2EBF5;padding-top:.8rem;">
            <strong>Conditions :</strong> {devis.get('conditions_paiement','')}<br>{devis.get('notes','')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📄 Générer le PDF", use_container_width=True, type="primary"):
            with st.spinner("Génération PDF..."):
                try:
                    pdf_bytes = generate_devis_pdf(
                        entreprise=st.session_state.devis_entreprise,
                        devis=st.session_state.devis_info,
                        lignes=st.session_state.devis_lignes,
                        logo_b64=st.session_state.get("devis_logo"),
                    )
                    nom = f"Devis_{devis.get('numero','').replace('-','_')}_{devis.get('client_nom','').replace(' ','_')}.pdf"
                    st.download_button("⬇️ Télécharger le PDF", data=pdf_bytes, file_name=nom,
                                       mime="application/pdf", use_container_width=True)
                    st.success("✅ PDF prêt !")
                except Exception as ex:
                    st.error(f"Erreur PDF : {ex}")
    with c2:
        export_full = {
            "metier": st.session_state.devis_metier,
            "entreprise": st.session_state.devis_entreprise,
            "devis": st.session_state.devis_info,
            "lignes": st.session_state.devis_lignes.to_dict("records"),
            "grille_materiaux": st.session_state.grille_materiaux.to_dict("records"),
            "grille_mo": st.session_state.grille_mo.to_dict("records"),
        }
        st.download_button("📊 Exporter tout (JSON)", data=json.dumps(export_full, ensure_ascii=False, indent=2).encode(),
                           file_name=f"devis_{devis.get('numero','')}.json", mime="application/json", use_container_width=True)

# ═══════════════════════════════════════════════════════════════════
# TAB 7 — TARIFS FOURNISSEURS
# ═══════════════════════════════════════════════════════════════════
with tabs[6]:
    st.markdown("### 📦 Tarifs Fournisseurs")
    st.markdown("""
    <div class="info-box">
    📄 Importez un <strong>catalogue PDF fournisseur</strong> — l'IA extrait automatiquement les produits,
    références et prix. Gérez et mettez à jour votre base de prix pour les réutiliser directement
    dans vos grilles de devis.
    </div>
    """, unsafe_allow_html=True)

    # ── Init ─────────────────────────────────────────────────────────────────
    if "tarifs_fournisseurs" not in st.session_state:
        st.session_state.tarifs_fournisseurs = pd.DataFrame(
            columns=["fournisseur", "ref", "designation", "unite", "prix_achat_ht", "derniere_maj"]
        )
    if "_extracted_tarifs" not in st.session_state:
        st.session_state._extracted_tarifs = None

    UNITES_OPTIONS = ["m²", "m³", "ml", "u", "kg", "T", "sac", "L", "rouleau", "Fft", "h", "j"]

    # ── Section import PDF ────────────────────────────────────────────────────
    col_upload, col_help = st.columns([3, 2])

    with col_upload:
        st.markdown("#### 📄 Importer un catalogue fournisseur")
        fournisseur_nom = st.text_input(
            "Nom du fournisseur", placeholder="Point.P, Brico Dépôt, Kiloutou, Saint-Gobain...",
            key="four_nom"
        )
        pdf_catalog = st.file_uploader("📥 Catalogue PDF (tarifs, bordereau de prix...)", type=["pdf"], key="pdf_catalog")

        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            extract_btn = st.button("🤖 Extraire les prix avec l'IA", use_container_width=True,
                                    key="btn_extract_pdf", type="primary",
                                    disabled=(not pdf_catalog or not fournisseur_nom))
        with c_btn2:
            manual_btn = st.button("➕ Saisie manuelle", use_container_width=True, key="btn_add_manual_four")

        if manual_btn:
            new_row = pd.DataFrame([{
                "fournisseur": fournisseur_nom or "—",
                "ref": "", "designation": "", "unite": "u",
                "prix_achat_ht": 0.0,
                "derniere_maj": datetime.now().strftime("%d/%m/%Y"),
            }])
            st.session_state.tarifs_fournisseurs = pd.concat(
                [st.session_state.tarifs_fournisseurs, new_row], ignore_index=True
            )
            st.rerun()

        if extract_btn and pdf_catalog and fournisseur_nom:
            if check_api_key():
                with st.spinner("📖 Lecture du PDF..."):
                    try:
                        import pdfplumber
                        all_text = []
                        with pdfplumber.open(pdf_catalog) as pdf_doc:
                            for page in pdf_doc.pages[:30]:
                                t = page.extract_text()
                                if t:
                                    all_text.append(t)
                                # Also extract tables
                                for table in page.extract_tables():
                                    for row in table:
                                        if row:
                                            all_text.append(" | ".join(str(c) for c in row if c))
                        raw_text = "\n".join(all_text)[:60000]
                    except Exception as ex:
                        st.error(f"Erreur lecture PDF : {ex}")
                        raw_text = ""

                if raw_text:
                    with st.spinner("🤖 Extraction des prix par l'IA (30-60s)..."):
                        try:
                            client_ai = get_client()
                            prompt = f"""Tu es un expert en tarification BTP. Analyse ce catalogue fournisseur et extrait TOUS les produits/articles avec leurs prix.

Fournisseur : {fournisseur_nom}

Réponds UNIQUEMENT avec un tableau JSON valide, sans markdown, sans explication.
Format EXACT :
[
  {{"ref": "REF001", "designation": "Béton prêt à l'emploi B25", "unite": "m³", "prix_achat_ht": 95.50}},
  {{"ref": "REF002", "designation": "Sable 0/4 en sac 25kg", "unite": "sac", "prix_achat_ht": 4.90}}
]

Règles :
- Inclure TOUS les produits visibles (même sans référence, mettre "—")
- Prix en euros HT décimaux (ex: 12.50)
- Unités standards : m², m³, ml, u, kg, T, sac, L, rouleau, Fft, h
- Si prix non trouvé, mettre 0
- Maximum 200 produits

CATALOGUE À ANALYSER :
{raw_text}"""

                            response = client_ai.messages.create(
                                model="claude-opus-4-5",
                                max_tokens=6000,
                                messages=[{"role": "user", "content": prompt}]
                            )
                            result_text = response.content[0].text.strip()
                            # Clean markdown fences
                            if "```" in result_text:
                                parts = result_text.split("```")
                                for part in parts:
                                    p = part.strip()
                                    if p.startswith("json"):
                                        p = p[4:]
                                    if p.startswith("["):
                                        result_text = p
                                        break
                            result_text = result_text.strip()
                            if result_text.startswith("["):
                                new_items = json.loads(result_text)
                                df_new = pd.DataFrame(new_items)
                                df_new["fournisseur"] = fournisseur_nom
                                df_new["derniere_maj"] = datetime.now().strftime("%d/%m/%Y")
                                for col in ["ref", "designation", "unite", "prix_achat_ht", "fournisseur", "derniere_maj"]:
                                    if col not in df_new.columns:
                                        df_new[col] = ""
                                st.session_state._extracted_tarifs = df_new
                                st.success(f"✅ {len(new_items)} produits extraits du catalogue {fournisseur_nom} !")
                            else:
                                st.error("L'IA n'a pas renvoyé un format JSON valide. Essayez avec un PDF mieux structuré.")
                        except Exception as ex:
                            st.error(f"Erreur extraction IA : {ex}")

    with col_help:
        st.markdown("#### ℹ️ Comment ça marche")
        st.markdown("""
        **3 étapes simples :**

        1. 🏷️ **Nommez le fournisseur** (Point.P, Kiloutou...)
        2. 📄 **Uploadez le PDF** de son catalogue / bordereau de prix
        3. 🤖 **L'IA extrait** automatiquement tous les produits et prix

        **Puis :**
        - ✅ Vérifiez et corrigez le tableau extrait
        - 💾 Sauvegardez dans votre base de prix
        - 🔄 Utilisez ces prix directement dans vos devis

        **Formats acceptés :**
        Catalogues PDF, bordereaux de prix, listes tarifaires, devis fournisseurs
        """)

        if not st.session_state.tarifs_fournisseurs.empty:
            nb_tarifs = len(st.session_state.tarifs_fournisseurs)
            fournisseurs_uniq = st.session_state.tarifs_fournisseurs["fournisseur"].nunique()
            st.markdown(f"""
            <div class="success-box">
            📦 <strong>{nb_tarifs} références</strong> de <strong>{fournisseurs_uniq} fournisseur(s)</strong> dans votre base
            </div>
            """, unsafe_allow_html=True)

    # ── Validation des tarifs extraits ────────────────────────────────────────
    if st.session_state._extracted_tarifs is not None and not st.session_state._extracted_tarifs.empty:
        st.markdown("---")
        st.markdown(f"#### ✅ {len(st.session_state._extracted_tarifs)} produits extraits — Vérifiez avant import")

        df_ext_edit = st.data_editor(
            st.session_state._extracted_tarifs,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_extracted_tarifs",
            column_config={
                "fournisseur": st.column_config.TextColumn("Fournisseur", width="small"),
                "ref": st.column_config.TextColumn("Référence", width="small"),
                "designation": st.column_config.TextColumn("Désignation", width="large"),
                "unite": st.column_config.SelectboxColumn("Unité", options=UNITES_OPTIONS, width="small"),
                "prix_achat_ht": st.column_config.NumberColumn("Prix achat HT (€)", min_value=0, step=0.1, format="%.2f €"),
                "derniere_maj": st.column_config.TextColumn("MAJ", width="small"),
            }
        )

        c_v1, c_v2, c_v3 = st.columns(3)
        with c_v1:
            if st.button("💾 Ajouter à ma base de prix", type="primary", use_container_width=True, key="btn_save_extracted"):
                existing = st.session_state.tarifs_fournisseurs
                combined = pd.concat([existing, df_ext_edit], ignore_index=True)
                # Deduplicate on fournisseur+ref, keep newest
                combined = combined.drop_duplicates(subset=["fournisseur", "ref"], keep="last")
                st.session_state.tarifs_fournisseurs = combined
                st.session_state._extracted_tarifs = None
                st.success(f"✅ {len(df_ext_edit)} produits importés dans votre base !")
                st.rerun()
        with c_v2:
            csv_ext = df_ext_edit.to_csv(index=False).encode("utf-8")
            st.download_button("📊 Télécharger CSV", data=csv_ext,
                               file_name=f"tarifs_{fournisseur_nom or 'export'}.csv",
                               mime="text/csv", use_container_width=True, key="dl_extracted_csv")
        with c_v3:
            if st.button("🗑️ Annuler", use_container_width=True, key="btn_cancel_extracted"):
                st.session_state._extracted_tarifs = None
                st.rerun()

    # ── Base de prix fournisseurs ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🗄️ Ma base de prix fournisseurs")

    if st.session_state.tarifs_fournisseurs.empty:
        st.info("📋 Aucun tarif fournisseur. Importez un catalogue PDF ou ajoutez manuellement ci-dessus.")
    else:
        # Filtres
        cf1, cf2, cf3 = st.columns([1, 2, 1])
        with cf1:
            four_list = ["Tous"] + sorted(st.session_state.tarifs_fournisseurs["fournisseur"].dropna().unique().tolist())
            filt_four = st.selectbox("Fournisseur", four_list, key="filt_fournisseur")
        with cf2:
            search_term = st.text_input("🔍 Rechercher", placeholder="béton, câble, tube...", key="search_tarif")
        with cf3:
            st.markdown("<div style='margin-top:1.6rem;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Utiliser dans grille devis", use_container_width=True, key="btn_use_in_devis"):
                df_to_use = st.session_state.tarifs_fournisseurs.copy()
                df_to_use["coeff"] = 1.30
                df_to_use = df_to_use.rename(columns={"ref": "ref", "designation": "designation",
                                                        "unite": "unite", "prix_achat_ht": "prix_achat"})
                keep_cols = ["ref", "designation", "unite", "prix_achat", "coeff"]
                for col in keep_cols:
                    if col not in df_to_use.columns:
                        df_to_use[col] = ""
                st.session_state.grille_materiaux = pd.concat(
                    [st.session_state.grille_materiaux, df_to_use[keep_cols]], ignore_index=True
                ).drop_duplicates(subset=["ref"], keep="last")
                st.success("✅ Prix intégrés dans la grille Métier & Tarifs !")

        # Filter data
        df_show = st.session_state.tarifs_fournisseurs.copy()
        if filt_four != "Tous":
            df_show = df_show[df_show["fournisseur"] == filt_four]
        if search_term:
            mask = (df_show["designation"].str.contains(search_term, case=False, na=False) |
                    df_show["ref"].str.contains(search_term, case=False, na=False))
            df_show = df_show[mask]

        st.markdown(f"**{len(df_show)} références affichées**")
        df_four_edit = st.data_editor(
            df_show,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_tarifs_fournisseurs",
            column_config={
                "fournisseur": st.column_config.TextColumn("Fournisseur", width="small"),
                "ref": st.column_config.TextColumn("Référence", width="small"),
                "designation": st.column_config.TextColumn("Désignation", width="large"),
                "unite": st.column_config.SelectboxColumn("Unité", options=UNITES_OPTIONS, width="small"),
                "prix_achat_ht": st.column_config.NumberColumn("Prix achat HT (€)", min_value=0, step=0.1, format="%.2f €"),
                "derniere_maj": st.column_config.TextColumn("MAJ", width="small"),
            }
        )

        cs1, cs2, cs3 = st.columns(3)
        with cs1:
            if st.button("💾 Sauvegarder modifications", type="primary", use_container_width=True, key="save_tarifs_four"):
                # Merge edited rows back into full dataset
                if filt_four != "Tous" or search_term:
                    # Replace edited rows in the full df (by index)
                    full_df = st.session_state.tarifs_fournisseurs.copy()
                    full_df.update(df_four_edit)
                    st.session_state.tarifs_fournisseurs = full_df
                else:
                    st.session_state.tarifs_fournisseurs = df_four_edit
                st.success("✅ Base de prix mise à jour !")
        with cs2:
            csv_all = st.session_state.tarifs_fournisseurs.to_csv(index=False).encode("utf-8")
            st.download_button("📊 Exporter tout (CSV)", data=csv_all,
                               file_name="tarifs_fournisseurs.csv",
                               mime="text/csv", use_container_width=True, key="export_all_csv")
        with cs3:
            json_imp = st.file_uploader("📥 Importer CSV", type=["csv"], key="import_four_csv")
            if json_imp:
                try:
                    df_imp = pd.read_csv(json_imp)
                    st.session_state.tarifs_fournisseurs = pd.concat(
                        [st.session_state.tarifs_fournisseurs, df_imp], ignore_index=True
                    ).drop_duplicates(subset=["fournisseur", "ref"], keep="last")
                    st.success(f"✅ {len(df_imp)} références importées !")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Erreur import : {ex}")
