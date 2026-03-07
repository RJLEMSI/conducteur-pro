"""
Page 4 — Aide au planning de chantier
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils import (
    GLOBAL_CSS, render_sidebar, get_client, check_api_key,
    extract_text_from_pdf, generate_planning
)

# ─── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Aide Planning · ConducteurPro",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_sidebar()

# ─── En-tête ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h2>📅 Aide au planning</h2>
    <p>Décrivez votre projet ou importez vos analyses — L'IA génère phasage, planning et checklist de démarrage</p>
</div>
""", unsafe_allow_html=True)

# ─── Tabs : Saisie manuelle ou import ─────────────────────────────────────────
tab_manual, tab_import, tab_analyses = st.tabs([
    "✏️  Saisie manuelle",
    "📄  Importer un document",
    "🔗  Depuis mes analyses"
])

context_parts = []

# ─── Tab 1 : Saisie manuelle ──────────────────────────────────────────────────
with tab_manual:
    st.markdown("##### Décrivez votre projet de construction")

    col1, col2 = st.columns(2)
    with col1:
        project_type = st.selectbox(
            "Type de projet",
            ["Maison individuelle", "Immeuble collectif", "Bâtiment tertiaire",
             "Réhabilitation / Extension", "Ouvrage d'art / VRD", "Bâtiment industriel", "Autre"]
        )
        surface = st.text_input("Surface approximative", placeholder="Ex : 250 m² SHOB")
        nb_niveaux = st.text_input("Nombre de niveaux", placeholder="Ex : R+2 avec sous-sol")
        structure = st.selectbox(
            "Type de structure",
            ["Maçonnerie traditionnelle", "Béton armé", "Ossature bois", "Métal / charpente", "Mixte", "Inconnu"]
        )

    with col2:
        localisation = st.text_input("Localisation", placeholder="Ex : Bordeaux (33), zone sismique 2")
        date_debut = st.text_input("Date de début souhaitée", placeholder="Ex : Septembre 2025")
        duree = st.text_input("Durée souhaitée", placeholder="Ex : 14 mois")
        budget = st.text_input("Budget approximatif (optionnel)", placeholder="Ex : 450 000 € HT")

    contraintes = st.text_area(
        "Contraintes particulières et informations complémentaires",
        placeholder="Ex : Site en zone inondable, accès difficile, riverains proches, démolition préalable, lot séparé pour électricité...",
        height=100
    )

    if st.button("➕ Ajouter ces informations au contexte", use_container_width=False):
        context_manual = f"""
INFORMATIONS PROJET :
- Type : {project_type}
- Surface : {surface}
- Niveaux : {nb_niveaux}
- Structure : {structure}
- Localisation : {localisation}
- Date de début : {date_debut}
- Durée souhaitée : {duree}
- Budget : {budget}
- Contraintes : {contraintes}
"""
        st.session_state["planning_manual_context"] = context_manual
        st.success("✅ Informations ajoutées !")

# ─── Tab 2 : Import document ──────────────────────────────────────────────────
with tab_import:
    st.markdown("##### Importez un document pour enrichir le contexte planning")
    st.markdown("""
    <div class="info-box">
        Vous pouvez importer ici : un DCE, une synthèse d'études, un programme de travaux,
        un CCTP ou tout document décrivant le projet.
    </div>
    """, unsafe_allow_html=True)

    doc_file = st.file_uploader("📂 Importer un document PDF", type=["pdf"], key="planning_doc")
    doc_type = st.text_input("Type de document", placeholder="Ex : DCE, CCTP, programme travaux...")

    if doc_file and st.button("📖 Extraire et ajouter au contexte", use_container_width=False):
        with st.spinner("Extraction du texte..."):
            text = extract_text_from_pdf(doc_file)
        if text.strip():
            label = doc_type or doc_file.name
            # Tronquer à 20 000 chars pour le contexte planning
            text_short = text[:20000] + ("..." if len(text) > 20000 else "")
            st.session_state[f"planning_doc_ctx_{doc_file.name}"] = f"\n\n--- {label} ---\n{text_short}"
            st.success(f"✅ Document '{doc_file.name}' ajouté au contexte !")
        else:
            st.error("Impossible d'extraire le texte. Vérifiez que le PDF contient du texte.")

