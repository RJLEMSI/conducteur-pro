"""
Page 7 — Historique des plannings générés
Permet de consulter, ajuster les périodes et exporter les plannings sauvegardés.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import json
import pandas as pd
from datetime import datetime
from utils import GLOBAL_CSS, render_sidebar

st.set_page_config(
    page_title="Historique · ConducteurPro",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_sidebar()

# ─── En-tête ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h2>📚 Historique des plannings</h2>
    <p>Consultez, ajustez les périodes et exportez vos plannings générés</p>
</div>
""", unsafe_allow_html=True)

# ─── Initialisation session ─────────────────────────────────────────────────────
if "planning_history" not in st.session_state:
    st.session_state.planning_history = []

# ─── Import / Export JSON ────────────────────────────────────────────────────────
col_import, col_export, col_clear = st.columns([2, 2, 1])

with col_import:
    uploaded_history = st.file_uploader(
        "📥 Importer un historique (.json)",
        type=["json"],
        key="history_import",
        help="Importez un fichier JSON exporté depuis une session précédente"
    )
    if uploaded_history:
        try:
            data = json.loads(uploaded_history.read().decode("utf-8"))
            if isinstance(data, list):
                existing_ids = {p.get("id") for p in st.session_state.planning_history}
                new_plans = [p for p in data if p.get("id") not in existing_ids]
                st.session_state.planning_history.extend(new_plans)
                st.success(f"✅ {len(new_plans)} planning(s) importé(s) !")
                st.rerun()
        except Exception as e:
            st.error(f"Erreur import : {e}")

