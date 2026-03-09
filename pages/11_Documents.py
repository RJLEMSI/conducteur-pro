"""
Page 11 — Documents
Centre de gestion documentaire : documents rangés par famille puis par chantier.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
import pandas as pd
from datetime import datetime
from utils import GLOBAL_CSS, render_sidebar

st.set_page_config(page_title="Documents | ConducteurPro", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_sidebar()

# ── Données par défaut ─────────────────────────────────────────────
def _default_documents():
    return [
        # Plans
        {"chantier": "Résidence Les Lilas", "famille": "Plans", "type": "Plan", "nom": "Plan Exécution Étage 2",
         "date": "2025-01-25", "statut_doc": "Validé", "montant": 0.0, "fichier": "plan_exec_e2.pdf"},
        {"chantier": "Résidence Les Lilas", "famille": "Plans", "type": "Plan", "nom": "Plan Fondations RDC",
         "date": "2025-01-10", "statut_doc": "Validé", "montant": 0.0, "fichier": "plan_fond_rdc.pdf"},
        {"chantier": "Bureau Delta", "famille": "Plans", "type": "Plan", "nom": "Plan Électrique N1",
         "date": "2025-02-18", "statut_doc": "Validé", "montant": 0.0, "fichier": "plan_elec_n1.pdf"},
        {"chantier": "École Molière", "famille": "Plans", "type": "Plan", "nom": "Plan Masse Général",
         "date": "2025-03-05", "statut_doc": "En attente", "montant": 0.0, "fichier": "plan_masse.pdf"},
        # Métrés
        {"chantier": "Résidence Les Lilas", "famille": "Métrés", "type": "Métré", "nom": "Métré Gros Œuvre",
         "date": "2025-01-20", "statut_doc": "Validé", "montant": 0.0, "fichier": "metre_go.xlsx"},
        {"chantier": "Entrepôt LogiNord", "famille": "Métrés", "type": "Métré", "nom": "Métré Charpente Métallique",
         "date": "2025-02-15", "statut_doc": "Validé", "montant": 0.0, "fichier": "metre_charpente.xlsx"},
        {"chantier": "Bureau Delta", "famille": "Métrés", "type": "Métré", "nom": "Métré Câblage",
         "date": "2025-03-01", "statut_doc": "En attente", "montant": 0.0, "fichier": "metre_cablage.xlsx"},
        # Devis
        {"chantier": "Résidence Les Lilas", "famille": "Devis", "type": "Devis", "nom": "Devis Électricité",
         "date": "2025-02-20", "statut_doc": "En attente", "montant": 28000.0, "fichier": "devis_elec.pdf"},
        {"chantier": "Villa Méditerranée", "famille": "Devis", "type": "Devis", "nom": "Devis Piscine",
         "date": "2025-03-18", "statut_doc": "En attente", "montant": 35000.0, "fichier": "devis_piscine.pdf"},
        {"chantier": "Bureau Delta", "famille": "Devis", "type": "Devis", "nom": "Devis Menuiserie Int.",
         "date": "2025-03-22", "statut_doc": "Validé", "montant": 15600.0, "fichier": "devis_menuiserie.pdf"},
        # Documents techniques
        {"chantier": "École Molière", "famille": "Documents techniques", "type": "PPSPS", "nom": "PPSPS Mise à jour",
         "date": "2025-01-15", "statut_doc": "Validé", "montant": 0.0, "fichier": "ppsps_v2.pdf"},
        {"chantier": "Entrepôt LogiNord", "famille": "Documents techniques", "type": "DOE", "nom": "DOE Charpente Métallique",
         "date": "2025-02-28", "statut_doc": "Brouillon", "montant": 0.0, "fichier": "doe_charpente.pdf"},
        {"chantier": "Résidence Les Lilas", "famille": "Documents techniques", "type": "CCTP", "nom": "CCTP Lot Plomberie",
         "date": "2025-01-05", "statut_doc": "Validé", "montant": 0.0, "fichier": "cctp_plomberie.pdf"},
        {"chantier": "Bureau Delta", "famille": "Documents techniques", "type": "PV Réception", "nom": "PV Réception Lot 1",
         "date": "2025-03-01", "statut_doc": "Validé", "montant": 0.0, "fichier": "pv_reception_lot1.pdf"},
        # Études
        {"chantier": "École Molière", "famille": "Études", "type": "Étude", "nom": "Étude de sol G2",
         "date": "2025-02-10", "statut_doc": "Validé", "montant": 4500.0, "fichier": "etude_sol_g2.pdf"},
        {"chantier": "Résidence Les Lilas", "famille": "Études", "type": "Étude", "nom": "Étude thermique RT2020",
         "date": "2025-01-08", "statut_doc": "Validé", "montant": 3200.0, "fichier": "etude_thermique.pdf"},
        {"chantier": "Entrepôt LogiNord", "famille": "Études", "type": "Étude", "nom": "Étude structure métallique",
         "date": "2025-02-05", "statut_doc": "Validé", "montant": 6800.0, "fichier": "etude_structure.pdf"},
        # Factures
        {"chantier": "Résidence Les Lilas", "famille": "Factures", "type": "Facture", "nom": "Facture Gros-œuvre Mars",
         "date": "2025-03-15", "statut_doc": "Validé", "montant": 45000.0, "fichier": "facture_go_mars.pdf"},
        {"chantier": "Bureau Delta", "famille": "Factures", "type": "Facture", "nom": "Facture Plomberie",
         "date": "2025-03-10", "statut_doc": "Validé", "montant": 18500.0, "fichier": "facture_plomb.pdf"},
        {"chantier": "Entrepôt LogiNord", "famille": "Factures", "type": "Facture", "nom": "Facture Fondations",
         "date": "2025-03-05", "statut_doc": "Validé", "montant": 95000.0, "fichier": "facture_fond.pdf"},
        {"chantier": "École Molière", "famille": "Factures", "type": "Situation", "nom": "Situation N°3 - Mars",
         "date": "2025-03-20", "statut_doc": "En attente", "montant": 62000.0, "fichier": "situation_3.pdf"},
        # Contrats / Avenants
        {"chantier": "Villa Méditerranée", "famille": "Contrats", "type": "Contrat", "nom": "Contrat Sous-traitance Jardin",
         "date": "2025-02-10", "statut_doc": "Validé", "montant": 12000.0, "fichier": "contrat_jardin.pdf"},
        {"chantier": "Bureau Delta", "famille": "Contrats", "type": "Avenant", "nom": "Avenant N°2 Menuiserie",
         "date": "2025-03-12", "statut_doc": "En attente", "montant": 8500.0, "fichier": "avenant_2.pdf"},
    ]

if "docs_all" not in st.session_state:
    st.session_state["docs_all"] = _default_documents()

df = pd.DataFrame(st.session_state["docs_all"])
df["date"] = pd.to_datetime(df["date"])

# ── En-tête ────────────────────────────────────────────────────────
st.markdown("## 📂 Centre Documentaire")
st.caption("Documents classés par famille puis par chantier. Utilisez les filtres pour affiner la recherche.")

# ── KPIs ───────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total documents", len(df))
col2.metric("Validés", len(df[df["statut_doc"] == "Validé"]))
col3.metric("En attente", len(df[df["statut_doc"] == "En attente"]))
col4.metric("Brouillons", len(df[df["statut_doc"] == "Brouillon"]))

st.divider()

# ── Filtres globaux ────────────────────────────────────────────────
fc1, fc2, fc3 = st.columns(3)
with fc1:
    f_chantier = st.multiselect("Filtrer par chantier", options=sorted(df["chantier"].unique()), default=[])
with fc2:
    f_statut = st.multiselect("Filtrer par statut", options=sorted(df["statut_doc"].unique()), default=[])
with fc3:
    f_search = st.text_input("🔍 Recherche", placeholder="Nom du document...")

# Appliquer les filtres
filtered = df.copy()
if f_chantier:
    filtered = filtered[filtered["chantier"].isin(f_chantier)]
if f_statut:
    filtered = filtered[filtered["statut_doc"].isin(f_statut)]
if f_search:
    filtered = filtered[filtered["nom"].str.contains(f_search, case=False, na=False)]

st.markdown(f"**{len(filtered)}** document(s) trouvé(s)")
st.divider()

# ── Couleurs & Icônes ─────────────────────────────────────────────
STATUT_COLORS = {"Validé": "#4CAF50", "En attente": "#FF9800", "Brouillon": "#9E9E9E"}

FAMILLE_CONFIG = {
    "Plans":                {"icon": "📐", "color": "#3F51B5", "desc": "Plans d'exécution, plans masse, plans techniques"},
    "Métrés":               {"icon": "📏", "color": "#00897B", "desc": "Quantitatifs, métrés détaillés"},
    "Devis":                {"icon": "📝", "color": "#FF9800", "desc": "Devis clients, estimations"},
    "Documents techniques": {"icon": "🔧", "color": "#607D8B", "desc": "PPSPS, DOE, CCTP, PV de réception"},
    "Études":               {"icon": "🔬", "color": "#9C27B0", "desc": "Études de sol, thermiques, structurelles"},
    "Factures":             {"icon": "🧾", "color": "#2196F3", "desc": "Factures, situations de travaux"},
    "Contrats":             {"icon": "📄", "color": "#795548", "desc": "Contrats, avenants, marchés"},
}

# ── Affichage par famille ──────────────────────────────────────────
familles_presentes = filtered["famille"].unique()
familles_ordonnees = ["Plans", "Métrés", "Devis", "Documents techniques", "Études", "Factures", "Contrats"]
familles_affichees = [f for f in familles_ordonnees if f in familles_presentes]

for famille in familles_affichees:
    conf = FAMILLE_CONFIG.get(famille, {"icon": "📁", "color": "#666", "desc": ""})
    docs_famille = filtered[filtered["famille"] == famille]
    nb = len(docs_famille)

    # En-tête de famille
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{conf['color']}22,{conf['color']}11);
                border-left:4px solid {conf['color']};border-radius:10px;padding:14px 20px;margin:20px 0 12px;">
        <div style="display:flex;align-items:center;justify-content:space-between;">
            <div>
                <span style="font-size:1.4rem;">{conf['icon']}</span>
                <strong style="font-size:1.15rem;margin-left:10px;">{famille}</strong>
                <span style="color:#888;margin-left:12px;font-size:0.85rem;">— {conf['desc']}</span>
            </div>
            <span style="background:{conf['color']};color:#fff;padding:4px 14px;border-radius:20px;
                         font-size:0.85rem;font-weight:600;">{nb} doc(s)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Grouper par chantier
    chantiers_in_famille = sorted(docs_famille["chantier"].unique())

    for chantier in chantiers_in_famille:
        docs_ch = docs_famille[docs_famille["chantier"] == chantier].sort_values("date", ascending=False)

        with st.expander(f"🏗️ {chantier} ({len(docs_ch)} document(s))", expanded=False):
            for _, row in docs_ch.iterrows():
                color = STATUT_COLORS.get(row["statut_doc"], "#666")
                montant_str = f"{row['montant']:,.0f} €".replace(",", " ") if row["montant"] > 0 else ""
                date_str = row["date"].strftime("%d/%m/%Y")

                mc1, mc2, mc3, mc4 = st.columns([4, 2, 2, 1])
                with mc1:
                    st.markdown(f"**{row['nom']}**")
                    st.caption(f"{row['type']} · `{row['fichier']}` · {date_str}")
                with mc2:
                    if montant_str:
                        st.markdown(f"<span style='color:#4FC3F7;font-weight:600;'>{montant_str}</span>",
                                    unsafe_allow_html=True)
                with mc3:
                    st.markdown(f"<span style='background:{color};color:#fff;padding:3px 10px;border-radius:16px;"
                                f"font-size:0.8rem;'>{row['statut_doc']}</span>", unsafe_allow_html=True)
                with mc4:
                    if row["type"] in ["Facture", "Situation"]:
                        st.page_link("pages/10_Facturation.py", label="🧾", help="Voir la facturation")

                st.markdown("<hr style='margin:4px 0;border:none;border-top:1px solid #eee;'>",
                            unsafe_allow_html=True)

# ── Tableau récapitulatif ──────────────────────────────────────────
st.divider()
st.markdown("### 📋 Tableau récapitulatif")

display_df = filtered.copy()
display_df["date"] = display_df["date"].dt.strftime("%d/%m/%Y")
display_df["montant"] = display_df["montant"].apply(lambda x: f"{x:,.0f} €".replace(",", " ") if x > 0 else "—")
display_df = display_df.rename(columns={
    "famille": "Famille", "chantier": "Chantier", "type": "Type", "nom": "Document",
    "date": "Date", "statut_doc": "Statut", "montant": "Montant", "fichier": "Fichier"
})
st.dataframe(display_df[["Famille", "Chantier", "Type", "Document", "Date", "Statut", "Montant"]],
             use_container_width=True, hide_index=True)
