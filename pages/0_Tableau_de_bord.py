import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from lib.helpers import page_setup, render_saas_sidebar
from lib import db
from utils import GLOBAL_CSS


# Mapping statuts pour affichage
STATUT_DISPLAY = {
    "en_cours": "En cours", "termine": "Terminé", "en_attente": "En attente",
    "annule": "Annulé", "brouillon": "Brouillon", "envoye": "Envoyé",
    "envoyee": "Envoyée", "accepte": "Accepté", "refuse": "Refusé",
    "payee": "Payée", "en_retard": "En retard", "validé": "Validé",
}

def _fmt_date(val):
    if pd.isna(val) or val is None:
        return ""
    s = str(val)[:10]
    return s

def _fmt_statut(val):
    return STATUT_DISPLAY.get(str(val), str(val).replace("_", " ").capitalize())

user_id = page_setup(title="Tableau de bord", icon="📊")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.title("📊 Tableau de bord")


# ─── KPIs ─────────────────────────────────────────────────────────────────────
stats = db.get_dashboard_stats(user_id)

# Row 1: Main KPIs with clickable details
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🏗️ Chantiers", stats["nb_chantiers"], f"{stats['nb_chantiers_actifs']} actifs")
with col2:
    st.metric("📄 Devis", stats["nb_devis"], f"{stats['total_devis_ht']:,.0f} € HT")
with col3:
    st.metric("🧾 Factures", stats["nb_factures"], f"{stats['total_factures_ttc']:,.0f} € TTC")
with col4:
    st.metric("💰 Recouvrement", f"{stats['taux_recouvrement']:.0f}%", f"{stats['total_paye']:,.0f} € payés")

# Row 2: Financial summary
st.markdown("---")
col_a, col_b, col_c = st.columns(3)
with col_a:
    reste = stats.get("total_factures_ttc", 0) - stats.get("total_paye", 0)
    st.metric("💳 Reste à encaisser", f"{reste:,.0f} €")
with col_b:
    st.metric("📈 CA Total", f"{stats.get('total_paye', 0):,.0f} €")
with col_c:
    marge = stats.get("total_devis_ht", 0) - stats.get("total_factures_ttc", 0)
    st.metric("📊 Devis non facturés", f"{marge:,.0f} €")

st.markdown("---")

# ─── Détails par onglet ──────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🏗️ Chantiers", "📄 Devis", "🧾 Factures"])

