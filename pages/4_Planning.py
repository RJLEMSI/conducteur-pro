"""
Page 4 â Aide au planning de chantier
GÃ©nÃ¨re un planning + checklist. Permet de sauvegarder dans l'historique.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
import json
from datetime import datetime
from utils import (
    GLOBAL_CSS, render_sidebar, get_client, check_api_key,
    extract_text_from_pdf, generate_planning
)

st.set_page_config(
    page_title="Aide Planning Â· ConducteurPro",
    page_icon="ð",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_sidebar()

# âââ En-tÃªte âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
st.markdown("""
<div class="page-header">
    <h2>ð Aide au planning</h2>
    <p>DÃ©crivez votre projet ou importez vos analyses â L'IA gÃ©nÃ¨re phasage, planning et checklist de dÃ©marrage</p>
</div>
""", unsafe_allow_html=True)

# âââ Tabs : Saisie manuelle ou import ââââââââââââââââââââââââââââââââââââââââââââ
tab_manual, tab_import, tab_analyses = st.tabs([
    "âï¸ Saisie manuelle",
    "ð Importer un document",
    "ð Depuis mes analyses"
])

# âââ Tab 1 : Saisie manuelle âââââââââââââââââââââââââââââââââââââââââââââââââââââ
with tab_manual:
    st.markdown("##### DÃ©crivez votre projet de construction")
    col1, col2 = st.columns(2)
    with col1:
        project_type = st.selectbox(
            "Type de projet",
            ["Maison individuelle", "Immeuble collectif", "BÃ¢timent tertiaire",
             "RÃ©habilitation / Extension", "Ouvrage d'art / VRD", "BÃ¢timent industriel", "Autre"]
        )
        surface = st.text_input("Surface approximative", placeholder="Ex : 250 mÂ² SHOB")
        nb_niveaux = st.text_input("Nombre de niveaux", placeholder="Ex : R+2 avec sous-sol")
        structure = st.selectbox(
            "Type de structure",
            ["MaÃ§onnerie traditionnelle", "BÃ©ton armÃ©", "Ossature bois", "MÃ©tal / charpente", "Mixte", "Inconnu"]
        )
    with col2:
        localisation = st.text_input("Localisation", placeholder="Ex : Bordeaux (33), zone sismique 2")
        date_debut = st.text_input("Date de dÃ©but souhaitÃ©e", placeholder="Ex : Septembre 2025")
        duree = st.text_input("DurÃ©e souhaitÃ©e", placeholder="Ex : 14 mois")
        budget = st.text_input("Budget approximatif (optionnel)", placeholder="Ex : 450 000 â¬ HT")

    contraintes = st.text_area(
        "Contraintes particuliÃ¨res et informations complÃ©mentaires",
        placeholder="Ex : Site en zone inondable, accÃ¨s difficile, riverains proches, dÃ©molition prÃ©alable...",
        height=100
    )

    if st.button("â Ajouter ces informations au contexte", use_container_width=False):
        context_manual = f"""
