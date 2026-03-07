"""
Page 1 — Métrés automatiques depuis un plan (PDF ou image)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import io
from utils import (
    GLOBAL_CSS, render_sidebar, get_client, check_api_key,
    pdf_first_page_to_image, image_file_to_base64,
    encode_image_bytes_to_base64, analyze_plan_image
)

# ─── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Métrés · ConducteurPro",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_sidebar()

# ─── En-tête ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h2>📐 Métrés automatiques</h2>
    <p>Uploadez un plan PDF ou une photo de plan — l'IA analyse et génère le tableau de métrés en secondes</p>
</div>
""", unsafe_allow_html=True)

# ─── Colonnes principal / infos ───────────────────────────────────────────────
col_main, col_info = st.columns([3, 1])

with col_info:
    st.markdown("""
    <div class="info-box">
        <strong>📌 Formats acceptés</strong><br>
        • PDF (plan technique)<br>
        • JPG / PNG (photo de plan)<br>
        • Scan de plan papier<br><br>
        <strong>💡 Conseils</strong><br>
        • Plan avec cartouche = meilleure précision<br>
        • Évitez les plans trop flous<br>
        • 1 plan par analyse
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <strong>⚠️ Limite actuelle</strong><br>
        L'IA analyse la 1ère page du PDF ou l'image complète. Pour un plan multi-pages, analysez page par page.
    </div>
    """, unsafe_allow_html=True)

with col_main:
    # ─── Upload ───────────────────────────────────────────────────────────────
    uploaded_file = st.file_uploader(
        "📂 Glissez-déposez votre plan ici",
        type=["pdf", "jpg", "jpeg", "png"],
        help="PDF ou image d'un plan de construction"
    )

    extra_info = st.text_area(
        "Informations complémentaires (optionnel)",
        placeholder="Ex : Maison individuelle R+1, surface totale estimée 120m², plan de masse niveau RDC...",
        height=80
    )

    # ─── Aperçu du fichier uploadé ────────────────────────────────────────────
    if uploaded_file:
        file_type = uploaded_file.type

        if file_type == "application/pdf":
            st.info(f"📄 PDF chargé : **{uploaded_file.name}** — Analyse de la 1ère page")
            with st.spinner("Conversion de la première page..."):
                img_bytes = pdf_first_page_to_image(uploaded_file)
            if img_bytes:
                st.image(img_bytes, caption="Aperçu — Page 1 du plan", use_container_width=True)
                image_b64 = encode_image_bytes_to_base64(img_bytes)
                media_type = "image/png"
            else:
                st.error("Impossible de convertir le PDF en image.")
                st.stop()
        else:
            st.image(uploaded_file, caption=f"Plan chargé : {uploaded_file.name}", use_container_width=True)
            uploaded_file.seek(0)
            image_b64, media_type = image_file_to_base64(uploaded_file)

        st.markdown("---")

        # ─── Bouton d'analyse ─────────────────────────────────────────────────
        if st.button("🚀 Lancer l'analyse des métrés", use_container_width=True):
            if not check_api_key():
                st.stop()

            client = get_client()
            with st.spinner("🤖 L'IA analyse le plan... (30-60 secondes)"):
                try:
                    result = analyze_plan_image(image_b64, media_type, client, extra_info)
                    st.session_state["metres_result"] = result
                    st.session_state["metres_filename"] = uploaded_file.name
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse : {e}")
                    st.stop()

# ─── Résultats ────────────────────────────────────────────────────────────────
if "metres_result" in st.session_state:
    st.markdown("""
    <div class="result-box">
        <h3>📊 Résultats de l'analyse</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="success-box">
        ✅ Analyse complète de : <strong>{st.session_state.get('metres_filename', 'plan')}</strong>
    </div>
    """, unsafe_allow_html=True)

    # Afficher le résultat Markdown
    st.markdown(st.session_state["metres_result"])

    st.markdown("---")

    # ─── Export ───────────────────────────────────────────────────────────────
    st.markdown("#### 💾 Exporter les métrés")
    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        # Export texte brut
        txt_content = f"MÉTRÉS — {st.session_state.get('metres_filename', 'plan')}\n\n{st.session_state['metres_result']}"
        st.download_button(
            label="📄 Télécharger en TXT",
            data=txt_content.encode("utf-8"),
            file_name="metres_conducteurpro.txt",
            mime="text/plain",
            use_container_width=True
        )

    with col_dl2:
        # Copier dans presse-papier (bouton informatif)
        st.markdown("""
        <div class="info-box" style="text-align:center; padding: 0.7rem;">
            💡 Sélectionnez le texte ci-dessus et copiez-le dans votre logiciel métré
        </div>
        """, unsafe_allow_html=True)

    # ─── Nouvelle analyse ─────────────────────────────────────────────────────
    if st.button("🔄 Nouvelle analyse", use_container_width=False):
        del st.session_state["metres_result"]
        st.rerun()

elif uploaded_file is None:
    st.markdown("""
    <div class="info-box">
        👆 <strong>Commencez par uploader un plan ci-dessus.</strong><br>
        L'IA identifiera automatiquement tous les ouvrages et générera un tableau de métrés complet.
    </div>
    """, unsafe_allow_html=True)
