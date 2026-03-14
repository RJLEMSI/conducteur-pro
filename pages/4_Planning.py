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

# Palette de couleurs par chantier
CHANTIER_COLORS = ["#1B4F8A", "#E67E22", "#2ECC71", "#9B59B6", "#E74C3C", "#1ABC9C", "#F39C12", "#3498DB", "#D35400", "#27AE60", "#8E44AD", "#C0392B", "#16A085", "#2980B9", "#F1C40F"]


user_id = page_setup(title="Planning", icon="\U0001f4c5")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.title("\U0001f4c5 Planning")

# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Phases types BTP avec durées et couleurs ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ
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

# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ ONGLETS PRINCIPAUX ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ
tab_general, tab_chantier = st.tabs([
    "\U0001f3D7\uFE0F Planning General",
    "\U0001f4CB Calculer un Planning Chantier"
])

# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ

# TAB 1 : PLANNING GENERAL
with tab_general:
    st.subheader("\U0001f3D7\uFE0F Vue d'ensemble de tous les chantiers")

    chantiers = db.get_chantiers(user_id)
    all_phases = db.get_all_phases_user(user_id)

    phases_par_chantier_id = {}
    if all_phases:
        for p in all_phases:
            cid = p.get("chantier_id")
            if cid:
                if cid not in phases_par_chantier_id:
                    phases_par_chantier_id[cid] = []
                phases_par_chantier_id[cid].append(p)

    gantt_data = []
    chantier_ids_map = {}
    if chantiers:
        for ch in chantiers:
            ch_nom = ch.get("nom", "Sans nom")
            ch_id = ch.get("id")
            chantier_ids_map[ch_nom] = ch_id
            ch_phases = phases_par_chantier_id.get(ch_id, [])
            if ch_phases:
                dates_debut = [p["date_debut"] for p in ch_phases if p.get("date_debut")]
                dates_fin = [p["date_fin"] for p in ch_phases if p.get("date_fin")]
                if dates_debut and dates_fin:
                    gantt_data.append({"Chantier": ch_nom, "Debut": str(min(dates_debut)), "Fin": str(max(dates_fin)), "Client": ch.get("client_nom", "-"), "Phases": len(ch_phases)})
            elif ch.get("date_debut") and ch.get("date_fin"):
                gantt_data.append({"Chantier": ch_nom, "Debut": str(ch["date_debut"]), "Fin": str(ch["date_fin"]), "Client": ch.get("client_nom", "-"), "Phases": 0})

    plan_container = st.container()
    with plan_container:
        if gantt_data:
            df_gantt = pd.DataFrame(gantt_data)
            unique_ch = list(df_gantt["Chantier"].unique())
            ch_color_map = {name: CHANTIER_COLORS[i % len(CHANTIER_COLORS)] for i, name in enumerate(unique_ch)}
            fig = px.timeline(df_gantt, x_start="Debut", x_end="Fin", y="Chantier", color="Chantier", hover_data=["Client", "Phases"], color_discrete_map=ch_color_map, title="")
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(height=max(250, len(unique_ch) * 80), margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
            event = st.plotly_chart(fig, key="plan_gantt_general", on_select="rerun", width="stretch")

            selected_from_chart = None
            if event and hasattr(event, "selection") and event.selection and event.selection.points:
                pt = event.selection.points[0]
                selected_from_chart = pt.get("y", None) or pt.get("label", None)

            ch_names = [g["Chantier"] for g in gantt_data]
            if selected_from_chart and selected_from_chart in ch_names:
                st.session_state["selected_chantier_general"] = selected_from_chart

            cur_sel = st.session_state.get("selected_chantier_general", ch_names[0] if ch_names else None)
            sel_idx = ch_names.index(cur_sel) if cur_sel in ch_names else 0
            chosen = st.selectbox("\U0001f50d Ou selectionnez un chantier :", ch_names, index=sel_idx, key="select_ch_general")
            st.session_state["selected_chantier_general"] = chosen
        else:
            _today = datetime.now()
            _sm = _today.replace(day=1)
            _em = (_today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            fig = go.Figure()
            fig.add_shape(type="line", x0=str(_today.date()), x1=str(_today.date()), y0=-0.5, y1=0.5, line=dict(color="red", width=2, dash="dash"))
            fig.add_annotation(x=str(_today.date()), y=0.3, text="Aujourd'hui", showarrow=False, font=dict(color="red", size=10))
            fig.update_layout(xaxis=dict(type="date", range=[str(_sm.date()), str(_em.date())], title="", dtick="D1", tickformat="%d %b"), yaxis=dict(visible=False), height=200, margin=dict(l=0, r=0, t=10, b=40), plot_bgcolor="white")
            st.plotly_chart(fig, key="empty_cal_general", width="stretch")
            st.info("Aucun chantier avec des dates. Creez un chantier depuis le Tableau de bord.")
            chosen = None

    # Detail du chantier selectionne
    if chosen and chantiers:
        st.markdown("---")
        ch_data = next((ch for ch in chantiers if ch.get("nom") == chosen), None)
        if ch_data:
            ch_id = ch_data.get("id")
            ch_phases = phases_par_chantier_id.get(ch_id, [])
            st.markdown(f"### \U0001f4cb Planning detaille : {chosen}")
            col_i1, col_i2, col_i3 = st.columns(3)
            col_i1.metric("Client", ch_data.get("client_nom", "-"))
            col_i2.metric("Adresse", ch_data.get("adresse", "-"))
            col_i3.metric("Statut", str(ch_data.get("statut", "-")).replace("_", " ").capitalize())

            if ch_phases:
                ch_phases.sort(key=lambda x: x.get("ordre", 0))
                st.markdown("**Phases du chantier :**")
                h1, h2, h3, h4, h5 = st.columns([3, 1.5, 1.5, 1.2, 0.8])
                h1.markdown("**Phase**")
                h2.markdown("**Debut**")
                h3.markdown("**Fin**")
                h4.markdown("**Statut**")
                h5.markdown("**Progr.**")

                for _ip, ph in enumerate(ch_phases):
                    col_a, col_b, col_c, col_d, col_e = st.columns([3, 1.5, 1.5, 1.2, 0.8])
                    col_a.markdown(f"\U0001f539 **{ph.get('nom', 'Phase')}**")
                    _ph_deb = ph.get("date_debut")
                    _ph_fin = ph.get("date_fin")
                    try:
                        _dv = datetime.strptime(str(_ph_deb), "%Y-%m-%d").date() if _ph_deb else date.today()
                    except Exception:
                        _dv = date.today()
                    try:
                        _fv = datetime.strptime(str(_ph_fin), "%Y-%m-%d").date() if _ph_fin else date.today()
                    except Exception:
                        _fv = date.today()
                    col_b.date_input("d", value=_dv, key=f"ph_deb_{ch_id}_{_ip}", label_visibility="collapsed")
                    col_c.date_input("f", value=_fv, key=f"ph_fin_{ch_id}_{_ip}", label_visibility="collapsed")
                    statut = ph.get("statut", "a_faire")
                    col_d.markdown(f"_{STATUT_LABELS.get(statut, statut)}_")
                    prog = ph.get("progression", 0)
                    col_e.progress(prog / 100 if prog else 0)

                if st.button("\U0001f4be Enregistrer les modifications", key=f"save_phases_{ch_id}", type="primary"):
                    _all_ok = True
                    for _ip2, ph2 in enumerate(ch_phases):
                        _nd = st.session_state.get(f"ph_deb_{ch_id}_{_ip2}")
                        _nf = st.session_state.get(f"ph_fin_{ch_id}_{_ip2}")
                        if _nd and _nf and ph2.get("id"):
                            try:
                                db.update_phase(ph2["id"], {"date_debut": str(_nd), "date_fin": str(_nf), "duree_jours": (_nf - _nd).days})
                            except Exception as _e:
                                _all_ok = False
                                st.error(f"Erreur phase {ph2.get('nom')}: {_e}")
                    if _all_ok:
                        all_deb = [st.session_state.get(f"ph_deb_{ch_id}_{i}") for i in range(len(ch_phases))]
                        all_fin = [st.session_state.get(f"ph_fin_{ch_id}_{i}") for i in range(len(ch_phases))]
                        all_deb = [d for d in all_deb if d]
                        all_fin = [d for d in all_fin if d]
                        if all_deb and all_fin:
                            db.update_chantier(ch_id, {"date_debut": str(min(all_deb)), "date_fin": str(max(all_fin))})
                        st.success("Dates mises a jour !")
                        st.rerun()

                # Mini Gantt des phases
                phase_gantt = []
                for ph in ch_phases:
                    if ph.get("date_debut") and ph.get("date_fin"):
                        phase_gantt.append({"Phase": ph["nom"], "Debut": str(ph["date_debut"]), "Fin": str(ph["date_fin"]), "Statut": STATUT_LABELS.get(ph.get("statut", "a_faire"), "A faire")})
                if phase_gantt:
                    df_ph = pd.DataFrame(phase_gantt)
                    fig_ph = px.timeline(df_ph, x_start="Debut", x_end="Fin", y="Phase", color="Statut", title="")
                    fig_ph.update_yaxes(autorange="reversed")
                    fig_ph.update_layout(height=max(250, len(phase_gantt) * 40), margin=dict(l=0, r=0, t=10, b=0))
                    st.plotly_chart(fig_ph, key=f"phase_gantt_{ch_id}", width="stretch")
            else:
                st.warning("Aucune phase detaillee pour ce chantier.")
                if st.button(f"\U0001f916 Generer le planning IA pour {chosen}", key=f"gen_plan_{ch_id}"):
                    _date_debut = ch_data.get("date_debut")
                    if _date_debut and isinstance(_date_debut, str):
                        try:
                            _start = datetime.strptime(_date_debut, "%Y-%m-%d").date()
                        except Exception:
                            _start = date.today()
                    elif _date_debut and hasattr(_date_debut, "year"):
                        _start = _date_debut
                    else:
                        _start = date.today()
                    _phases_to_save = []
                    _current = _start
                    for _idx_p, _phase in enumerate(PHASES_BTP):
                        _d_debut = _current
                        _d_fin = _d_debut + timedelta(days=_phase["duree"])
                        _phases_to_save.append({"nom": _phase["nom"], "categorie": _phase.get("categorie", "personnalisee"), "date_debut": _d_debut.isoformat(), "date_fin": _d_fin.isoformat(), "duree_jours": _phase["duree"], "statut": "a_faire", "progression": 0, "ordre": _idx_p + 1, "couleur": _phase.get("couleur", "#1B4F8A")})
                        _current = _d_fin - timedelta(days=min(2, _phase["duree"] - 1))
                    _ok = db.save_phases_batch(user_id, ch_id, _phases_to_save)
                    if _ok:
                        db.update_chantier(ch_id, {"date_debut": _phases_to_save[0]["date_debut"], "date_fin": _phases_to_save[-1]["date_fin"]})
                        st.success(f"Planning genere avec {len(_phases_to_save)} phases !")
                        st.rerun()
                    else:
                        st.error("Erreur lors de la generation.")

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

        # ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Si des phases existent déjà ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ
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

        # ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Aucune phase : proposer la création ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ
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
            st.plotly_chart(_fig_e, width="stretch", key="empty_cal_per_chantier")

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
