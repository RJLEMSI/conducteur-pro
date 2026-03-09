import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib import db, storage
from utils import (GLOBAL_CSS, check_api_key, get_client,
                   extract_text_from_pdf, analyze_plu)

# ─── Setup ──────────────────────────────────────────────────────────────────
user_id = page_setup(title="PLU", icon="🏙️")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.markdown("## 🏙️ Analyse PLU")
st.caption("Analysez le Plan Local d'Urbanisme pour vérifier la conformité de votre projet.")

if not check_api_key():
    st.warning("⚙️ Configurez votre clé API Anthropic depuis la page d'accueil.")
    st.stop()

require_feature(user_id, "ai_analysis")

chantier = chantier_selector(key="plu_chantier")

# ─── Informations terrain / projet ───────────────────────────────────────────
st.markdown("### 📍 Informations sur le terrain et le projet")

col1, col2 = st.columns(2)
with col1:
    adresse = st.text_input("Adresse du terrain", key="plu_adresse")
    surface_terrain = st.number_input("Surface du terrain (m²)", min_value=0, value=0, key="plu_surface")
    zone_plu = st.text_input("Zone PLU (si connue)", placeholder="Ex: UA, UB, AU...", key="plu_zone")
with col2:
    type_projet = st.selectbox("Type de projet",
        ["Construction neuve", "Rénovation", "Extension", "Changement de destination", "Division parcellaire"],
        key="plu_type")
    hauteur_prevue = st.number_input("Hauteur prévue (m)", min_value=0.0, value=0.0, key="plu_hauteur")
    emprise_prevue = st.number_input("Emprise au sol prévue (m²)", min_value=0.0, value=0.0, key="plu_emprise")

description_projet = st.text_area("Description du projet",
    placeholder="Décrivez votre projet (usage, nombre de niveaux, accès, stationnement...)",
    key="plu_description")

# ─── Upload du règlement PLU ──────────────────────────────────────────────────
st.markdown("### 📄 Upload du règlement PLU")
uploaded_plu = st.file_uploader("Chargez le règlement PLU (PDF)",
                                  type=["pdf"], key="plu_upload")

plu_text = ""
if uploaded_plu:
    with st.spinner("📖 Extraction du règlement PLU..."):
        plu_text = extract_text_from_pdf(uploaded_plu)
        if plu_text:
            st.success(f"✅ {len(plu_text)} caractères extraits du PLU")
            st.session_state["plu_filename"] = uploaded_plu.name

            # Upload to Supabase Storage
            if chantier:
                pdf_bytes = uploaded_plu.getvalue()
                path = storage.upload_file(
                    user_id, chantier["id"], "documents_techniques",
                    uploaded_plu.name, pdf_bytes
                )
                if path:
                    db.create_document({
                        "nom": uploaded_plu.name,
                        "type": "Règlement PLU",
                        "famille": "Documents techniques",
                        "statut": "Importé",
                        "storage_path": path,
                        "file_size_bytes": len(pdf_bytes),
                        "chantier_id": chantier["id"],
                        "is_encrypted": True,
                    })
        else:
            st.error("Impossible d'extraire le texte du PDF.")

# ─── Contexte projet pour l'analyse ──────────────────────────────────────────
plu_context = f"""
Adresse : {adresse}
Surface terrain : {surface_terrain} m²
Zone PLU : {zone_plu}
Type de projet : {type_projet}
Hauteur prévue : {hauteur_prevue} m
Emprise au sol prévue : {emprise_prevue} m²
Description : {description_projet}
"""
st.session_state["plu_context"] = plu_context

# ─── Analyse IA ──────────────────────────────────────────────────────────────
if st.button("🚀 Analyser le PLU", use_container_width=True,
             disabled=not (plu_text and description_projet)):
    with st.spinner("🤖 Analyse du PLU et extraction des règles... (30-60 secondes)"):
        client = get_client()
        result = analyze_plu(plu_text, plu_context, client)

        if result:
            st.session_state["plu_result"] = result
            st.session_state["global_plu"] = result

            # Save to Supabase
            if chantier:
                etude_data = {
                    "titre": f"Analyse PLU — {zone_plu or adresse or 'N/A'}",
                    "type_etude": "PLU",
                    "synthese": result[:5000],
                    "chantier_id": chantier["id"],
                }
                saved = db.save_etude(etude_data)
                if saved:
                    db.log_activity("create_etude", "etude", saved.get("id", ""),
                                    {"type": "PLU", "zone": zone_plu})

            st.success("✅ Analyse PLU terminée !")

# ─── Résultat ────────────────────────────────────────────────────────────────
if st.session_state.get("plu_result"):
    st.markdown("### 📊 Résultat de l'analyse PLU")
    st.markdown(st.session_state["plu_result"])

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button("💾 Télécharger l'analyse (TXT)",
                           st.session_state["plu_result"],
                           file_name="analyse_plu.txt",
                           mime="text/plain")
    with col_dl2:
        if st.button("🗑️ Effacer l'analyse", key="clear_plu"):
            st.session_state["plu_result"] = None
            st.rerun()

# ─── Historique ──────────────────────────────────────────────────────────────
if chantier:
    st.markdown("---")
    st.markdown("### 📚 Historique des analyses PLU")
    etudes = db.get_etudes(chantier_id=chantier["id"])
    plu_etudes = [e for e in etudes if e.get("type_etude") == "PLU"]

    if plu_etudes:
        for e in plu_etudes:
            with st.expander(f"📋 {e.get('titre', 'Analyse PLU')} — {e.get('created_at', '')[:10]}"):
                st.markdown(e.get("synthese", ""))
    else:
        st.info("Aucune analyse PLU pour ce chantier.")