INFORMATIONS PROJET :
- Type : {project_type}
- Surface : {surface}
- Niveaux : {nb_niveaux}
- Structure : {structure}
- Localisation : {localisation}
- Date de dÃ©but : {date_debut}
- DurÃ©e souhaitÃ©e : {duree}
- Budget : {budget}
- Contraintes : {contraintes}
"""
        st.session_state["planning_manual_context"] = context_manual
        # MÃ©moriser pour l'historique
        st.session_state["planning_projet_info"] = {
            "type": project_type,
            "surface": surface,
            "localisation": localisation,
            "date_debut": date_debut,
            "duree": duree,
        }
        st.success("â Informations ajoutÃ©es !")

# âââ Tab 2 : Import document ââââââââââââââââââââââââââââââââââââââââââââââââââââââ
with tab_import:
    st.markdown("##### Importez un document pour enrichir le contexte planning")
    st.markdown("""
    <div class="info-box">
    Vous pouvez importer ici : un DCE, une synthÃ¨se d'Ã©tudes, un programme de travaux, un CCTP ou tout document dÃ©crivant le projet.
    </div>
    """, unsafe_allow_html=True)

    doc_file = st.file_uploader("ð Importer un document PDF", type=["pdf"], key="planning_doc")
    doc_type = st.text_input("Type de document", placeholder="Ex : DCE, CCTP, programme travaux...")

    if doc_file and st.button("ð Extraire et ajouter au contexte", use_container_width=False):
        with st.spinner("Extraction du texte..."):
            text = extract_text_from_pdf(doc_file)
            if text.strip():
                text_short = text[:20000] + ("..." if len(text) > 20000 else "")
                label = doc_type or doc_file.name
                st.session_state[f"planning_doc_ctx_{doc_file.name}"] = f"\n\n--- {label} ---\n{text_short}"
                st.success(f"â Document '{doc_file.name}' ajoutÃ© au contexte !")
            else:
                st.error("Impossible d'extraire le texte. VÃ©rifiez que le PDF contient du texte.")

# âââ Tab 3 : Analyses prÃ©cÃ©dentes ââââââââââââââââââââââââââââââââââââââââââââââââ
with tab_analyses:
    if st.session_state.get("planning_context"):
        st.markdown("""
        <div class="success-box">
        â Des analyses depuis les autres modules ont Ã©tÃ© ajoutÃ©es automatiquement au contexte.
        </div>
        """, unsafe_allow_html=True)
        with st.expander("Voir le contexte importÃ© des analyses"):
            st.text(st.session_state["planning_context"][:3000] + "...")
        if st.button("ðï¸ Effacer le contexte importÃ©"):
            del st.session_state["planning_context"]
            st.rerun()
    else:
        st.markdown("""
        <div class="info-box">
        ð¡ <strong>Astuce :</strong> AprÃ¨s avoir analysÃ© un DCE ou une Ã©tude technique dans les modules correspondants,
        cliquez sur "Envoyer au module Planning" â les rÃ©sultats seront automatiquement disponibles ici.
        </div>
        """, unsafe_allow_html=True)

# âââ Assemblage du contexte et gÃ©nÃ©ration ââââââââââââââââââââââââââââââââââââââââ
st.markdown("---")
st.markdown("### ð GÃ©nÃ©rer le planning")

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
    â Contexte prÃªt â L'IA dispose de suffisamment d'informations pour gÃ©nÃ©rer un planning.
    </div>
    """, unsafe_allow_html=True)
    with st.expander("Voir le contexte assemblÃ©"):
        st.text(assembled_context[:2000] + ("..." if len(assembled_context) > 2000 else ""))
else:
    st.markdown("""
    <div class="warning-box">
    â ï¸ Aucun contexte fourni. Remplissez au moins la saisie manuelle (onglet âï¸) ou importez un document.
    </div>
    """, unsafe_allow_html=True)

specific_request = st.text_area(
    "Demande spÃ©cifique (optionnel)",
    placeholder="Ex : Insiste sur la phase gros oeuvre et les dÃ©lais d'approvisionnement bÃ©ton. PrÃ©vois 2 Ã©quipes maÃ§onnerie...",
    height=80
)
if specific_request:
    assembled_context += f"\n\nDEMANDE SPÃCIFIQUE DU CDT : {specific_request}"

col_btn, col_info = st.columns([2, 1])
with col_btn:
    generate_btn = st.button(
        "ð¤ GÃ©nÃ©rer le planning et la checklist",
        use_container_width=True,
        disabled=not assembled_context.strip()
    )
with col_info:
    st.markdown("""
    <div class="info-box" style="font-size:0.82rem;">
    ð¡ Plus vous fournissez d'informations, plus le planning sera prÃ©cis et adaptÃ©.
    </div>
    """, unsafe_allow_html=True)

