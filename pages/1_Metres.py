import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import io
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib import db, storage
from lib.auth import check_feature
from utils import (GLOBAL_CSS, render_sidebar, check_api_key,
                   extract_text_from_pdf, pdf_first_page_to_image,
                   encode_image_bytes_to_base64, image_file_to_base64,
                   analyze_plan_image, get_client)

# ─── Setup ──────────────────────────────────────────────────────────────────
user_id = page_setup(title="Métrés", icon="📐")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.markdown("## 📐 Métrés automatiques")
st.caption("Uploadez un plan (PDF ou image), l'IA extrait les ouvrages mesurables.")

# Vérifier la clé API
if not check_api_key():
    st.warning("⚙️ Configurez votre clé API Anthropic depuis la page d'accueil.")
    st.stop()

require_feature(user_id, "ai_analysis")

# ─── Sélection du chantier ──────────────────────────────────────────────────
chantier = chantier_selector(key="metres_chantier")

# ─── Upload du plan ─────────────────────────────────────────────────────────
uploaded = st.file_uploader("📎 Charger un plan (PDF ou image)",
                            type=["pdf", "png", "jpg", "jpeg"],
                            key="metres_upload")

extra_info = st.text_area("Informations complémentaires (optionnel)",
                          placeholder="Ex: Bâtiment R+3, lot gros œuvre",
                          key="metres_info")

if uploaded:
    st.markdown("### 📄 Aperçu")

    is_pdf = uploaded.name.lower().endswith(".pdf")
    image_b64 = None
    media_type = "image/png"

    if is_pdf:
        preview_bytes = pdf_first_page_to_image(uploaded)
        st.image(preview_bytes, caption="Première page du plan", width="stretch")
        image_b64 = encode_image_bytes_to_base64(preview_bytes)
    else:
        st.image(uploaded, caption="Plan chargé", width="stretch")
        image_b64, media_type = image_file_to_base64(uploaded)

    if st.button("🚀 Analyser le plan et extraire les métrés", width="stretch"):
        with st.spinner("🔍 Analyse en cours par l'IA Claude..."):
            client = get_client()
            result = analyze_plan_image(image_b64, media_type, client, extra_info)

            if result:
                st.session_state["metres_result"] = result
                st.session_state["metres_filename"] = uploaded.name

                # Sauvegarder dans Supabase
                if chantier:
                    metre_data = {
                        "titre": f"Métrés — {uploaded.name}",
                        "ouvrages": [],  # Parsé du résultat si structuré
                        "synthese": result,
                        "chantier_id": chantier["id"],
                    }
                    saved = db.save_metre(metre_data)
                    if saved:
                        db.log_activity("create_metre", "metre", saved.get("id", ""),
                                        {"titre": uploaded.name})

                    # Upload du fichier source
                    uploaded.seek(0)
                    path = storage.upload_file(
                        file_bytes=uploaded.read(),
                        filename=uploaded.name,
                        chantier_id=chantier["id"],
                        famille="metres")
                    # Document auto-classifie par storage.upload_file()

if st.session_state.get("metres_result"):
    st.markdown("---")
    st.markdown("### 📊 Résultats des métrés")
    st.markdown(st.session_state["metres_result"])

    # Export CSV si possible
    if st.button("📥 Exporter en CSV"):
        csv_content = st.session_state["metres_result"]
        st.download_button("💾 Télécharger CSV", csv_content,
                           file_name="metres_export.csv", mime="text/csv")

# ─── Historique des métrés ──────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📜 Historique des métrés")

if chantier:
    from lib.supabase_client import get_supabase_client
    client_sb = get_supabase_client()
    if client_sb:
        try:
            result = (client_sb.table("metres")
                      .select("*")
                      .eq("user_id", user_id)
                      .eq("chantier_id", chantier["id"])
                      .order("created_at", desc=True)
                      .limit(10)
                      .execute())
            if result.data:
                for m in result.data:
                    with st.expander(f"📐 {m.get('titre', 'Sans titre')} — {m.get('created_at', '')[:10]}"):
                        st.markdown(m.get("synthese", "Pas de synthèse"))
            else:
                st.caption("Aucun métré enregistré pour ce chantier.")
        except Exception:
            st.caption("Erreur de chargement.")
else:
    st.caption("Sélectionnez un chantier pour voir l'historique.")
