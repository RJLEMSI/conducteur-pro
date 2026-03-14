import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector
from lib import db
from utils import GLOBAL_CSS

user_id = page_setup(title="Planning", icon="\U0001f4c5")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.title("\U0001f4c5 Planning")

# ─── Phases types BTP avec durées et couleurs ─────────────────────────────────
PHASES_BTP = [
    {"nom": "Etudes et preparation", "duree": 21, "couleur": "#6C5B7B", "categorie": "preparation"},
    {"nom": "Installation de chantier", "duree": 7, "couleur": "#C06C84", "categorie": "preparation"},
    {"nom": "Terrassement", "duree": 14, "couleur": "#F67280", "categorie": "gros_oeuvre"},
    {"nom": "Fondations", "duree": 21, "couleur": "#F8B500", "categorie": "gros_oeuvre"},
    {"nom": "Elevation / Gros oeuvre", "duree": 45, "couleur": "#1B4F8A", "categorie": "gros_oeuvre"},
    {"nom": "Charpente / Couverture", "duree": 21, "couleur": "#2D6BB4", "categorie": "gros_oeuvre"},
    {"nom": "Menuiseries exterieures", "duree": 14, "couleur": "#45B7D1", "categorie": "second_oeuvre"},
    {"nom": "Electricite", "duree": 21, "couleur": "#E8A838", "categorie": "second_oeuvre"},
    {"nom": "Plomberie / CVC", "duree": 21, "couleur": "#96CEB4", "categorie": "second_oeuvre"},
    {"nom": "Isolation / Platrerie", "duree": 18, "couleur": "#FFEAA7", "categorie": "second_oeuvre"},
    {"nom": "Revetements sols et murs", "duree": 14, "couleur": "#DDA0DD", "categorie": "finitions"},
    {"nom": "Peinture", "duree": 14, "couleur": "#88D8B0", "categorie": "finitions"},
    {"nom": "Amenagements exterieurs", "duree": 14, "couleur": "#FF6B6B", "categorie": "finitions"},
    {"nom": "Nettoyage / Reception", "duree": 7, "couleur": "#4ECDC4", "categorie": "finitions"},
]

STATUT_LABELS = {
    "a_faire": "\u23F3 A faire",
    "en_cours": "\U0001f6A7 En cours",
    "termine": "\u2705 Termine",
    "en_retard": "\u26A0\uFE0F En retard",
}

STATUT_COLORS = {
    "a_faire": "#95a5a6",
    "en_cours": "#1B4F8A",
    "termine": "#27ae60",
    "en_retard": "#e74c3c",
}