if generate_btn:
    if not check_api_key():
        st.stop()
    client = get_client()
    with st.spinner("ð¤ GÃ©nÃ©ration du planning... (30-60 secondes)"):
        try:
            result = generate_planning(assembled_context, client)
            st.session_state["planning_result"] = result
        except Exception as e:
            st.error(f"Erreur lors de la gÃ©nÃ©ration : {e}")
            st.stop()

# âââ RÃ©sultats ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
if "planning_result" in st.session_state:
    st.markdown("""
    <div class="result-box">
        <h3>ð Planning et checklist gÃ©nÃ©rÃ©s</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(st.session_state["planning_result"])
    st.markdown("---")

    # âââ Sauvegarde dans l'historique ââââââââââââââââââââââââââââââââââââââââââââ
    st.markdown("#### ð¾ Sauvegarder ce planning")

    col_sv1, col_sv2 = st.columns([2, 1])
    with col_sv1:
        planning_name = st.text_input(
            "Nom du planning",
            value=st.session_state.get("planning_projet_info", {}).get(
                "type", f"Planning du {datetime.now().strftime('%d/%m/%Y')}"
            ),
            key="planning_save_name"
        )
    with col_sv2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ð¾ Sauvegarder dans l'historique", use_container_width=True):
            if "planning_history" not in st.session_state:
                st.session_state.planning_history = []

            projet_info = st.session_state.get("planning_projet_info", {})

            # Extraction des phases pour l'Ã©dition ultÃ©rieure
            from _planning_utils import extract_phases_from_markdown
            phases = extract_phases_from_markdown(st.session_state["planning_result"])

            new_entry = {
                "id": f"{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "nom": planning_name,
                "date": datetime.now().strftime("%d/%m/%Y Ã  %H:%M"),
                "projet": f"{projet_info.get('type','')} â {projet_info.get('surface','')}",
                "localisation": projet_info.get("localisation", ""),
                "date_debut": projet_info.get("date_debut", ""),
                "duree": projet_info.get("duree", ""),
                "contenu": st.session_state["planning_result"],
                "phases": phases,
                "contexte": assembled_context[:5000],
            }
            st.session_state.planning_history.append(new_entry)
            st.success(f"â Planning '{planning_name}' sauvegardÃ© dans l'historique !")

    st.markdown("---")
    col_dl1, col_dl2, col_dl3 = st.columns(3)

    with col_dl1:
        txt_content = f"AIDE AU PLANNING â GÃ©nÃ©rÃ© par ConducteurPro\n\n{st.session_state['planning_result']}"
        st.download_button(
            label="ð TÃ©lÃ©charger en TXT",
            data=txt_content.encode("utf-8"),
            file_name="planning_conducteurpro.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col_dl2:
        md_content = f"# Planning de chantier\nGÃ©nÃ©rÃ© par ConducteurPro\n\n{st.session_state['planning_result']}"
        st.download_button(
            label="ð TÃ©lÃ©charger en Markdown",
            data=md_content.encode("utf-8"),
            file_name="planning_conducteurpro.md",
            mime="text/markdown",
            use_container_width=True
        )
    with col_dl3:
        if st.button("ð° GÃ©nÃ©rer un devis Ã  partir de ce planning", use_container_width=True):
            projet_info = st.session_state.get("planning_projet_info", {})
            st.session_state["devis_from_planning"] = {
                "nom": planning_name,
                "projet": f"{projet_info.get('type','')} â {projet_info.get('surface','')}",
                "localisation": projet_info.get("localisation", ""),
                "contenu": st.session_state["planning_result"],
            }
            st.switch_page("pages/8_Devis.py")

    if st.button("ð GÃ©nÃ©rer un nouveau planning", use_container_width=False):
        del st.session_state["planning_result"]
        for k in list(st.session_state.keys()):
            if k.startswith("planning_") and k not in ["planning_history"]:
                del st.session_state[k]
        st.rerun()
