"""
Page 11 — Documents
Centre de gestion documentaire : consultation, filtrage et recherche de tous les documents.
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
        {"chantier": "Résidence Les Lilas", "type": "Facture", "nom": "Facture Gros-œuvre Mars",
         "date": "2025-03-15", "statut_doc": "Validé", "montant": 45000.0, "fichier": "facture_go_mars.pdf"},
        {"chantier": "Résidence Les Lilas", "type": "Devis", "nom": "Devis Électricité",
         "date": "2025-02-20", "statut_doc": "En attente", "montant": 28000.0, "fichier": "devis_elec.pdf"},
        {"chantier": "Bureau Delta", "type": "PV Réception", "nom": "PV Réception Lot 1",
         "date": "2025-03-01", "statut_doc": "Validé", "montant": 0.0, "fichier": "pv_reception_lot1.pdf"},
        {"chantier": "Bureau Delta", "type": "Facture", "nom": "Facture Plomberie",
         "date": "2025-03-10", "statut_doc": "Validé", "montant": 18500.0, "fichier": "facture_plomb.pdf"},
        {"chantier": "École Molière", "type": "Situation", "nom": "Situation N°3 - Mars",
         "date": "2025-03-20", "statut_doc": "En attente", "montant": 62000.0, "fichier": "situation_3.pdf"},
        {"chantier": "École Molière", "type": "PPSPS", "nom": "PPSPS Mise à jour",
         "date": "2025-01-15", "statut_doc": "Validé", "montant": 0.0, "fichier": "ppsps_v2.pdf"},
        {"chantier": "Entrepôt LogiNord", "type": "DOE", "nom": "DOE Charpente Métallique",
         "date": "2025-02-28", "statut_doc": "Brouillon", "montant": 0.0, "fichier": "doe_charpente.pdf"},
        {"chantier": "Entrepôt LogiNord", "type": "Facture", "nom": "Facture Fondations",
         "date": "2025-03-05", "statut_doc": "Validé", "montant": 95000.0, "fichier": "facture_fond.pdf"},
        {"chantier": "Villa Méditerranée", "type": "Devis", "nom": "Devis Piscine",
         "date": "2025-03-18", "statut_doc": "En attente", "montant": 35000.0, "fichier": "devis_piscine.pdf"},
        {"chantier": "Villa Méditerranée", "type": "Contrat", "nom": "Contrat Sous-traitance Jardin",
         "date": "2025-02-10", "statut_doc": "Validé", "montant": 12000.0, "fichier": "contrat_jardin.pdf"},
        {"chantier": "Résidence Les Lilas", "type": "Plan", "nom": "Plan Exécution Étage 2",
         "date": "2025-01-25", "statut_doc": "Validé", "montant": 0.0, "fichier": "plan_exec_e2.pdf"},
        {"chantier": "Bureau Delta", "type": "Avenant", "nom": "Avenant N°2 Menuiserie",
         "date": "2025-03-12", "statut_doc": "En attente", "montant": 8500.0, "fichier": "avenant_2.pdf"},
    ]

if "docs_all" not in st.session_state:
    st.session_state["docs_all"] = _default_documents()

df = pd.DataFrame(st.session_state["docs_all"])
df["date"] = pd.to_datetime(df["date"])

# ── En-tête ────────────────────────────────────────────────────────
st.markdown("## 📂 Centre Documentaire")
st.caption("Consultez, filtrez et recherchez tous les documents de vos chantiers.")

# ── KPIs ───────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total documents", len(df))
col2.metric("Validés", len(df[df["statut_doc"] == "Validé"]))
col3.metric("En attente", len(df[df["statut_doc"] == "En attente"]))
col4.metric("Brouillons", len(df[df["statut_doc"] == "Brouillon"]))

st.divider()

# ── Filtres ────────────────────────────────────────────────────────
fc1, fc2, fc3, fc4 = st.columns(4)
with fc1:
    f_chantier = st.multiselect("Chantier", options=sorted(df["chantier"].unique()), default=[])
with fc2:
    f_type = st.multiselect("Type", options=sorted(df["type"].unique()), default=[])
with fc3:
    f_statut = st.multiselect("Statut", options=sorted(df["statut_doc"].unique()), default=[])
with fc4:
    f_search = st.text_input("🔍 Recherche", placeholder="Nom du document...")

# Appliquer les filtres
filtered = df.copy()
if f_chantier:
    filtered = filtered[filtered["chantier"].isin(f_chantier)]
if f_type:
    filtered = filtered[filtered["type"].isin(f_type)]
if f_statut:
    filtered = filtered[filtered["statut_doc"].isin(f_statut)]
if f_search:
    filtered = filtered[filtered["nom"].str.contains(f_search, case=False, na=False)]

filtered = filtered.sort_values("date", ascending=False)

st.markdown(f"**{len(filtered)}** document(s) trouvé(s)")

# ── Couleurs statut ────────────────────────────────────────────────
STATUT_COLORS = {
    "Validé": "#4CAF50",
    "En attente": "#FF9800",
    "Brouillon": "#9E9E9E",
}

TYPE_ICONS = {
    "Facture": "🧾",
    "Devis": "📝",
    "PV Réception": "✅",
    "Situation": "📊",
    "PPSPS": "🦺",
    "DOE": "📁",
    "Plan": "📐",
    "Contrat": "📄",
    "Avenant": "📎",
}

# ── Liste des documents ────────────────────────────────────────────
for _, row in filtered.iterrows():
    icon = TYPE_ICONS.get(row["type"], "📄")
    color = STATUT_COLORS.get(row["statut_doc"], "#666")
    montant_str = f"{row['montant']:,.0f} €".replace(",", " ") if row["montant"] > 0 else ""
    date_str = row["date"].strftime("%d/%m/%Y")

    st.markdown(f"""
    <div style="background:#1e1e2e; border-radius:12px; padding:16px 20px; margin-bottom:10px;
                border-left:4px solid {color}; display:flex; align-items:center; justify-content:space-between;">
        <div style="flex:1;">
            <span style="font-size:1.3rem;">{icon}</span>
            <strong style="color:#fff; margin-left:8px; font-size:1.05rem;">{row['nom']}</strong>
            <span style="color:#aaa; margin-left:12px; font-size:0.85rem;">{row['type']}</span>
        </div>
        <div style="text-align:right;">
            <span style="background:{color}; color:#fff; padding:3px 10px; border-radius:20px;
                         font-size:0.8rem; font-weight:600;">{row['statut_doc']}</span>
            <br/>
            <span style="color:#aaa; font-size:0.82rem;">{row['chantier']} · {date_str}</span>
            {"<br/><span style='color:#4FC3F7; font-weight:600; font-size:0.95rem;'>" + montant_str + "</span>" if montant_str else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"Détails — {row['nom']}", expanded=False):
        dc1, dc2 = st.columns(2)
        dc1.write(f"**Chantier :** {row['chantier']}")
        dc1.write(f"**Type :** {row['type']}")
        dc1.write(f"**Date :** {date_str}")
        dc2.write(f"**Statut :** {row['statut_doc']}")
        dc2.write(f"**Fichier :** `{row['fichier']}`")
        if row["montant"] > 0:
            dc2.write(f"**Montant :** {montant_str}")

        # Liens de navigation rapide
        bcol1, bcol2, bcol3 = st.columns(3)
        if row["type"] in ["Facture", "Situation"]:
            with bcol1:
                st.page_link("pages/10_Facturation.py", label="➡️ Voir Facturation", icon="🧾")
        with bcol2:
            st.page_link("pages/0_Tableau_de_bord.py", label="➡️ Tableau de bord", icon="📊")
        with bcol3:
            st.page_link("pages/4_Planning.py", label="➡️ Planning", icon="📅")

# ── Tableau récapitulatif ──────────────────────────────────────────
st.divider()
st.markdown("### 📋 Tableau récapitulatif")

display_df = filtered.copy()
display_df["date"] = display_df["date"].dt.strftime("%d/%m/%Y")
display_df["montant"] = display_df["montant"].apply(lambda x: f"{x:,.0f} €".replace(",", " ") if x > 0 else "—")
display_df = display_df.rename(columns={
    "chantier": "Chantier", "type": "Type", "nom": "Document",
    "date": "Date", "statut_doc": "Statut", "montant": "Montant", "fichier": "Fichier"
})
st.dataframe(display_df[["Chantier", "Type", "Document", "Date", "Statut", "Montant"]], use_container_width=True, hide_index=True)
