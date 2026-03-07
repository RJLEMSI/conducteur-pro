"""
Page 6 — Synthèse Globale : croise TOUS les documents pour mâcher 90% du boulot
PLU + DCE + Études + Métrés → Rapport complet de projet
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils import (
    GLOBAL_CSS, render_sidebar, get_client, check_api_key,
    extract_text_from_pdf, generate_synthese_globale
)

# ─── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Synthèse Globale · ConducteurPro",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_sidebar()

# ─── En-tête ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header" style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);">
    <h2>🧠 Synthèse Globale du Projet</h2>
    <p>Donnez TOUS vos documents — L'IA croise tout et produit 90% du dossier. Il ne vous reste qu'à vérifier.</p>
</div>
""", unsafe_allow_html=True)

# ─── Explication du module ────────────────────────────────────────────────────
st.markdown("""
<div class="info-box">
    <strong>🎯 Comment ça fonctionne</strong><br>
    Alimentez le module avec autant de documents que vous avez (PLU, DCE, études béton/structure/thermique/acoustique, plans).
    L'IA lit tout, croise les informations, identifie les contradictions, les risques et les contraintes croisées.
    Elle produit un <strong>rapport de projet complet</strong> prêt à être soumis au chef de chantier.
</div>
""", unsafe_allow_html=True)

# ─── État des documents disponibles ──────────────────────────────────────────
st.markdown("### 📂 Documents disponibles pour la synthèse")

doc_status = {
    "🗺️ PLU / Règlement de zone": "global_plu",
    "📋 Synthèse DCE": "dce_result",
    "🧱 Étude béton/fondations": None,
    "🏗️ Étude structure": None,
    "🌡️ Étude thermique": None,
    "🔊 Étude acoustique": None,
    "📐 Métrés": "metres_result",
    "📅 Analyse planning": "planning_result",
}

# Compter les docs déjà disponibles depuis les autres modules
available_from_session = []
for label, key in doc_status.items():
    if key and st.session_state.get(key):
        available_from_session.append(label)

col_s1, col_s2, col_s3, col_s4 = st.columns(4)
status_cols = [col_s1, col_s2, col_s3, col_s4]
for i, (label, key) in enumerate(doc_status.items()):
    with status_cols[i % 4]:
        is_available = key and st.session_state.get(key)
        color = "#F0FDF4" if is_available else "#F8FAFC"
        border = "#22C55E" if is_available else "#E2EBF5"
        icon = "✅" if is_available else "⬜"
        st.markdown(f"""
        <div style="background:{color};border:1.5px solid {border};border-radius:10px;
                    padding:0.7rem;text-align:center;font-size:0.82rem;font-weight:600;
                    color:{'#166534' if is_available else '#94A3B8'};">
            {icon} {label}
        </div>
        """, unsafe_allow_html=True)

