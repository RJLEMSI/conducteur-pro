import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import json
from datetime import datetime
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib import db
from utils import GLOBAL_CSS

user_id = page_setup(title="Devis", icon="💰")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.title("💰 Devis")

chantier = chantier_selector(key="devis_chantier")
if not chantier:
    st.stop()

# ─── Nouveau devis ────────────────────────────────────────────────────────────
st.subheader("🆕 Créer un devis")
with st.form("new_devis"):
    titre = st.text_input("Titre du devis *")
    col1, col2 = st.columns(2)
    montant_ht = col1.number_input("Montant HT (€)", min_value=0.0, step=100.0)
    tva = col2.selectbox("TVA", [20.0, 10.0, 5.5, 0.0])
    montant_ttc = montant_ht * (1 + tva / 100)
    st.info(f"Montant TTC: **{montant_ttc:,.2f} €**")
    
    statut = st.selectbox("Statut", ["Brouillon", "Envoyé", "Accepté", "Refusé"])
    description = st.text_area("Description / Détails")
    
    if st.form_submit_button("Créer le devis") and titre:
        # Auto-générer le numéro de devis
        existing = db.get_devis(user_id=user_id)
        next_num = len(existing) + 1
        numero = f"DEV-{datetime.now().strftime('%Y')}-{next_num:03d}"
        result = db.save_devis(user_id, chantier["id"], {
            "numero": numero,
            "objet": titre,
            "client_nom": chantier.get("client_nom", ""),
            "montant_ht": montant_ht,
            "tva_pct": tva,
            "montant_ttc": montant_ttc,
            "statut": statut.lower().replace("é", "e"),
            "date_devis": datetime.now().strftime("%Y-%m-%d"),
        })
        if result:
            st.success(f"Devis '{titre}' créé ({montant_ttc:,.2f} € TTC)")
            st.rerun()

# ─── Génération IA ────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🤖 Devis assisté par IA")
require_feature(user_id, "ai_analysis")

metres = db.get_metres(chantier["id"])
desc_travaux = st.text_area("Description des travaux", placeholder="Décrivez les travaux pour lesquels vous souhaitez un devis...")

if st.button("Générer un devis IA", type="primary", disabled=not desc_travaux):
    with st.spinner("Génération..."):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
            
            metres_ctx = json.dumps(metres[:5], indent=2, default=str) if metres else "Aucun métré"
            response = client.messages.create(
                model="claude-sonnet-4-20250514", max_tokens=3000,
                messages=[{"role": "user", "content": f"""Génère un devis détaillé pour ces travaux BTP:
Chantier: {chantier.get('nom', 'N/A')}
Travaux: {desc_travaux}
Métrés disponibles: {metres_ctx}

Format: tableau avec Poste, Désignation, Unité, Quantité, PU HT, Total HT. Termine par le total général."""}]
            )
            st.markdown(response.content[0].text)
        except Exception as e:
            st.error(f"Erreur: {e}")

# ─── Liste devis existants ────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Devis existants")
devis = db.get_devis(chantier_id=chantier["id"])
if devis:
    for d in devis:
        status_icon = {"brouillon": "📝", "envoye": "📤", "accepte": "✅", "refuse": "❌", "Brouillon": "📝", "Envoyé": "📤", "Accepté": "✅", "Refusé": "❌"}.get(d.get("statut", ""), "📄")
        with st.expander(f"{status_icon} {d.get('objet', d.get('titre', 'N/A'))} — {d.get('montant_ttc', 0):,.2f} € TTC"):
            st.write(f"**Statut:** {d.get('statut', 'N/A')}")
            st.write(f"**Montant HT:** {d.get('montant_ht', 0):,.2f} €")
            st.write(f"**TVA:** {d.get('tva', 20)}%")
            st.write(f"**Date:** {d.get('created_at', '')[:10]}")
            if d.get("description"):
                st.markdown(d["description"])
else:
    st.info("Aucun devis pour ce chantier.")