# ─── Tab 3 : Analyses précédentes ─────────────────────────────────────────────
with tab_analyses:
    if st.session_state.get("planning_context"):
        st.markdown("""
        <div class="success-box">
            ✅ Des analyses depuis les autres modules ont été ajoutées automatiquement au contexte.
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Voir le contexte importé des analyses"):
            st.text(st.session_state["planning_context"][:3000] + "...")

        if st.button("🗑️ Effacer le contexte importé"):
            del st.session_state["planning_context"]
            st.rerun()
    else:
        st.markdown("""
        <div class="info-box">
            💡 <strong>Astuce :</strong> Après avoir analysé un DCE ou une étude technique dans les modules correspondants,
            cliquez sur "Envoyer au module Planning" — les résultats seront automatiquement disponibles ici.
        </div>
        """, unsafe_allow_html=True)

# ─── Assemblage du contexte et génération ─────────────────────────────────────
st.markdown("---")
st.markdown("### 🚀 Générer le planning")

# Résumé du contexte assemblé
all_context_keys = ["planning_manual_context", "planning_context"]
all_context_keys += [k for k in st.session_state.keys() if k.startswith("planning_doc_ctx_")]

assembled_context = "\n".join([
    st.session_state.get(k, "")
    for k in all_context_keys
    if st.session_state.get(k, "").strip()
])

if assembled_context.strip():
    st.markdown("""
    <div class="success-box">
        ✅ Contexte prêt — L'IA dispose de suffisamment d'informations pour générer un planning.
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Voir le contexte assemblé"):
        st.text(assembled_context[:2000] + ("..." if len(assembled_context) > 2000 else ""))
else:
    st.markdown("""
    <div class="warning-box">
        ⚠️ Aucun contexte fourni. Remplissez au moins la saisie manuelle (onglet ✏️) ou importez un document.
    </div>
    """, unsafe_allow_html=True)

# Option : demande spécifique
specific_request = st.text_area(
    "Demande spécifique (optionnel)",
    placeholder="Ex : Insiste sur la phase gros oeuvre et les délais d'approvisionnement béton. Prévois 2 équipes maçonnerie...",
    height=80
)

if specific_request:
    assembled_context += f"\n\nDEMANDE SPÉCIFIQUE DU CDT : {specific_request}"

col_btn, col_info = st.columns([2, 1])
with col_btn:
    generate_btn = st.button("🤖 Générer le planning et la checklist", use_container_width=True, disabled=not assembled_context.strip())

with col_info:
    st.markdown("""
    <div class="info-box" style="font-size:0.82rem;">
        💡 Plus vous fournissez d'informations, plus le planning sera précis et adapté.
    </div>
    """, unsafe_allow_html=True)

if generate_btn:
    if not check_api_key():
        st.stop()

    client = get_client()
    with st.spinner("🤖 Génération du planning... (30-60 secondes)"):
        try:
            result = generate_planning(assembled_context, client)
            st.session_state["planning_result"] = result
        except Exception as e:
            st.error(f"Erreur lors de la génération : {e}")
            st.stop()

# ─── Résultats ────────────────────────────────────────────────────────────────
if "planning_result" in st.session_state:
    st.markdown("""
    <div class="result-box">
        <h3>📅 Planning et checklist générés</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(st.session_state["planning_result"])

    st.markdown("---")

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        txt_content = f"AIDE AU PLANNING — Généré par ConducteurPro\n\n{st.session_state['planning_result']}"
        st.download_button(
            label="📄 Télécharger en TXT",
            data=txt_content.encode("utf-8"),
            file_name="planning_conducteurpro.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col_dl2:
        md_content = f"# Planning de chantier\nGénéré par ConducteurPro\n\n{st.session_state['planning_result']}"
        st.download_button(
            label="📝 Télécharger en Markdown",
            data=md_content.encode("utf-8"),
            file_name="planning_conducteurpro.md",
            mime="text/markdown",
            use_container_width=True
        )

    if st.button("🔄 Générer un nouveau planning", use_container_width=False):
        del st.session_state["planning_result"]
        # Nettoyer aussi les contextes
        for k in list(st.session_state.keys()):
            if k.startswith("planning_"):
                del st.session_state[k]
        st.rerun()
