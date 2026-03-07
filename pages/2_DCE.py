"""
Page 2 — Synthèse automatique de DCE
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils import (
    GLOBAL_CSS, render_sidebar, get_client, check_api_key,
    extract_text_from_pdf, synthesize_dce
)

# ─── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Synthèse DCE · ConducteurPro",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_sidebar()

# ─── En-tête ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h2>📋 Synthèse DCE</h2>
    <p>Uploadez votre Dossier de Consultation des Entreprises — l'IA le synthétise et extrait l'essentiel</p>
</div>
""", unsafe_allow_html=True)

# ─── Colonnes ─────────────────────────────────────────────────────────────────
col_main, col_info = st.columns([3, 1])

with col_info:
    st.markdown("""
    <div class="info-box">
        <strong>📌 Qu'est-ce que vous obtenez ?</strong><br>
        • Fiche de synthèse rapide<br>
        • Toutes les dates critiques<br>
        • Exigences techniques clés<br>
        • Points de vigilance<br>
        • Documents à fournir<br>
        • Critères de sélection<br>
        • Recommandations pratiques
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        <strong>📄 Formats acceptés</strong><br>
        • PDF texte (CCTP, CCAP, RC...)<br>
        • DCE complet multi-sections<br><br>
        <strong>⚠️ Conseil</strong><br>
        Si votre DCE fait +200 pages, commencez par le CCAP + RC pour les infos contractuelles, le CCTP pour le technique.
    </div>
    """, unsafe_allow_html=True)

with col_main:
    uploaded_file = st.file_uploader(
        "📂 Uploadez votre DCE (PDF)",
        type=["pdf"],
        help="Dossier de Consultation des Entreprises complet ou partiels (RC, CCAP, CCTP...)"
    )

    section_hint = st.selectbox(
        "Type de document uploadé (optionnel, aide l'IA)",
        ["DCE complet", "RC — Règlement de Consultation", "CCAP — Cahier des Clauses Administratives",
         "CCTP — Cahier des Clauses Techniques", "BPU / DQE", "Autre"],
        index=0
    )

    if uploaded_file:
        st.info(f"📄 Fichier chargé : **{uploaded_file.name}** ({uploaded_file.size // 1024} Ko)")

        st.markdown("---")

        if st.button("🚀 Synthétiser le DCE", use_container_width=True):
            if not check_api_key():
                st.stop()

            client = get_client()

            with st.spinner("📖 Extraction du texte en cours..."):
                text = extract_text_from_pdf(uploaded_file)

            if not text.strip():
                st.markdown("""
                <div class="warning-box">
                    ⚠️ <strong>Aucun texte extrait.</strong> Votre PDF est peut-être un scan image.<br>
                    Conseil : utiliser un PDF avec texte natif, ou effectuez une OCR avant upload.
                </div>
                """, unsafe_allow_html=True)
                st.stop()

            char_count = len(text)
            st.success(f"✅ {char_count:,} caractères extraits ({char_count // 250} pages environ)")

            # Ajouter le type de section au contexte si précisé
            if section_hint != "DCE complet":
                text = f"[Type de document : {section_hint}]\n\n{text}"

            with st.spinner("🤖 L'IA analyse le DCE... (peut prendre 30-60 secondes)"):
                try:
                    result = synthesize_dce(text, client)
                    st.session_state["dce_result"] = result
                    st.session_state["dce_filename"] = uploaded_file.name
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse IA : {e}")
                    st.stop()

# ─── Résultats ────────────────────────────────────────────────────────────────
if "dce_result" in st.session_state:
    st.markdown("""
    <div class="result-box">
        <h3>📊 Synthèse DCE générée</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="success-box">
        ✅ Synthèse de : <strong>{st.session_state.get('dce_filename', 'document')}</strong>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(st.session_state["dce_result"])

    st.markdown("---")

    # ─── Export ───────────────────────────────────────────────────────────────
    st.markdown("#### 💾 Exporter la synthèse")
    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        txt_content = f"SYNTHÈSE DCE — {st.session_state.get('dce_filename', 'document')}\nGénéré par ConducteurPro\n\n{st.session_state['dce_result']}"
        st.download_button(
            label="📄 Télécharger en TXT",
            data=txt_content.encode("utf-8"),
            file_name="synthese_dce_conducteurpro.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col_dl2:
        md_content = f"# Synthèse DCE\n**Fichier :** {st.session_state.get('dce_filename', '')}\n\n{st.session_state['dce_result']}"
        st.download_button(
            label="📝 Télécharger en Markdown",
            data=md_content.encode("utf-8"),
            file_name="synthese_dce_conducteurpro.md",
            mime="text/markdown",
            use_container_width=True
        )

    if st.button("🔄 Analyser un autre DCE", use_container_width=False):
        del st.session_state["dce_result"]
        st.rerun()

elif uploaded_file is None:
    st.markdown("""
    <div class="info-box">
        👆 <strong>Uploadez votre DCE ci-dessus.</strong><br>
        L'IA va lire l'intégralité du document et vous sortir une synthèse claire et opérationnelle en moins d'une minute.
    </div>
    """, unsafe_allow_html=True)

    # Exemple de ce qu'on peut analyser
    with st.expander("📖 Exemple de ce que l'IA extrait du DCE"):
        st.markdown("""
        **Exemple de synthèse générée :**

        | Élément | Contenu |
        |---------|---------|
        | Maître d'ouvrage | Commune de Saint-Martin (47) |
        | Nature des travaux | Construction d'une salle polyvalente R+0 |
        | Montant estimatif | 850 000 € HT |
        | Remise des offres | 15 mars 2025 à 12h00 |
        | Démarrage | Juin 2025 |
        | Durée | 12 mois |

        **Points de vigilance détectés :**
        - Pénalités de retard : 1/3000ème du marché par jour calendaire
        - Variante technique obligatoire sur les menuiseries extérieures
        - Caution bancaire de 5% requise dans les 30 jours
        """)