with col_export:
    if st.session_state.planning_history:
        export_data = json.dumps(st.session_state.planning_history, ensure_ascii=False, indent=2)
        st.download_button(
            label="📤 Exporter tout l'historique (.json)",
            data=export_data.encode("utf-8"),
            file_name=f"conducteurpro_historique_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )

with col_clear:
    if st.session_state.planning_history:
        if st.button("🗑️ Tout effacer", use_container_width=True):
            st.session_state.planning_history = []
            if "history_selected" in st.session_state:
                del st.session_state["history_selected"]
            st.rerun()

st.markdown("---")

# ─── Liste des plannings ─────────────────────────────────────────────────────────
if not st.session_state.planning_history:
    st.markdown("""
    <div class="info-box">
        📚 <strong>Aucun planning sauvegardé pour l'instant.</strong><br><br>
        Allez dans <strong>📅 Aide au planning</strong>, générez un planning, puis cliquez sur
        <strong>"💾 Sauvegarder ce planning"</strong> pour le retrouver ici.<br><br>
        💡 <em>Conseil : exportez votre historique régulièrement en JSON pour ne rien perdre entre les sessions.</em>
    </div>
    """, unsafe_allow_html=True)
else:
    nb = len(st.session_state.planning_history)
    st.markdown(f"#### 📋 {nb} planning(s) sauvegardé(s)")

    # Si un planning est en cours d'édition
    if "history_selected" in st.session_state:
        idx = st.session_state["history_selected"]
        if idx < len(st.session_state.planning_history):
            planning = st.session_state.planning_history[idx]

            col_back, col_title = st.columns([1, 5])
            with col_back:
                if st.button("← Retour à la liste"):
                    del st.session_state["history_selected"]
                    st.rerun()
            with col_title:
                st.markdown(f"### ✏️ {planning.get('nom', 'Planning')}")

            st.caption(f"Projet : **{planning.get('projet', 'N/A')}** | Généré le : **{planning.get('date', 'N/A')}** | Localisation : **{planning.get('localisation', 'N/A')}**")

            # Renommer le planning
            col_nom, col_save_nom = st.columns([4, 1])
            with col_nom:
                new_nom = st.text_input("📝 Nom du planning", value=planning.get("nom", "Planning sans titre"))
            with col_save_nom:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Renommer", use_container_width=True):
                    st.session_state.planning_history[idx]["nom"] = new_nom
                    st.success("Renommé !")
                    st.rerun()

            st.markdown("---")
            # ─── Ajustement des phases et périodes ──────────────────────────────
            st.markdown("#### 📅 Phases et périodes — Ajustement")
            st.markdown("""
            <div class="info-box" style="font-size:0.85rem;">
            Modifiez directement le tableau ci-dessous : durées, dates de début/fin, conditions.
            Vous pouvez aussi ajouter ou supprimer des lignes avec les boutons en bas du tableau.
            </div>
            """, unsafe_allow_html=True)

            phases_data = planning.get("phases", [])

            if not phases_data:
                # Tenter d'extraire automatiquement les phases du markdown
                phases_data = extract_phases_from_markdown(planning.get("contenu", ""))
                if phases_data:
                    st.session_state.planning_history[idx]["phases"] = phases_data

            if phases_data:
                df = pd.DataFrame(phases_data)
                # S'assurer que les colonnes existent
                for col in ["phase", "description", "duree", "debut", "fin", "conditions", "responsable"]:
                    if col not in df.columns:
                        df[col] = ""

                edited_df = st.data_editor(
                    df[["phase", "description", "duree", "debut", "fin", "conditions", "responsable"]],
                    use_container_width=True,
                    num_rows="dynamic",
                    column_config={
                        "phase": st.column_config.TextColumn("🏗️ Phase", width="medium"),
                        "description": st.column_config.TextColumn("📝 Description", width="large"),
                        "duree": st.column_config.TextColumn("⏱️ Durée", width="small"),
                        "debut": st.column_config.TextColumn("📅 Début", width="small"),
                        "fin": st.column_config.TextColumn("🏁 Fin", width="small"),
                        "conditions": st.column_config.TextColumn("⚠️ Conditions préalables", width="medium"),
                        "responsable": st.column_config.TextColumn("👷 Responsable", width="small"),
                    },
                    key=f"editor_{idx}"
                )

                col_s1, col_s2 = st.columns([1, 3])
                with col_s1:
                    if st.button("💾 Enregistrer les modifications", use_container_width=True):
                        st.session_state.planning_history[idx]["phases"] = edited_df.to_dict("records")
                        st.success("✅ Modifications enregistrées !")
                        st.rerun()
                with col_s2:
                    # Export phases en CSV
                    csv_data = edited_df.to_csv(index=False, sep=";")
                    st.download_button(
                        "📊 Exporter les phases en CSV",
                        data=csv_data.encode("utf-8"),
                        file_name=f"{planning.get('nom', 'planning').replace(' ', '_')}_phases.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            else:
                st.markdown("""
                <div class="warning-box">
                ⚠️ Aucune phase structurée trouvée. Le planning a été sauvegardé en texte brut uniquement.
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            # ─── Contenu complet du planning ────────────────────────────────────
            with st.expander("📄 Planning complet (texte généré par l'IA)", expanded=False):
                st.markdown(planning.get("contenu", "Aucun contenu disponible"))

            # ─── Exports ────────────────────────────────────────────────────────
            st.markdown("#### 📥 Télécharger ce planning")
            col_dl1, col_dl2, col_dl3 = st.columns(3)
            with col_dl1:
                st.download_button(
                    "📄 Télécharger en TXT",
                    data=planning.get("contenu", "").encode("utf-8"),
                    file_name=f"{planning.get('nom', 'planning').replace(' ', '_')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            with col_dl2:
                md_content = f"# {planning.get('nom', 'Planning')}\n**Projet :** {planning.get('projet','')}\n**Date :** {planning.get('date','')}\n\n{planning.get('contenu', '')}"
                st.download_button(
                    "📝 Télécharger en Markdown",
                    data=md_content.encode("utf-8"),
                    file_name=f"{planning.get('nom', 'planning').replace(' ', '_')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            with col_dl3:
                # Export vers devis
                if st.button("💰 Utiliser pour un devis", use_container_width=True):
                    st.session_state["devis_from_planning"] = planning
                    st.switch_page("pages/8_Devis.py")

            return  # Fin de l'affichage édition

    # ─── Liste des plannings (vue liste) ────────────────────────────────────────
    for i, planning in enumerate(reversed(st.session_state.planning_history)):
        real_idx = len(st.session_state.planning_history) - 1 - i

        col_info, col_btns = st.columns([5, 2])
        with col_info:
            st.markdown(f"""
            <div style="background:white;border:1px solid #E2EBF5;border-radius:12px;padding:1rem 1.2rem;margin-bottom:0.5rem;">
                <strong>📋 {planning.get('nom', f'Planning #{real_idx+1}')}</strong><br>
                <span style="color:#6B7280;font-size:0.85rem;">
                    📁 {planning.get('projet', 'Projet N/A')} &nbsp;|&nbsp;
                    📍 {planning.get('localisation', 'N/A')} &nbsp;|&nbsp;
                    🗓️ {planning.get('date', 'N/A')}
                </span>
            </div>
            """, unsafe_allow_html=True)
        with col_btns:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✏️ Éditer", key=f"edit_{real_idx}", use_container_width=True):
                    st.session_state["history_selected"] = real_idx
                    st.rerun()
            with c2:
                if st.button("🗑️", key=f"del_{real_idx}", use_container_width=True, help="Supprimer"):
                    st.session_state.planning_history.pop(real_idx)
                    st.rerun()


def extract_phases_from_markdown(text: str) -> list:
    """Tente d'extraire les phases depuis le markdown du planning généré."""
    phases = []
    lines = text.split('\n')
    in_table = False
    header_found = False

    for line in lines:
        line = line.strip()
        if '|' not in line:
            in_table = False
            header_found = False
            continue

        cols = [c.strip() for c in line.split('|') if c.strip()]
        if not cols:
            continue

        # Détection du tableau de phases
        if any(kw in line.lower() for kw in ['phase', 'phasage', 'description', 'durée']):
            in_table = True
            header_found = True
            continue

        if header_found and set(c.replace('-','').replace(' ','') for c in cols) == {''}:
            continue  # ligne séparatrice

        if in_table and len(cols) >= 2:
            phase = {
                "phase": cols[0] if len(cols) > 0 else "",
                "description": cols[1] if len(cols) > 1 else "",
                "duree": cols[2] if len(cols) > 2 else "",
                "debut": "",
                "fin": "",
                "conditions": cols[3] if len(cols) > 3 else "",
                "responsable": "",
            }
            if phase["phase"] and phase["phase"] != "Phase":
                phases.append(phase)

    return phases