with tab1:
    chantiers = stats.get("chantiers", [])
    if chantiers:
        # Filtre par statut
        statuts = list(set(c.get("statut", "") for c in chantiers))
        statuts_display = ["Tous"] + [_fmt_statut(s) for s in statuts]
        filtre = st.selectbox("Filtrer par statut", statuts_display, key="filtre_chantier")
        
        df = pd.DataFrame(chantiers)
        if filtre != "Tous":
            # Find matching raw statut
            for s in statuts:
                if _fmt_statut(s) == filtre:
                    df = df[df["statut"] == s]
                    break
        
        cols_display = [c for c in ["nom", "client_nom", "statut", "adresse", "budget_ht", "avancement_pct", "created_at"] if c in df.columns]
        df_display = df[cols_display].copy() if cols_display else df.copy()
        if "statut" in df_display.columns:
            df_display["statut"] = df_display["statut"].apply(_fmt_statut)
        if "created_at" in df_display.columns:
            df_display["created_at"] = df_display["created_at"].apply(_fmt_date)
        if "budget_ht" in df_display.columns:
            df_display["budget_ht"] = df_display["budget_ht"].apply(lambda x: f"{float(x or 0):,.0f} €" if x else "—")
        if "avancement_pct" in df_display.columns:
            df_display["avancement_pct"] = df_display["avancement_pct"].apply(lambda x: f"{float(x or 0):.0f}%" if x else "—")
        
        rename = {"nom": "Nom", "client_nom": "Client", "statut": "Statut", "adresse": "Adresse", "budget_ht": "Budget HT", "avancement_pct": "Avancement", "created_at": "Créé le"}
        df_display.columns = [rename.get(c, c) for c in df_display.columns]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Répartition par statut (pie chart)
        if "statut" in df.columns:
            fig = px.pie(df, names="statut", title="Répartition par statut", color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucun chantier. Créez votre premier chantier ci-dessous.")
    
    # Créer un chantier — formulaire amélioré
    with st.expander("➕ Nouveau chantier"):
        with st.form("new_chantier"):
            c1, c2 = st.columns(2)
            with c1:
                nom = st.text_input("Nom du chantier *")
                client = st.text_input("Client")
                adresse = st.text_input("Adresse")
            with c2:
                budget = st.number_input("Budget HT (€)", min_value=0.0, step=1000.0, value=0.0)
                metier = st.selectbox("Métier", ["Gros œuvre", "Second œuvre", "Génie civil", "Rénovation", "Extension", "Neuf", "Autre"])
                responsable = st.text_input("Responsable")
            notes = st.text_area("Notes", height=80)
            submitted = st.form_submit_button("Créer le chantier", type="primary")
            if submitted and nom:
                data = {"nom": nom, "client_nom": client, "adresse": adresse, "statut": "en_cours", "budget_ht": budget, "metier": metier, "responsable": responsable, "notes": notes}
                result = db.create_chantier(user_id, data)
                if result:
                    st.success(f"Chantier '{nom}' créé !")
                    st.rerun()
                else:
                    st.error("Erreur lors de la création.")

with tab2:
    devis = stats.get("devis", [])
    if devis:
        df = pd.DataFrame(devis)
        cols_display = [c for c in ["numero", "objet", "client_nom", "montant_ht", "statut", "created_at"] if c in df.columns]
        df_display = df[cols_display].copy() if cols_display else df.copy()
        if "statut" in df_display.columns:
            df_display["statut"] = df_display["statut"].apply(_fmt_statut)
        if "created_at" in df_display.columns:
            df_display["created_at"] = df_display["created_at"].apply(_fmt_date)
        if "montant_ht" in df_display.columns:
            df_display["montant_ht"] = df_display["montant_ht"].apply(lambda x: f"{float(x or 0):,.2f} €")
        rename = {"numero": "N°", "objet": "Objet", "client_nom": "Client", "montant_ht": "Montant HT", "statut": "Statut", "created_at": "Créé le"}
        df_display.columns = [rename.get(c, c) for c in df_display.columns]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun devis. Créez-en un depuis la page Devis.")

with tab3:
    factures = stats.get("factures", [])
    if factures:
        # Financial summary for factures
        total_ttc = sum(float(f.get("montant_ttc", 0) or 0) for f in factures)
        payees = sum(float(f.get("montant_ttc", 0) or 0) for f in factures if f.get("statut") in ("payee", "payée"))
        fc1, fc2, fc3 = st.columns(3)
        fc1.metric("Total facturé", f"{total_ttc:,.0f} €")
        fc2.metric("Payé", f"{payees:,.0f} €")
        fc3.metric("Impayé", f"{total_ttc - payees:,.0f} €")
        
        df = pd.DataFrame(factures)
        cols_display = [c for c in ["numero", "client_nom", "objet", "montant_ttc", "statut", "date_facture", "date_echeance"] if c in df.columns]
        df_display = df[cols_display].copy() if cols_display else df.copy()
        if "statut" in df_display.columns:
            df_display["statut"] = df_display["statut"].apply(_fmt_statut)
        for dc in ["date_facture", "date_echeance"]:
            if dc in df_display.columns:
                df_display[dc] = df_display[dc].apply(_fmt_date)
        if "montant_ttc" in df_display.columns:
            df_display["montant_ttc"] = df_display["montant_ttc"].apply(lambda x: f"{float(x or 0):,.2f} €")
        rename = {"numero": "N°", "client_nom": "Client", "objet": "Objet", "montant_ttc": "Montant TTC", "statut": "Statut", "date_facture": "Date", "date_echeance": "Échéance"}
        df_display.columns = [rename.get(c, c) for c in df_display.columns]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune facture. Créez-en une depuis la page Facturation.")
