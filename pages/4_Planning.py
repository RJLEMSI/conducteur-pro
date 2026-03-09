"""
Page 4 — Planning
Vue planning général de tous les chantiers avec diagramme de Gantt interactif.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils import GLOBAL_CSS, render_sidebar

st.set_page_config(page_title="Planning | ConducteurPro", page_icon="📅", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_sidebar()

# ── Données de démonstration ───────────────────────────────────────
def _default_chantiers():
    return [
        {"nom": "Résidence Les Lilas", "client": "SCI Les Lilas", "statut": "En cours",
         "date_debut": "2025-01-15", "date_fin": "2025-06-30", "budget_ht": 285000,
         "lot": "Gros Œuvre", "responsable": "Martin D.", "avancement_pct": 65},
        {"nom": "Bureau Delta", "client": "Entreprise Delta", "statut": "En cours",
         "date_debut": "2025-03-01", "date_fin": "2025-07-15", "budget_ht": 124000,
         "lot": "Électricité", "responsable": "Leroy S.", "avancement_pct": 30},
        {"nom": "École Molière", "client": "Mairie de Meyzieu", "statut": "Planifié",
         "date_debut": "2025-05-01", "date_fin": "2025-12-31", "budget_ht": 520000,
         "lot": "TCE", "responsable": "Garcia P.", "avancement_pct": 0},
        {"nom": "Entrepôt LogiNord", "client": "LogiNord SAS", "statut": "En cours",
         "date_debut": "2025-02-10", "date_fin": "2025-08-20", "budget_ht": 380000,
         "lot": "Charpente", "responsable": "Martin D.", "avancement_pct": 45},
        {"nom": "Villa Méditerranée", "client": "M. Dubois", "statut": "Terminé",
         "date_debut": "2024-09-01", "date_fin": "2025-02-28", "budget_ht": 67000,
         "lot": "Rénovation", "responsable": "Leroy S.", "avancement_pct": 100},
    ]

def _default_etapes():
    return [
        {"chantier": "Résidence Les Lilas", "etape": "Fondations", "responsable": "Martin D.",
         "date_debut": "2025-01-15", "date_fin": "2025-02-28", "statut": "Terminé", "priorite": "Haute"},
        {"chantier": "Résidence Les Lilas", "etape": "Élévation RDC", "responsable": "Martin D.",
         "date_debut": "2025-03-01", "date_fin": "2025-04-15", "statut": "En cours", "priorite": "Haute"},
        {"chantier": "Résidence Les Lilas", "etape": "Élévation R+1", "responsable": "Martin D.",
         "date_debut": "2025-04-16", "date_fin": "2025-05-30", "statut": "Planifié", "priorite": "Normale"},
        {"chantier": "Résidence Les Lilas", "etape": "Toiture", "responsable": "Garcia P.",
         "date_debut": "2025-06-01", "date_fin": "2025-06-30", "statut": "Planifié", "priorite": "Normale"},
        {"chantier": "Bureau Delta", "etape": "Câblage principal", "responsable": "Leroy S.",
         "date_debut": "2025-03-01", "date_fin": "2025-04-15", "statut": "En cours", "priorite": "Haute"},
        {"chantier": "Bureau Delta", "etape": "Tableau électrique", "responsable": "Leroy S.",
         "date_debut": "2025-04-16", "date_fin": "2025-05-30", "statut": "Planifié", "priorite": "Normale"},
        {"chantier": "Bureau Delta", "etape": "Mise en service", "responsable": "Leroy S.",
         "date_debut": "2025-06-01", "date_fin": "2025-07-15", "statut": "Planifié", "priorite": "Basse"},
        {"chantier": "Entrepôt LogiNord", "etape": "Terrassement", "responsable": "Martin D.",
         "date_debut": "2025-02-10", "date_fin": "2025-03-15", "statut": "Terminé", "priorite": "Haute"},
        {"chantier": "Entrepôt LogiNord", "etape": "Structure métallique", "responsable": "Martin D.",
         "date_debut": "2025-03-16", "date_fin": "2025-05-30", "statut": "En cours", "priorite": "Haute"},
        {"chantier": "Entrepôt LogiNord", "etape": "Bardage", "responsable": "Garcia P.",
         "date_debut": "2025-06-01", "date_fin": "2025-08-20", "statut": "Planifié", "priorite": "Normale"},
        {"chantier": "École Molière", "etape": "Préparation chantier", "responsable": "Garcia P.",
         "date_debut": "2025-05-01", "date_fin": "2025-06-15", "statut": "Planifié", "priorite": "Haute"},
        {"chantier": "École Molière", "etape": "Gros œuvre", "responsable": "Garcia P.",
         "date_debut": "2025-06-16", "date_fin": "2025-09-30", "statut": "Planifié", "priorite": "Haute"},
        {"chantier": "École Molière", "etape": "Second œuvre", "responsable": "Leroy S.",
         "date_debut": "2025-10-01", "date_fin": "2025-12-31", "statut": "Planifié", "priorite": "Normale"},
    ]

if "planning_chantiers" not in st.session_state:
    st.session_state["planning_chantiers"] = _default_chantiers()
if "planning_etapes" not in st.session_state:
    st.session_state["planning_etapes"] = _default_etapes()

df_c = pd.DataFrame(st.session_state["planning_chantiers"])
df_e = pd.DataFrame(st.session_state["planning_etapes"])

# ── En-tête ────────────────────────────────────────────────────────
st.markdown("""<div style="background:linear-gradient(135deg,#1a237e,#3949ab);border-radius:16px;
padding:28px 32px;color:#fff;margin-bottom:20px;">
<h1 style="margin:0;font-size:1.8rem;">📅 Planning Général</h1>
<p style="margin:4px 0 0;opacity:0.85;">Vue d'ensemble de tous vos chantiers et de leurs étapes.</p>
</div>""", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Chantiers actifs", len(df_c[df_c["statut"] == "En cours"]))
k2.metric("Chantiers planifiés", len(df_c[df_c["statut"] == "Planifié"]))
k3.metric("Étapes en cours", len(df_e[df_e["statut"] == "En cours"]))
k4.metric("Étapes à venir", len(df_e[df_e["statut"] == "Planifié"]))

st.divider()

# ── Onglets ────────────────────────────────────────────────────────
tab_global, tab_detail, tab_etapes = st.tabs(["📊 Planning Global", "🔍 Détail par Chantier", "📋 Liste des Étapes"])

# ── TAB 1: Planning Global (Gantt) ─────────────────────────────────
with tab_global:
    st.markdown("### 🗓️ Diagramme de Gantt — Tous les chantiers")

    # Filtre statut
    fc1, fc2 = st.columns([1, 3])
    with fc1:
        filtre_statut = st.multiselect("Filtrer par statut", ["En cours", "Planifié", "Terminé"],
                                        default=["En cours", "Planifié"], key="gantt_statut")

    df_gantt = df_c[df_c["statut"].isin(filtre_statut)].copy()
    df_gantt["date_debut"] = pd.to_datetime(df_gantt["date_debut"])
    df_gantt["date_fin"] = pd.to_datetime(df_gantt["date_fin"])

    if len(df_gantt) > 0:
        color_map = {"En cours": "#2196F3", "Planifié": "#FF9800", "Terminé": "#4CAF50"}

        fig = px.timeline(
            df_gantt, x_start="date_debut", x_end="date_fin", y="nom",
            color="statut", color_discrete_map=color_map,
            hover_data=["client", "lot", "responsable", "budget_ht", "avancement_pct"],
            labels={"nom": "Chantier", "statut": "Statut"}
        )
        fig.update_layout(
            height=max(300, len(df_gantt) * 70),
            yaxis_title="", xaxis_title="",
            font=dict(size=13),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        fig.update_yaxes(autorange="reversed")

        # Ligne "Aujourd'hui"
        today = datetime.now()
        fig.add_shape(type="line", x0=today, x1=today,
                      y0=-0.5, y1=len(df_gantt) - 0.5,
                      line=dict(color="red", width=2, dash="dash"))
        fig.add_annotation(x=today, y=-0.3, text="Aujourd'hui",
                           showarrow=False, font=dict(color="red", size=11))

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucun chantier ne correspond aux filtres sélectionnés.")

    # Gantt détaillé par étapes
    st.markdown("### 📐 Détail des étapes par chantier")

    df_e_gantt = df_e.copy()
    df_e_gantt["date_debut"] = pd.to_datetime(df_e_gantt["date_debut"])
    df_e_gantt["date_fin"] = pd.to_datetime(df_e_gantt["date_fin"])

    # Filtrer par chantiers sélectionnés
    chantiers_visibles = df_gantt["nom"].tolist() if len(df_gantt) > 0 else []
    df_e_filtered = df_e_gantt[df_e_gantt["chantier"].isin(chantiers_visibles)]

    if len(df_e_filtered) > 0:
        # Créer un label combiné pour l'axe Y
        df_e_filtered = df_e_filtered.copy()
        df_e_filtered["label"] = df_e_filtered["chantier"] + " — " + df_e_filtered["etape"]

        etape_colors = {"Terminé": "#4CAF50", "En cours": "#2196F3", "Planifié": "#FF9800"}

        fig2 = px.timeline(
            df_e_filtered, x_start="date_debut", x_end="date_fin", y="label",
            color="statut", color_discrete_map=etape_colors,
            hover_data=["responsable", "priorite"],
            labels={"label": "Étape", "statut": "Statut"}
        )
        fig2.update_layout(
            height=max(400, len(df_e_filtered) * 45),
            yaxis_title="", xaxis_title="",
            font=dict(size=11),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        fig2.update_yaxes(autorange="reversed")

        fig2.add_shape(type="line", x0=today, x1=today,
                       y0=-0.5, y1=len(df_e_filtered) - 0.5,
                       line=dict(color="red", width=2, dash="dash"))

        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Aucune étape à afficher.")

# ── TAB 2: Détail par Chantier ─────────────────────────────────────
with tab_detail:
    st.markdown("### 🏗️ Fiche détaillée par chantier")

    chantier_choisi = st.selectbox("Sélectionner un chantier", df_c["nom"].tolist(), key="detail_chantier")

    ch = df_c[df_c["nom"] == chantier_choisi].iloc[0]
    etapes_ch = df_e[df_e["chantier"] == chantier_choisi]

    # Fiche chantier
    statut_color = {"En cours": "#2196F3", "Planifié": "#FF9800", "Terminé": "#4CAF50"}
    sc = statut_color.get(ch["statut"], "#666")

    st.markdown(f"""
    <div style="background:#1e1e2e;border-radius:14px;padding:20px 24px;margin-bottom:16px;
                border-left:5px solid {sc};">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <h3 style="color:#fff;margin:0;">{ch['nom']}</h3>
                <p style="color:#aaa;margin:4px 0 0;">Client : {ch['client']} · Lot : {ch['lot']} · Responsable : {ch['responsable']}</p>
            </div>
            <div style="text-align:right;">
                <span style="background:{sc};color:#fff;padding:5px 14px;border-radius:20px;font-size:0.85rem;
                             font-weight:600;">{ch['statut']}</span>
                <br/><span style="color:#4FC3F7;font-size:1.1rem;font-weight:700;">{ch['budget_ht']:,.0f} € HT</span>
            </div>
        </div>
        <div style="margin-top:12px;">
            <div style="background:#333;border-radius:8px;height:12px;overflow:hidden;">
                <div style="background:linear-gradient(90deg,#4CAF50,#8BC34A);height:100%;width:{ch['avancement_pct']}%;
                            border-radius:8px;"></div>
            </div>
            <span style="color:#aaa;font-size:0.82rem;">Avancement : {ch['avancement_pct']}% · Du {ch['date_debut']} au {ch['date_fin']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Étapes du chantier
    if len(etapes_ch) > 0:
        st.markdown("#### 📋 Étapes du chantier")
        for _, e in etapes_ch.iterrows():
            ec = statut_color.get(e["statut"], "#666")
            prio_icon = {"Haute": "🔴", "Normale": "🟡", "Basse": "🟢"}.get(e["priorite"], "⚪")
            st.markdown(f"""
            <div style="background:#1a1a2e;border-radius:10px;padding:12px 16px;margin-bottom:8px;
                        border-left:3px solid {ec};">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-weight:600;color:#fff;">{e['etape']}</span>
                        <span style="color:#aaa;margin-left:10px;font-size:0.82rem;">{prio_icon} {e['priorite']}</span>
                    </div>
                    <span style="background:{ec};color:#fff;padding:2px 10px;border-radius:16px;
                                 font-size:0.75rem;">{e['statut']}</span>
                </div>
                <span style="color:#888;font-size:0.8rem;">{e['responsable']} · {e['date_debut']} → {e['date_fin']}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Aucune étape définie pour ce chantier.")

    # Liens rapides
    st.divider()
    lc1, lc2, lc3 = st.columns(3)
    with lc1:
        st.page_link("pages/10_Facturation.py", label="🧾 Facturation", icon="🧾")
    with lc2:
        st.page_link("pages/11_Documents.py", label="📂 Documents", icon="📂")
    with lc3:
        st.page_link("pages/0_Tableau_de_bord.py", label="📊 Tableau de bord", icon="📊")

# ── TAB 3: Liste des Étapes ────────────────────────────────────────
with tab_etapes:
    st.markdown("### 📋 Toutes les étapes")

    # Filtres
    ef1, ef2, ef3 = st.columns(3)
    with ef1:
        f_ch = st.multiselect("Chantier", df_e["chantier"].unique().tolist(), key="etapes_chantier")
    with ef2:
        f_st = st.multiselect("Statut", ["Terminé", "En cours", "Planifié"], key="etapes_statut")
    with ef3:
        f_pr = st.multiselect("Priorité", ["Haute", "Normale", "Basse"], key="etapes_prio")

    df_display = df_e.copy()
    if f_ch:
        df_display = df_display[df_display["chantier"].isin(f_ch)]
    if f_st:
        df_display = df_display[df_display["statut"].isin(f_st)]
    if f_pr:
        df_display = df_display[df_display["priorite"].isin(f_pr)]

    df_show = df_display.rename(columns={
        "chantier": "Chantier", "etape": "Étape", "responsable": "Responsable",
        "date_debut": "Début", "date_fin": "Fin", "statut": "Statut", "priorite": "Priorité"
    })
    st.dataframe(df_show[["Chantier", "Étape", "Responsable", "Début", "Fin", "Statut", "Priorité"]],
                 use_container_width=True, hide_index=True)
