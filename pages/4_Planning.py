import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib import db
from utils import GLOBAL_CSS

user_id = page_setup(title="Planning", icon="📅")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.title("📅 Planning Chantier")

chantier = chantier_selector(key="planning_chantier")
if not chantier:
    st.stop()

# ─── Étapes existantes ────────────────────────────────────────────────────────
etapes = db.get_etapes(chantier["id"])

if etapes:
    st.subheader("📊 Diagramme de Gantt")
    df = pd.DataFrame(etapes)
    
    if all(c in df.columns for c in ["nom", "date_debut", "date_fin"]):
        df["date_debut"] = pd.to_datetime(df["date_debut"])
        df["date_fin"] = pd.to_datetime(df["date_fin"])
        
        fig = px.timeline(df, x_start="date_debut", x_end="date_fin", y="nom",
                         color="statut" if "statut" in df.columns else None,
                         title=f"Planning — {chantier['nom']}")
        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("📋 Liste des étapes")
    for i, e in enumerate(etapes):
        cols = st.columns([3, 2, 2, 1, 1])
        cols[0].write(f"**{e.get('nom', 'N/A')}**")
        cols[1].write(f"📅 {e.get('date_debut', 'N/A')}")
        cols[2].write(f"→ {e.get('date_fin', 'N/A')}")
        cols[3].write(e.get("statut", "—"))
        if cols[4].button("🗑️", key=f"del_etape_{i}"):
            db.delete_etape(e["id"])
            st.rerun()
else:
    st.info("Aucune étape définie. Ajoutez-en ci-dessous.")

# ─── Ajouter une étape ────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("➕ Ajouter une étape")
with st.form("new_etape"):
    col1, col2 = st.columns(2)
    nom = col1.text_input("Nom de l'étape *")
    statut = col2.selectbox("Statut", ["À faire", "En cours", "Terminé"])
    col3, col4 = st.columns(2)
    date_debut = col3.date_input("Date de début", datetime.now())
    date_fin = col4.date_input("Date de fin", datetime.now() + timedelta(days=14))
    description = st.text_area("Description")
    ordre = st.number_input("Ordre", min_value=1, value=len(etapes) + 1)
    
    if st.form_submit_button("Ajouter") and nom:
        result = db.save_etape(user_id, chantier["id"], {
            "nom": nom, "statut": statut,
            "date_debut": date_debut.isoformat(), "date_fin": date_fin.isoformat(),
            "description": description, "ordre": ordre
        })
        if result:
            st.success(f"Étape '{nom}' ajoutée.")
            st.rerun()

# ─── Génération IA ────────────────────────────────────────────────────────────
st.markdown("---")
require_feature(user_id, "ai_analysis")
if st.button("🤖 Générer un planning IA", type="primary"):
    with st.spinner("Génération en cours..."):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
            
            response = client.messages.create(
                model="claude-sonnet-4-20250514", max_tokens=3000,
                messages=[{"role": "user", "content": f"""Génère un planning réaliste pour ce chantier BTP:
Nom: {chantier.get('nom', 'N/A')}
Adresse: {chantier.get('adresse', '')}

Donne les étapes avec nom, durée estimée, dépendances. Format: tableau markdown."""}]
            )
            st.markdown(response.content[0].text)
        except Exception as e:
            st.error(f"Erreur: {e}")
