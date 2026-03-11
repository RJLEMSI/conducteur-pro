import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
from datetime import datetime
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib import db, storage
from utils import GLOBAL_CSS

user_id = page_setup(title="Analyse DCE", icon="📋")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)
require_feature(user_id, "ai_analysis")

st.title("📋 Analyse DCE")
st.markdown("Analysez automatiquement vos Dossiers de Consultation des Entreprises avec l'IA.")

chantier = chantier_selector(key="dce_chantier")
if not chantier:
    st.stop()

# ─── Upload DCE ───────────────────────────────────────────────────────────────
st.subheader("📤 Importer un DCE")
uploaded = st.file_uploader("Fichier DCE (PDF)", type=["pdf"], key="dce_upload")

if uploaded:
    # Upload vers Supabase Storage
    file_url = storage.upload_file(user_id, chantier["id"], uploaded.name, uploaded.getvalue(), "dce")
    if file_url:
        st.success(f"Fichier '{uploaded.name}' uploadé.")
    
    # Analyse IA
    if st.button("🤖 Analyser le DCE", type="primary"):
        with st.spinner("Analyse en cours..."):
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                
                import pdfplumber
                import io
                text = ""
                with pdfplumber.open(io.BytesIO(uploaded.getvalue())) as pdf:
                    for page in pdf.pages[:30]:
                        text += page.extract_text() or ""
                
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4000,
                    messages=[{"role": "user", "content": f"""Analyse ce DCE de chantier. Identifie:
1. Les lots et leur description
2. Les exigences techniques clés
3. Les dates et délais importants
4. Les points de vigilance
5. Les documents à fournir

DCE:\n{text[:15000]}"""}]
                )
                result = response.content[0].text
                st.markdown("### 📊 Résultat de l'analyse")
                st.markdown(result)
                
                # Sauvegarder
                db.save_etude(user_id, chantier["id"], "DCE", f"Analyse DCE - {uploaded.name}", result)
                st.success("Analyse sauvegardée.")
            except Exception as e:
                st.error(f"Erreur d'analyse: {e}")

# ─── Historique ───────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📜 Historique des analyses DCE")
etudes = db.get_etudes(chantier_id=chantier["id"], etude_type="DCE")
if etudes:
    for e in etudes:
        with st.expander(f"📋 {e.get('titre', 'Sans titre')} — {e.get('created_at', '')[:10]}"):
            st.markdown(e.get("contenu", ""))
else:
    st.info("Aucune analyse DCE pour ce chantier.")
