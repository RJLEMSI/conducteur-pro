"""
Page 5 — Analyse du Plan Local d'Urbanisme (PLU / PLUi)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils import (
    GLOBAL_CSS, render_sidebar, get_client, check_api_key,
    extract_text_from_pdf, analyze_plu
)

# ─── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Analyse PLU · ConducteurPro",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_sidebar()

# ─── En-tête ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h2>🗺️ Analyse PLU / PLUi</h2>
    <p>Uploadez le règlement de votre zone — L'IA extrait toutes les règles applicables à votre projet</p>
</div>
""", unsafe_allow_html=True)

# ─── Colonnes ─────────────────────────────────────────────────────────────────
col_main, col_info = st.columns([3, 1])

with col_info:
    st.markdown("""
    <div class="info-box">
        <strong>📌 Ce que l'IA extrait</strong><br>
        • Zone applicable et caractère<br>
        • Usages autorisés / interdits<br>
        • Emprise au sol max (CES)<br>
        • Hauteur maximale<br>
        • Retraits par rapport aux voies<br>
        • Retraits par rapport aux limites<br>
        • Aspect extérieur imposé<br>
        • Stationnement obligatoire<br>
        • Espaces verts réglementaires<br>
        • Servitudes particulières
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        <strong>💡 Conseil</strong><br>
        Uploadez le règlement de la <strong>zone spécifique</strong> de votre terrain (ex : Zone Ua, Ub, AU…)<br><br>
        Si vous avez le PLU complet, l'IA trouvera la bonne zone.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        <strong>🔗 Utilisation optimale</strong><br>
        Après l'analyse PLU, allez dans <strong>Synthèse Globale</strong> — l'IA croisera automatiquement les règles PLU avec votre DCE et vos études.
    </div>
    """, unsafe_allow_html=True)

with col_main:
    # ─── Infos contextuelles ──────────────────────────────────────────────────
    st.markdown("##### Informations sur le terrain et le projet")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        commune = st.text_input("Commune", placeholder="Ex : Bordeaux (33)")
        zone_connue = st.text_input("Zone PLU si connue", placeholder="Ex : Ua, UB, AU1...")
    with col_b:
        surface_terrain = st.text_input("Surface du terrain", placeholder="Ex : 850 m²")
        emprise_projet = st.text_input("Emprise au sol projet", placeholder="Ex : 120 m²")
    with col_c:
        hauteur_projet = st.text_input("Hauteur projet prévue", placeholder="Ex : 7,50m à l'égout")
        usage_projet = st.selectbox("Usage du projet", [
            "Habitation individuelle", "Habitation collective",
            "Commerce / ERP", "Bureaux / tertiaire",
            "Industrie / entrepôt", "Équipement public", "Mixte"
        ])

    st.markdown("---")

    # ─── Upload PLU ───────────────────────────────────────────────────────────
    st.markdown("##### Upload du règlement PLU")
    uploaded_plu = st.file_uploader(
        "📂 Uploadez le règlement PLU / PLUi (PDF)",
        type=["pdf"],
        help="Règlement de zone, PLU complet, règlement de lotissement..."
    )

    # Option : upload plan de zonage (image)
    uploaded_zonage = st.file_uploader(
        "🗺️ Plan de zonage (optionnel — image ou PDF)",
        type=["pdf", "jpg", "jpeg", "png"],
        help="Le plan de zonage graphique pour aider l'IA à identifier la zone"
    )

    if uploaded_plu:
        st.info(f"📄 PLU chargé : **{uploaded_plu.name}** ({uploaded_plu.size // 1024} Ko)")

        if st.button("🚀 Analyser le PLU", use_container_width=True):
            if not check_api_key():
                st.stop()

            client = get_client()

            with st.spinner("📖 Extraction du règlement PLU..."):
                text_plu = extract_text_from_pdf(uploaded_plu)

            if not text_plu.strip():
                st.markdown("""
                <div class="warning-box">
                    ⚠️ <strong>Aucun texte extrait.</strong> Le PLU est peut-être un scan.
                    Essayez une version texte ou demandez le PLU numérique à la mairie.
                </div>
                """, unsafe_allow_html=True)
                st.stop()

            # Construire le contexte projet
            projet_context = f"""
Projet : {usage_projet}
Commune : {commune}
Zone PLU identifieé : {zone_connue or 'Non précisée - à identifier dans le document'}
Surface terrain : {surface_terrain}
Emprise au sol projet : {emprise_projet}
Hauteur projet prévue : {hauteur_projet}
"""

            with st.spinner("🤖 Analyse du PLU et extraction des règles... (30-60 secondes)"):
                try:
                    result = analyze_plu(text_plu, projet_context, client)
                    st.session_state["plu_result"] = result
                    st.session_state["plu_filename"] = uploaded_plu.name
                    st.session_state["plu_context"] = projet_context
                    # Stocker pour la synthèse globale
                    st.session_state["global_plu"] = f"--- ANALYSE PLU ({uploaded_plu.name}) ---\n{result}"
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse IA : {e}")
                    st.stop()

# ─── Résultats ────────────────────────────────────────────────────────────────
if "plu_result" in st.session_state:
    st.markdown(f"""
    <div class="success-box">
        ✅ Analyse PLU complète : <strong>{st.session_state.get('plu_filename', '')}</strong>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(st.session_state["plu_result"])

    st.markdown("---")
    col_dl1, col_dl2, col_dl3 = st.columns(3)

    with col_dl1:
        txt = f"ANALYSE PLU\nFichier : {st.session_state.get('plu_filename','')}\n\n{st.session_state['plu_result']}"
        st.download_button("📄 Télécharger TXT", txt.encode("utf-8"),
                           "analyse_plu.txt", "text/plain", use_container_width=True)

    with col_dl2:
        if st.button("🔗 Envoyer à la Synthèse Globale", use_container_width=True):
            st.session_state["global_plu"] = (
                f"--- ANALYSE PLU ({st.session_state.get('plu_filename','')}) ---\n"
                f"{st.session_state['plu_result']}"
            )
            st.success("✅ PLU ajouté à la Synthèse Globale !")

    with col_dl3:
        if st.button("🔄 Analyser un autre PLU", use_container_width=True):
            del st.session_state["plu_result"]
            st.rerun()

elif uploaded_plu is None:
    st.markdown("""
    <div class="info-box">
        👆 <strong>Renseignez le contexte projet puis uploadez le règlement PLU.</strong><br>
        L'IA extraira toutes les règles applicables et vérifiera si votre projet est conforme.
        Ensuite, utilisez la <strong>Synthèse Globale</strong> pour croiser PLU + DCE + études en une seule analyse complète.
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📖 Exemple de règles extraites par l'IA"):
        st.markdown("""
        **Zone Ua — Centre bourg — Commune de Saint-Martin**

        | Règle | Valeur applicable | Conformité projet |
        |-------|------------------|-------------------|
        | Emprise au sol max | 60% | ✅ 14% (120m²/850m²) |
        | Hauteur max à l'égout | 9,00m | ✅ 7,50m prévu |
        | Retrait voie publique | 0m min (à l'alignement) | ⚠️ À vérifier plan masse |
        | Retrait limite séparative | H/2 min 3m | ✅ OK si H=7,5m → 3,75m |
        | Stationnement | 2 places/logement | ⚠️ À prévoir sur parcelle |
        | Espaces verts | 20% de la parcelle | ✅ 170m² prévu |
        | Matériaux toiture | Tuile canal ou ardoise | ℹ️ À préciser dans CCTP |
        """)
