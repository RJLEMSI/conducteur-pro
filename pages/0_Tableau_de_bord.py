import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from lib.helpers import page_setup, render_saas_sidebar
from lib import db
from utils import GLOBAL_CSS

user_id = page_setup(title="Tableau de bord", icon="📊")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.title("📊 Tableau de bord")

# ─── KPIs ─────────────────────────────────────────────────────────────────────
stats = db.get_dashboard_stats(user_id)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🏗️ Chantiers", stats["nb_chantiers"], f"{stats['nb_chantiers_actifs']} actifs")
with col2:
    st.metric("📄 Devis", stats["nb_devis"], f"{stats['total_devis_ht']:,.0f} € HT")
with col3:
    st.metric("🧾 Factures", stats["nb_factures"], f"{stats['total_factures_ttc']:,.0f} € TTC")
with col4:
    st.metric("💰 Recouvrement", f"{stats['taux_recouvrement']:.0f}%", f"{stats['total_paye']:,.0f} € payés")

st.markdown("---")

# ─── Détails cliquables ───────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🏗️ Chantiers", "📄 Devis", "🧾 Factures"])

with tab1:
    chantiers = stats.get("chantiers", [])
    if chantiers:
        df = pd.DataFrame(chantiers)
        cols_display = [c for c in ["nom", "client_nom", "statut", "adresse", "created_at"] if c in df.columns]
        df_display = df[cols_display].copy() if cols_display else df.copy()
        df_display.columns = [{"nom": "Nom", "client_nom": "Client", "statut": "Statut", "adresse": "Adresse", "created_at": "Créé le"}.get(c, c) for c in df_display.columns]
        st.dataframe(df_display, use_container_width=True)
        
        # Répartition par statut
        if "statut" in df.columns:
            fig = px.pie(df, names="statut", title="Répartition par statut")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucun chantier. Créez votre premier chantier ci-dessous.")
    
    # Créer un chantier
    with st.expander("➕ Nouveau chantier"):
        with st.form("new_chantier"):
            nom = st.text_input("Nom du chantier *")
            client = st.text_input("Client")
            adresse = st.text_input("Adresse")
            submitted = st.form_submit_button("Créer")
            if submitted and nom:
                result = db.create_chantier(user_id, {"nom": nom, "client_nom": client, "adresse": adresse, "statut": "en_cours"})
                if result:
                    st.success(f"Chantier '{nom}' créé !")
                    st.rerun()
                else:
                    st.error("Erreur lors de la création.")

with tab2:
    devis = stats.get("devis", [])
    if devis:
        df = pd.DataFrame(devis)
        cols_display = [c for c in ["titre", "montant_ht", "statut", "created_at"] if c in df.columns]
        df_display = df[cols_display].copy() if cols_display else df.copy()
        df_display.columns = [{"titre": "Titre", "montant_ht": "Montant HT", "statut": "Statut", "created_at": "Créé le"}.get(c, c) for c in df_display.columns]
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("Aucun devis.")

with tab3:
    factures = stats.get("factures", [])
    if factures:
        df = pd.DataFrame(factures)
        cols_display = [c for c in ["numero", "montant_ttc", "statut", "date_echeance"] if c in df.columns]
        df_display = df[cols_display].copy() if cols_display else df.copy()
        df_display.columns = [{"numero": "N°", "montant_ttc": "Montant TTC", "statut": "Statut", "date_echeance": "Échéance"}.get(c, c) for c in df_display.columns]
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("Aucune facture.")