# ─── ONGLETS PRINCIPAUX ───────────────────────────────────────────────────────
tab_general, tab_chantier = st.tabs([
    "\U0001f3D7\uFE0F Planning General",
    "\U0001f4CB Calculer un Planning Chantier"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 : PLANNING GÉNÉRAL (Gantt de tous les chantiers)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_general:
    st.subheader("\U0001f3D7\uFE0F Vue d'ensemble de tous les chantiers")

    chantiers = db.get_chantiers(user_id)
    if not chantiers:
        st.info("Aucun chantier en cours. Creez un chantier depuis le Tableau de bord.")
        # Calendrier vide - mois en cours
        from datetime import datetime as _dt, timedelta as _td
        _today = _dt.now()
        _start_m = _today.replace(day=1)
        _end_m = (_today.replace(day=28) + _td(days=4)).replace(day=1) - _td(days=1)
        import plotly.graph_objects as _go
        _fig_e = _go.Figure()
        _fig_e.add_shape(type="line", x0=str(_today.date()), x1=str(_today.date()), y0=-0.5, y1=0.5, line=dict(color="red", width=2, dash="dash"))
        _fig_e.add_annotation(x=str(_today.date()), y=0.3, text="Aujourd'hui", showarrow=False, font=dict(color="red", size=10))
        _fig_e.update_layout(
            xaxis=dict(type="date", range=[str(_start_m.date()), str(_end_m.date())], title="", dtick="D1", tickformat="%d %b"),
            yaxis=dict(visible=False),
            height=200, margin=dict(l=0, r=0, t=10, b=40),
            plot_bgcolor="white",
        )
        _fig_e.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#f0f0f0")
        st.plotly_chart(_fig_e, width="stretch")
    else:
        # Récupérer toutes les phases de l'utilisateur
        all_phases = db.get_all_phases_user(user_id)

        if all_phases:
            # Construire le DataFrame pour le Gantt
            gantt_data = []
            for phase in all_phases:
                chantier_info = phase.get("chantiers", {})
                chantier_nom = chantier_info.get("nom", "Sans nom") if chantier_info else "Sans nom"
                gantt_data.append({
                    "Tache": phase["nom"],
                    "Chantier": chantier_nom,
                    "Debut": phase["date_debut"],
                    "Fin": phase["date_fin"],
                    "Statut": STATUT_LABELS.get(phase.get("statut", "a_faire"), phase.get("statut", "")),
                    "Progression": phase.get("progression", 0),
                    "statut_raw": phase.get("statut", "a_faire"),
                })

            df = pd.DataFrame(gantt_data)
            df["Debut"] = pd.to_datetime(df["Debut"])
            df["Fin"] = pd.to_datetime(df["Fin"])

            # Filtres
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                chantier_filter = st.multiselect(
                    "Filtrer par chantier",
                    options=df["Chantier"].unique().tolist(),
                    default=df["Chantier"].unique().tolist(),
                    key="gantt_filter_chantier"
                )
            with col_f2:
                statut_filter = st.multiselect(
                    "Filtrer par statut",
                    options=list(STATUT_LABELS.values()),
                    default=list(STATUT_LABELS.values()),
                    key="gantt_filter_statut"
                )

            df_filtered = df[df["Chantier"].isin(chantier_filter) & df["Statut"].isin(statut_filter)]

            if not df_filtered.empty:
                # Gantt avec Plotly
                fig = px.timeline(
                    df_filtered,
                    x_start="Debut",
                    x_end="Fin",
                    y="Chantier",
                    color="Statut",
                    hover_data=["Tache", "Progression"],
                    color_discrete_map={
                        STATUT_LABELS["a_faire"]: STATUT_COLORS["a_faire"],
                        STATUT_LABELS["en_cours"]: STATUT_COLORS["en_cours"],
                        STATUT_LABELS["termine"]: STATUT_COLORS["termine"],
                        STATUT_LABELS["en_retard"]: STATUT_COLORS["en_retard"],
                    },
                    title="Planning General - Tous les chantiers"
                )
                fig.update_layout(
                    height=max(400, len(df_filtered["Chantier"].unique()) * 120),
                    xaxis_title="",
                    yaxis_title="",
                    font=dict(size=12),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, width="stretch")

                # Résumé par chantier
                st.subheader("\U0001f4CA Résumé par chantier")
                for ch_name in df_filtered["Chantier"].unique():
                    ch_df = df_filtered[df_filtered["Chantier"] == ch_name]
                    total = len(ch_df)
                    termines = len(ch_df[ch_df["statut_raw"] == "termine"])
                    en_cours = len(ch_df[ch_df["statut_raw"] == "en_cours"])
                    en_retard = len(ch_df[ch_df["statut_raw"] == "en_retard"])
                    pct = int((termines / total) * 100) if total > 0 else 0

                    with st.expander(f"\U0001f3D7\uFE0F {ch_name} — {pct}% termine ({termines}/{total} phases)", expanded=False):
                        st.progress(pct / 100)
                        cols = st.columns(4)
                        cols[0].metric("Total", total)
                        cols[1].metric("Termines", termines)
                        cols[2].metric("En cours", en_cours)
                        cols[3].metric("En retard", en_retard)
            else:
                st.warning("Aucune phase ne correspond aux filtres selectionnes.")
        else:
            st.info("Aucune phase de chantier planifiee. Utilisez l'onglet **Calculer un Planning Chantier** pour commencer.")
            # Calendrier vide - mois en cours
            from datetime import datetime as _dt, timedelta as _td
            _today = _dt.now()
            _start_m = _today.replace(day=1)
            _end_m = (_today.replace(day=28) + _td(days=4)).replace(day=1) - _td(days=1)
            import plotly.graph_objects as _go
            _fig_e = _go.Figure()
            _fig_e.add_shape(type="line", x0=str(_today.date()), x1=str(_today.date()), y0=-0.5, y1=0.5, line=dict(color="red", width=2, dash="dash"))
            _fig_e.add_annotation(x=str(_today.date()), y=0.3, text="Aujourd'hui", showarrow=False, font=dict(color="red", size=10))
            _fig_e.update_layout(
                xaxis=dict(type="date", range=[str(_start_m.date()), str(_end_m.date())], title="", dtick="D1", tickformat="%d %b"),
                yaxis=dict(visible=False),
                height=200, margin=dict(l=0, r=0, t=10, b=40),
                plot_bgcolor="white",
            )
            _fig_e.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#f0f0f0")
            st.plotly_chart(_fig_e, width="stretch")

            # Afficher les chantiers sous forme de cards
            st.subheader("Vos chantiers")
            for ch in chantiers:
                col1, col2 = st.columns([3, 1])
                col1.markdown(f"**{ch.get('nom', 'Sans nom')}** — {ch.get('adresse', '')}")
                col2.caption(ch.get("statut", "en_cours"))


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 : CALCULER UN PLANNING CHANTIER
# ═══════════════════════════════════════════════════════════════════════════════
with tab_chantier:
    st.subheader("\U0001f4CB Calculer le planning d'un chantier")

    # Charger les chantiers pour le selectbox (sans utiliser chantier_selector qui peut poser problème dans les tabs)
    chantiers_list = db.get_chantiers(user_id)
    if not chantiers_list:
        st.info("Aucun chantier disponible. Creez un chantier depuis le Tableau de bord.")
    else:
        chantier_options = {f"{ch.get('nom', 'Sans nom')} — {ch.get('adresse', '')}": ch for ch in chantiers_list}
        selected_label = st.selectbox(
            "Selectionner un chantier",
            options=list(chantier_options.keys()),
            key="planning_calc_chantier_select"
        )
        chantier = chantier_options[selected_label]
        chantier_id = chantier["id"]
        existing_phases = db.get_phases(chantier_id)

        # ─── Si des phases existent déjà ──────────────────────────────────────────
        if existing_phases:
            st.success(f"{len(existing_phases)} phases planifiees pour ce chantier")

            # Gantt du chantier
            phase_data = []
            for p in existing_phases:
                phase_data.append({
                    "Tache": p["nom"],
                    "Debut": p["date_debut"],
                    "Fin": p["date_fin"],
                    "Statut": STATUT_LABELS.get(p.get("statut", "a_faire"), ""),
                    "Progression": p.get("progression", 0),
                    "Categorie": p.get("categorie", "personnalisee"),
                    "id": p["id"],
                    "statut_raw": p.get("statut", "a_faire"),
                })

            df_ch = pd.DataFrame(phase_data)
            df_ch["Debut"] = pd.to_datetime(df_ch["Debut"])
            df_ch["Fin"] = pd.to_datetime(df_ch["Fin"])

            fig_ch = px.timeline(
                df_ch, x_start="Debut", x_end="Fin", y="Tache",
                color="Statut",
                color_discrete_map={
                    STATUT_LABELS["a_faire"]: STATUT_COLORS["a_faire"],
                    STATUT_LABELS["en_cours"]: STATUT_COLORS["en_cours"],
                    STATUT_LABELS["termine"]: STATUT_COLORS["termine"],
                    STATUT_LABELS["en_retard"]: STATUT_COLORS["en_retard"],
                },
                title=f"Planning — {chantier.get('nom', '')}"
            )
            fig_ch.update_layout(
                height=max(350, len(existing_phases) * 45),
                yaxis_title="", xaxis_title="",
                font=dict(size=12),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            )
            fig_ch.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_ch, width="stretch")

            # Tableau de mise à jour des statuts
            st.subheader("\u270F\uFE0F Mettre a jour les phases")
            for i, phase in enumerate(existing_phases):
                with st.expander(f"{phase['nom']} — {STATUT_LABELS.get(phase.get('statut', 'a_faire'), '')}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    new_statut = col1.selectbox(
                        "Statut", ["a_faire", "en_cours", "termine", "en_retard"],
                        index=["a_faire", "en_cours", "termine", "en_retard"].index(phase.get("statut", "a_faire")),
                        format_func=lambda x: STATUT_LABELS.get(x, x),
                        key=f"statut_{phase['id']}"
                    )
                    new_prog = col2.slider(
                        "Progression %", 0, 100, phase.get("progression", 0),
                        key=f"prog_{phase['id']}"
                    )
                    col3.text_input("Notes", value=phase.get("notes", "") or "", key=f"notes_{phase['id']}")

                    if st.button("Sauvegarder", key=f"save_{phase['id']}"):
                        db.update_phase(phase["id"], {
                            "statut": new_statut,
                            "progression": new_prog,
                            "notes": st.session_state.get(f"notes_{phase['id']}", ""),
                        })
                        st.success("Phase mise a jour !")
                        st.rerun()

            # Ajouter une phase personnalisée
            st.markdown("---")
            st.subheader("\u2795 Ajouter une tache personnalisee")
            with st.form("add_custom_phase"):
                c1, c2 = st.columns(2)
                new_nom = c1.text_input("Nom de la tache *")
                new_duree = c2.number_input("Duree (jours)", min_value=1, value=14)
                c3, c4 = st.columns(2)
                new_date_debut = c3.date_input("Date de debut", date.today())
                new_couleur = c4.color_picker("Couleur", "#1B4F8A")
                new_notes = st.text_area("Notes")

                if st.form_submit_button("Ajouter au planning", type="primary") and new_nom:
                    new_date_fin = new_date_debut + timedelta(days=new_duree)
                    result = db.save_phase(user_id, chantier_id, {
                        "nom": new_nom,
                        "categorie": "personnalisee",
                        "date_debut": new_date_debut.isoformat(),
                        "date_fin": new_date_fin.isoformat(),
                        "duree_jours": new_duree,
                        "statut": "a_faire",
                        "progression": 0,
                        "ordre": len(existing_phases) + 1,
                        "couleur": new_couleur,
                        "notes": new_notes,
                    })
                    if result:
                        st.success(f"Tache '{new_nom}' ajoutee !")
                        st.rerun()

            # Supprimer toutes les phases
            st.markdown("---")
            if st.button("\U0001f5D1\uFE0F Reinitialiser le planning de ce chantier", type="secondary"):
                for p in existing_phases:
                    db.delete_phase(p["id"])
                st.success("Planning reinitialise.")
                st.rerun()

        # ─── Aucune phase : proposer la création ──────────────────────────────────
        else:
            st.info("Aucun planning pour ce chantier. Generez-en un ci-dessous.")
            # Calendrier vide - mois en cours
            from datetime import datetime as _dt, timedelta as _td
            _today = _dt.now()
            _start_m = _today.replace(day=1)
            _end_m = (_today.replace(day=28) + _td(days=4)).replace(day=1) - _td(days=1)
            import plotly.graph_objects as _go
            _fig_e = _go.Figure()
            _fig_e.add_shape(type="line", x0=str(_today.date()), x1=str(_today.date()), y0=-0.5, y1=0.5, line=dict(color="red", width=2, dash="dash"))
            _fig_e.add_annotation(x=str(_today.date()), y=0.3, text="Aujourd'hui", showarrow=False, font=dict(color="red", size=10))
            _fig_e.update_layout(
                xaxis=dict(type="date", range=[str(_start_m.date()), str(_end_m.date())], title="", dtick="D1", tickformat="%d %b"),
                yaxis=dict(visible=False),
                height=200, margin=dict(l=0, r=0, t=10, b=40),
                plot_bgcolor="white",
            )
            _fig_e.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#f0f0f0")
            st.plotly_chart(_fig_e, width="stretch")

            st.subheader("\U0001f680 Generer un planning automatique")
            st.markdown("Selectionnez les phases BTP a inclure et definissez la date de debut du chantier.")

            date_debut_chantier = st.date_input(
                "Date de debut du chantier",
                value=date.today(),
                key="date_debut_gen"
            )

            st.markdown("#### Phases a inclure :")

            # Sélection des phases avec durées modifiables
            selected_phases = []
            categories = {"preparation": "Preparation", "gros_oeuvre": "Gros Oeuvre", "second_oeuvre": "Second Oeuvre", "finitions": "Finitions"}

            for cat_key, cat_label in categories.items():
                st.markdown(f"**{cat_label}**")
                cat_phases = [p for p in PHASES_BTP if p["categorie"] == cat_key]
                for phase in cat_phases:
                    col1, col2, col3 = st.columns([0.5, 3, 1.5])
                    include = col1.checkbox("", value=True, key=f"inc_{phase['nom']}")
                    col2.markdown(f"\U0001f539 {phase['nom']}")
                    duree = col3.number_input(
                        "jours", min_value=1, value=phase["duree"],
                        key=f"dur_{phase['nom']}", label_visibility="collapsed"
                    )
                    if include:
                        selected_phases.append({
                            "nom": phase["nom"],
                            "duree": duree,
                            "couleur": phase["couleur"],
                            "categorie": phase["categorie"],
                        })

            # Ajouter des tâches personnalisées
            st.markdown("---")
            st.markdown("#### Taches personnalisees supplementaires")
            nb_custom = st.number_input("Nombre de taches a ajouter", min_value=0, max_value=10, value=0, key="nb_custom")
            for i in range(int(nb_custom)):
                c1, c2, c3 = st.columns([3, 1, 1])
                cnom = c1.text_input(f"Nom tache {i+1}", key=f"cnom_{i}")
                cduree = c2.number_input(f"Duree", min_value=1, value=7, key=f"cdur_{i}")
                ccouleur = c3.color_picker(f"Couleur", "#FF6B6B", key=f"ccol_{i}")
                if cnom:
                    selected_phases.append({
                        "nom": cnom,
                        "duree": cduree,
                        "couleur": ccouleur,
                        "categorie": "personnalisee",
                    })

            if selected_phases:
                # Aperçu
                st.markdown("---")
                st.subheader("\U0001f4C6 Apercu du planning")
                preview_data = []
                current_date = date_debut_chantier
                for idx, phase in enumerate(selected_phases):
                    d_debut = current_date
                    d_fin = d_debut + timedelta(days=phase["duree"])
                    preview_data.append({
                        "Tache": phase["nom"],
                        "Debut": d_debut,
                        "Fin": d_fin,
                        "Duree": f"{phase['duree']}j",
                        "Categorie": phase.get("categorie", ""),
                    })
                    # Phase suivante commence 2 jours avant la fin (chevauchement léger)
                    current_date = d_fin - timedelta(days=min(2, phase["duree"] - 1))

                df_preview = pd.DataFrame(preview_data)
                df_preview["Debut"] = pd.to_datetime(df_preview["Debut"])
                df_preview["Fin"] = pd.to_datetime(df_preview["Fin"])

                fig_preview = px.timeline(
                    df_preview, x_start="Debut", x_end="Fin", y="Tache",
                    color="Categorie",
                    title="Apercu du planning genere",
                    color_discrete_sequence=["#6C5B7B", "#1B4F8A", "#E8A838", "#4ECDC4", "#FF6B6B"],
                )
                fig_preview.update_layout(
                    height=max(350, len(preview_data) * 40),
                    yaxis_title="", xaxis_title="",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                )
                fig_preview.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_preview, width="stretch")

                duree_totale = (pd.to_datetime(preview_data[-1]["Fin"]) - pd.to_datetime(preview_data[0]["Debut"])).days
                st.metric("Duree totale estimee", f"{duree_totale} jours ({duree_totale // 30} mois)")

                # Bouton de validation
                if st.button("\u2705 Valider et enregistrer ce planning", type="primary", width="stretch"):
                    phases_to_save = []
                    current_date = date_debut_chantier
                    for idx, phase in enumerate(selected_phases):
                        d_debut = current_date
                        d_fin = d_debut + timedelta(days=phase["duree"])
                        phases_to_save.append({
                            "nom": phase["nom"],
                            "categorie": phase.get("categorie", "personnalisee"),
                            "date_debut": d_debut.isoformat(),
                            "date_fin": d_fin.isoformat(),
                            "duree_jours": phase["duree"],
                            "statut": "a_faire",
                            "progression": 0,
                            "ordre": idx + 1,
                            "couleur": phase.get("couleur", "#1B4F8A"),
                        })
                        current_date = d_fin - timedelta(days=min(2, phase["duree"] - 1))

                    success = db.save_phases_batch(user_id, chantier_id, phases_to_save)
                    if success:
                        # Mettre à jour les dates du chantier
                        db.update_chantier(chantier_id, {
                            "date_debut": phases_to_save[0]["date_debut"],
                            "date_fin": phases_to_save[-1]["date_fin"],
                        })
                        st.success(f"Planning genere avec {len(phases_to_save)} phases !")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Erreur lors de l'enregistrement.")