if available_from_session:
    st.markdown(f"""
    <div class="success-box" style="margin-top:1rem;">
        ✅ <strong>{len(available_from_session)} document(s) déjà importé(s)</strong> depuis vos analyses précédentes :
        {', '.join(available_from_session)}
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ─── Upload de nouveaux documents ─────────────────────────────────────────────
st.markdown("### 📤 Ajouter des documents supplémentaires")
st.caption("Uploadez ici les documents que vous n'avez pas encore analysés dans les autres modules")

col_up1, col_up2 = st.columns(2)

with col_up1:
    new_docs = st.file_uploader(
        "📂 Uploadez 1 ou plusieurs documents PDF",
        type=["pdf"],
        accept_multiple_files=True,
        help="PLU, DCE, études, notes de calcul, CCTP, tout document utile au projet"
    )

    if new_docs:
        for doc in new_docs:
            key = f"extra_doc_{doc.name}"
            if key not in st.session_state:
                with st.spinner(f"Extraction : {doc.name}..."):
                    text = extract_text_from_pdf(doc)
                if text.strip():
                    st.session_state[key] = f"--- {doc.name} ---\n{text[:15000]}"
                    st.success(f"✅ {doc.name} ajouté ({len(text):,} caractères)")
                else:
                    st.warning(f"⚠️ {doc.name} : aucun texte extrait (scan ?)")

with col_up2:
    # Description manuelle du projet
    st.markdown("**Description manuelle du projet**")
    projet_desc = st.text_area(
        "Décrivez votre projet en quelques lignes",
        placeholder=(
            "Ex : Construction d'une maison individuelle R+1 de 145m² SHAB sur terrain de 820m² "
            "en zone Ua. Structure maçonnerie parpaing + charpente bois. Budget 280 000€ HT. "
            "Démarrage souhaité mars 2026. Maîtrise d'ouvrage privée. MOE : Cabinet XYZ."
        ),
        height=150,
        key="projet_description"
    )

st.markdown("---")

# ─── Options de la synthèse ───────────────────────────────────────────────────
st.markdown("### ⚙️ Options du rapport")

col_opt1, col_opt2 = st.columns(2)
with col_opt1:
    rapport_type = st.selectbox("Type de rapport à générer", [
        "Rapport complet (recommandé) — toutes les sections",
        "Rapport express — points critiques uniquement",
        "Rapport conformité PLU — focus règles d'urbanisme",
        "Rapport préparation chantier — focus opérationnel",
    ])
    include_checklist = st.checkbox("Inclure checklist de mise en chantier", value=True)
    include_risques = st.checkbox("Inclure analyse des risques", value=True)

with col_opt2:
    include_planning = st.checkbox("Inclure phasage et planning estimatif", value=True)
    include_budget = st.checkbox("Inclure estimation budgétaire par poste", value=True)
    demande_specifique = st.text_area(
        "Instructions spécifiques pour l'IA (optionnel)",
        placeholder="Ex : Insiste sur les contraintes thermiques RE2020. Donne une attention particulière aux interfaces GO/charpente...",
        height=80
    )

# ─── Assemblage du contexte ───────────────────────────────────────────────────
def assemble_context():
    parts = []

    if st.session_state.get("projet_description"):
        parts.append(f"DESCRIPTION DU PROJET :\n{st.session_state['projet_description']}")

    if st.session_state.get("global_plu"):
        parts.append(st.session_state["global_plu"][:12000])

    if st.session_state.get("dce_result"):
        parts.append(f"--- SYNTHÈSE DCE ---\n{st.session_state['dce_result'][:8000]}")

    if st.session_state.get("etude_result"):
        parts.append(f"--- ÉTUDE TECHNIQUE ({st.session_state.get('etude_type','')}) ---\n{st.session_state['etude_result'][:8000]}")

    if st.session_state.get("metres_result"):
        parts.append(f"--- MÉTRÉS ---\n{st.session_state['metres_result'][:5000]}")

    if st.session_state.get("planning_result"):
        parts.append(f"--- PLANNING ---\n{st.session_state['planning_result'][:5000]}")

    # Docs extra uploadés directement ici
    for key, val in st.session_state.items():
        if key.startswith("extra_doc_"):
            parts.append(val[:8000])

    # Context depuis module études
    if st.session_state.get("planning_context"):
        parts.append(st.session_state["planning_context"][:5000])

    return "\n\n".join(parts)


context_total = assemble_context()
nb_chars = len(context_total)

if nb_chars > 500:
    st.markdown(f"""
    <div class="success-box">
        🧠 <strong>Contexte assemblé :</strong> {nb_chars:,} caractères provenant de {len([p for p in context_total.split('---') if len(p) > 50])} section(s) de documents
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="warning-box">
        ⚠️ Peu de contexte disponible. Uploadez au moins un document ou décrivez votre projet ci-dessus pour obtenir une synthèse pertinente.
    </div>
    """, unsafe_allow_html=True)

# ─── Bouton génération ────────────────────────────────────────────────────────
st.markdown("---")
col_gen, col_hint = st.columns([2, 1])
with col_gen:
    gen_btn = st.button(
        "🧠 Générer la Synthèse Globale",
        use_container_width=True,
        disabled=(nb_chars < 100)
    )
with col_hint:
    st.markdown("""
    <div class="info-box" style="font-size:0.82rem;">
        ⏱️ <strong>45 à 120 secondes</strong> selon la quantité de documents.<br>
        L'IA lit et croise tout simultanément.
    </div>
    """, unsafe_allow_html=True)

if gen_btn:
    if not check_api_key():
        st.stop()

    client = get_client()

    # Options à passer à l'IA
    options_str = f"""
Options rapport : {rapport_type}
Inclure checklist : {include_checklist}
Inclure risques : {include_risques}
Inclure planning : {include_planning}
Inclure budget estimatif : {include_budget}
{f'Instructions spécifiques : {demande_specifique}' if demande_specifique else ''}
"""
    with st.spinner("🧠 L'IA analyse et croise tous vos documents... (peut prendre 60-120 secondes)"):
        try:
            result = generate_synthese_globale(context_total, options_str, client)
            st.session_state["synthese_result"] = result
        except Exception as e:
            st.error(f"Erreur lors de la synthèse : {e}")
            st.stop()

# ─── Résultats ────────────────────────────────────────────────────────────────
if "synthese_result" in st.session_state:
    st.markdown("""
    <div style="background: linear-gradient(135deg,#1a1a2e,#0f3460);color:white;
                border-radius:14px;padding:1.5rem 2rem;margin:1.5rem 0;">
        <h3 style="margin:0;font-size:1.3rem;">🧠 Rapport de Synthèse Globale</h3>
        <p style="opacity:0.8;margin-top:0.3rem;font-size:0.9rem;">Généré par ConducteurPro · Basé sur vos documents · À vérifier et ajuster selon votre expérience terrain</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(st.session_state["synthese_result"])

    st.markdown("---")

    col_dl1, col_dl2, col_dl3 = st.columns(3)
    with col_dl1:
        txt = f"SYNTHÈSE GLOBALE DU PROJET\nGénéré par ConducteurPro\n\n{st.session_state['synthese_result']}"
        st.download_button("📄 Télécharger TXT", txt.encode("utf-8"),
                           "synthese_globale_projet.txt", "text/plain", use_container_width=True)
    with col_dl2:
        md = f"# Synthèse Globale du Projet\n*Généré par ConducteurPro*\n\n{st.session_state['synthese_result']}"
        st.download_button("📝 Télécharger Markdown", md.encode("utf-8"),
                           "synthese_globale_projet.md", "text/markdown", use_container_width=True)
    with col_dl3:
        if st.button("🔄 Nouvelle synthèse", use_container_width=True):
            del st.session_state["synthese_result"]
            st.rerun()

    st.markdown("""
    <div class="warning-box">
        ⚠️ <strong>Rappel important :</strong> Ce rapport est généré par l'IA à partir de vos documents.
        Il couvre ~90% du travail d'analyse, mais votre expertise terrain reste indispensable pour la vérification finale,
        notamment sur les contraintes de sol, les spécificités locales et les relations avec les intervenants.
    </div>
    """, unsafe_allow_html=True)
