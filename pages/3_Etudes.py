"""
Page 3 — Analyse des études techniques (béton, structure, thermique, acoustique)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils import (
    GLOBAL_CSS, render_sidebar, get_client, check_api_key,
    extract_text_from_pdf, analyze_technical_study
)

# ─── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Études Techniques · ConducteurPro",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_sidebar()

# ─── En-tête ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h2>🔬 Études techniques</h2>
    <p>Béton · Structure · Thermique · Acoustique — L'IA lit les études et vous dit ce qui compte pour le chantier</p>
</div>
""", unsafe_allow_html=True)

# ─── Sélection du type d'étude ────────────────────────────────────────────────
st.markdown("#### Quel type d'étude souhaitez-vous analyser ?")

study_types = {
    "béton / fondations": {
        "icon": "🧱",
        "label": "Béton / Fondations",
        "desc": "Notes de calcul béton armé, étude de sol, fondations, plans béton"
    },
    "structure / charpente": {
        "icon": "🏗️",
        "label": "Structure / Charpente",
        "desc": "Notes de calcul structure, charpente bois ou métallique, descentes de charges"
    },
    "thermique / RE2020": {
        "icon": "🌡️",
        "label": "Thermique / RE2020",
        "desc": "Étude thermique RE2020, RT2012, calcul Bbio, Cep, bilan thermique"
    },
    "acoustique": {
        "icon": "🔊",
        "label": "Acoustique",
        "desc": "Étude acoustique, isolements aux bruits aériens et aux chocs, NRA"
    }
}

col1, col2, col3, col4 = st.columns(4)
selected_study = st.session_state.get("selected_study", "béton / fondations")

for col, (key, info) in zip([col1, col2, col3, col4], study_types.items()):
    with col:
        is_selected = selected_study == key
        border_style = "border: 2px solid #1B4F8A; background: #EFF6FF;" if is_selected else "border: 1px solid #E2EBF5; background: white;"
        st.markdown(f"""
        <div style="{border_style} border-radius: 14px; padding: 1.2rem; text-align: center; margin-bottom: 0.5rem; cursor:pointer;">
            <div style="font-size:2rem;">{info['icon']}</div>
            <div style="font-weight:700; color:#0D3B6E; font-size:0.9rem; margin:0.4rem 0;">{info['label']}</div>
            <div style="color:#6B7280; font-size:0.78rem;">{info['desc']}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Sélectionner", key=f"sel_{key}", use_container_width=True):
            st.session_state["selected_study"] = key
            st.rerun()

st.markdown("---")

# ─── Colonnes upload / infos ──────────────────────────────────────────────────
col_main, col_info = st.columns([3, 1])

with col_info:
    info = study_types[selected_study]
    st.markdown(f"""
    <div class="info-box">
        <strong>{info['icon']} Module sélectionné</strong><br>
        <strong>{info['label']}</strong><br><br>
        {info['desc']}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        <strong>📊 Ce que vous obtenez :</strong><br>
        • Résumé exécutif<br>
        • Tableau des données clés<br>
        • Contraintes d'exécution<br>
        • Points de vigilance critiques<br>
        • Impact sur le planning<br>
        • Normes et DTU de référence
    </div>
    """, unsafe_allow_html=True)

with col_main:
    study_info = study_types[selected_study]
    uploaded_file = st.file_uploader(
        f"📂 Uploadez votre étude {study_info['label']} (PDF)",
        type=["pdf"],
        help=f"Étude technique : {study_info['desc']}"
    )

    if uploaded_file:
        st.info(f"📄 Fichier chargé : **{uploaded_file.name}** ({uploaded_file.size // 1024} Ko)")

        # Option : préciser le contexte
        context_extra = st.text_area(
            "Contexte du projet (optionnel)",
            placeholder="Ex : Maison individuelle R+1, zone sismique 2, sol argileux... Toute info utile pour l'IA.",
            height=70
        )

        st.markdown("---")

        if st.button(f"🚀 Analyser l'étude {study_info['label']}", use_container_width=True):
            if not check_api_key():
                st.stop()

            client = get_client()

            with st.spinner("📖 Extraction du texte..."):
                text = extract_text_from_pdf(uploaded_file)

            if not text.strip():
                st.markdown("""
                <div class="warning-box">
                    ⚠️ <strong>Aucun texte extrait.</strong> Votre PDF est peut-être un scan. Essayez une version texte du document.
                </div>
                """, unsafe_allow_html=True)
                st.stop()

            if context_extra:
                text = f"[Contexte projet : {context_extra}]\n\n{text}"

            with st.spinner(f"🤖 Analyse de l'étude {study_info['label']}... (30-60 secondes)"):
                try:
                    result = analyze_technical_study(text, selected_study, client)
                    st.session_state["etude_result"] = result
                    st.session_state["etude_filename"] = uploaded_file.name
                    st.session_state["etude_type"] = selected_study
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse IA : {e}")
                    st.stop()

# ─── Résultats ────────────────────────────────────────────────────────────────
if "etude_result" in st.session_state:
    etude_type = st.session_state.get("etude_type", "")
    etude_info = study_types.get(etude_type, {"icon": "🔬", "label": "Étude"})

    st.markdown(f"""
    <div class="result-box">
        <h3>{etude_info['icon']} Analyse — {etude_info['label']}</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="success-box">
        ✅ Analyse complète de : <strong>{st.session_state.get('etude_filename', 'document')}</strong>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(st.session_state["etude_result"])

    st.markdown("---")

    # ─── Ajouter au contexte planning ─────────────────────────────────────────
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        txt_content = (
            f"ANALYSE ÉTUDE {etude_info['label'].upper()}\n"
            f"Fichier : {st.session_state.get('etude_filename', '')}\n"
            f"Généré par ConducteurPro\n\n"
            f"{st.session_state['etude_result']}"
        )
        st.download_button(
            label="📄 Télécharger en TXT",
            data=txt_content.encode("utf-8"),
            file_name=f"analyse_etude_{etude_type.replace('/', '_')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col_dl2:
        if st.button("📅 Envoyer au module Planning", use_container_width=True):
            # Stocker dans session_state pour le module planning
            if "planning_context" not in st.session_state:
                st.session_state["planning_context"] = ""
            st.session_state["planning_context"] += (
                f"\n\n--- ANALYSE ÉTUDE {etude_info['label'].upper()} ---\n"
                f"{st.session_state['etude_result']}"
            )
            st.success("✅ Analyse ajoutée au contexte Planning ! Allez dans le module Planning.")

    if st.button("🔄 Analyser une autre étude", use_container_width=False):
        del st.session_state["etude_result"]
        st.rerun()

elif uploaded_file is None:
    st.markdown("""
    <div class="info-box">
        👆 <strong>Sélectionnez le type d'étude puis uploadez le PDF.</strong><br>
        L'IA va lire l'étude complète et extraire uniquement ce qui est pertinent pour votre chantier.
    </div>
    """, unsafe_allow_html=True)
