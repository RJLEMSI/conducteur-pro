import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
from datetime import datetime
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib import db, storage
from utils import GLOBAL_CSS

user_id = page_setup(title="Études", icon="📝")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)
require_feature(user_id, "ai_analysis")

st.title("📝 Études Techniques")
st.markdown("Générez des études techniques approfondies assistées par l'IA.")

chantier = chantier_selector(key="etudes_chantier")
if not chantier:
    st.stop()

# ─── Nouvelle étude ───────────────────────────────────────────────────────────
st.subheader("🆕 Nouvelle étude")
type_etude = st.selectbox("Type d'étude", ["Étude de sol", "Étude thermique", "Étude acoustique", "Étude structure", "Étude technique générale", "Autre"])
sujet = st.text_area("Sujet / Question", placeholder="Décrivez le sujet de l'étude ou la question technique...")

uploaded = st.file_uploader("Document de référence (optionnel)", type=["pdf", "txt", "csv"], key="etude_doc")
ref_text = ""
if uploaded:
    if uploaded.name.endswith(".pdf"):
        import pdfplumber, io
        with pdfplumber.open(io.BytesIO(uploaded.getvalue())) as pdf:
            for page in pdf.pages[:20]:
                ref_text += page.extract_text() or ""
    else:
        ref_text = uploaded.getvalue().decode("utf-8", errors="ignore")

if st.button("🤖 Générer l'étude", type="primary", disabled=not sujet):
    with st.spinner("Analyse en cours..."):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
            
            context = f"\nDocument de référence:\n{ref_text[:10000]}" if ref_text else ""
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": f"""Réalise une {type_etude} pour un chantier BTP.
Chantier: {chantier.get('nom', 'Sans nom')} - {chantier.get('adresse', '')}
Sujet: {sujet}
{context}

Structure ton analyse avec: Contexte, Analyse, Recommandations, Conclusion."""}]
            )
            result = response.content[0].text
            st.markdown("### 📊 Résultat")
            st.markdown(result)
            
            db.save_etude(user_id, chantier["id"], type_etude, f"{type_etude} - {sujet[:50]}", result)
            st.success("Étude sauvegardée.")
        except Exception as e:
            st.error("Erreur: Veuillez réessayer.")

# ─── Historique ───────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📜 Historique des études")
etudes = db.get_etudes(chantier_id=chantier["id"])
if etudes:
    for e in etudes:
        with st.expander(f"📝 {e.get('titre', 'Sans titre')} — {e.get('created_at', '')[:10]}"):
            st.markdown(e.get("contenu", ""))
            st.download_button("💾 Télécharger (.txt)", e.get("contenu", ""), file_name=f"etude_{e.get('id', '')[:8]}.txt")
else:
    st.info("Aucune étude pour ce chantier.")
