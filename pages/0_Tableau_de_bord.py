"""
Page 0 — Tableau de bord global ConducteurPro
Vue d'ensemble : chantiers actifs, planning global, finances, alertes + assistant IA.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime, timedelta
from utils import GLOBAL_CSS, render_sidebar

st.set_page_config(
    page_title="Tableau de bord · ConducteurPro",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_sidebar()

st.markdown("""<style>
.kpi-card {
    background:white;border:1px solid #E2EBF5;border-radius:14px;
    padding:1.2rem 1rem;text-align:center;
    box-shadow:0 2px 8px rgba(0,0,0,.04);height:100%;
}
.kpi-value { font-size:1.75rem;font-weight:800;color:#0D3B6E;line-height:1.1; }
.kpi-label { font-size:.78rem;color:#6B7280;margin-top:.3rem;font-weight:600;text-transform:uppercase;letter-spacing:.04em; }
.kpi-delta { font-size:.78rem;margin-top:.35rem; }
.prog-wrap { background:#F1F5F9;border-radius:6px;height:10px;overflow:hidden;margin-top:.3rem; }
.prog-bar   { height:100%;border-radius:6px; }
.ch-card {
    background:white;border:1px solid #E2EBF5;border-radius:12px;
    padding:.9rem 1.1rem;margin-bottom:.65rem;
    box-shadow:0 1px 4px rgba(0,0,0,.03);
}
.task-item {
    padding:.65rem .9rem;border-radius:8px;margin-bottom:.45rem;
    border-left:3px solid;
}
.badge { display:inline-block;padding:.18rem .65rem;border-radius:20px;font-size:.72rem;font-weight:700; }
.badge-actif    { background:#D1FAE5;color:#065F46; }
.badge-planifie { background:#DBEAFE;color:#1E40AF; }
.badge-termine  { background:#F3F4F6;color:#6B7280; }
.badge-retard   { background:#FEE2E2;color:#991B1B; }
.badge-attente  { background:#FEF3C7;color:#92400E; }
.doc-card {
    background:white;border:1px solid #E2EBF5;border-radius:10px;
    padding:.7rem 1rem;margin-bottom:.45rem;
    box-shadow:0 1px 4px rgba(0,0,0,.03);
    display:flex;align-items:center;justify-content:space-between;
}
.doc-icon { font-size:1.4rem;margin-right:.7rem; }
.doc-info { flex:1;min-width:0; }
.doc-name { font-weight:700;font-size:.82rem;color:#0D3B6E; }
.doc-meta { font-size:.7rem;color:#6B7280; }
.doc-badge { display:inline-block;padding:.15rem .55rem;border-radius:12px;font-size:.68rem;font-weight:600; }
.doc-valid { background:#D1FAE5;color:#065F46; }
.doc-attente { background:#FEF3C7;color:#92400E; }
.doc-brouillon { background:#F3F4F6;color:#6B7280; }
</style>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────────
# SESSION STATE — DONNÉES CHANTIERS
# ─────────────────────────────────────────────────────────────────────────────────
TODAY = datetime.now()

def _default_chantiers():
    return pd.DataFrame([
        {"nom": "Résidence Les Pins — Gros Œuvre",  "client": "SCI Les Pins",
         "statut": "En cours",  "date_debut": "2025-01-15", "date_fin": "2025-06-30",
         "budget_ht": 285000, "facture_ht": 142500, "encaisse_ht": 114000,
         "avancement_pct": 50, "localisation": "Lyon (69)", "metier": "🧱 Maçon", "notes": ""},
        {"nom": "Villa Beaumont — Rénovation complète", "client": "M. Beaumont Jean",
         "statut": "En cours",  "date_debut": "2025-03-01", "date_fin": "2025-07-15",
         "budget_ht": 67000, "facture_ht": 20000, "encaisse_ht": 10000,
         "avancement_pct": 25, "localisation": "Villeurbanne (69)", "metier": "🏗️ Général", "notes": ""},
        {"nom": "Immeuble Colbert — Plomberie",  "client": "Syndic Colbert",
         "statut": "Planifié", "date_debut": "2025-04-01", "date_fin": "2025-05-31",
         "budget_ht": 38500, "facture_ht": 0, "encaisse_ht": 0,
         "avancement_pct": 0,  "localisation": "Bron (69)", "metier": "🔧 Plombier", "notes": ""},
        {"nom": "Lotissement Verdure — Électricité", "client": "Promoteur Verdure SAS",
         "statut": "En cours", "date_debut": "2025-02-10", "date_fin": "2025-08-31",
         "budget_ht": 124000, "facture_ht": 45000, "encaisse_ht": 45000,
         "avancement_pct": 35, "localisation": "Décines (69)", "metier": "⚡ Électricien", "notes": ""},
        {"nom": "École Pasteur — Ravalement", "client": "Mairie de Meyzieu",
         "statut": "Terminé",  "date_debut": "2024-09-01", "date_fin": "2024-12-20",
         "budget_ht": 52000, "facture_ht": 52000, "encaisse_ht": 52000,
         "avancement_pct": 100, "localisation": "Meyzieu (69)", "metier": "🎨 Peintre", "notes": "Solde reçu"},
    ])

def _default_etapes():
    return pd.DataFrame([
        {"chantier": "Résidence Les Pins", "etape": "Livraison armatures HA",
         "responsable": "Chef chantier Dupont", "date_echeance": (TODAY + timedelta(days=2)).strftime("%Y-%m-%d"),
         "statut": "À faire", "priorite": "Haute"},
        {"chantier": "Résidence Les Pins", "etape": "Coulage dalle R+1",
         "responsable": "Équipe maçonnerie",   "date_echeance": (TODAY + timedelta(days=9)).strftime("%Y-%m-%d"),
         "statut": "À faire", "priorite": "Haute"},
        {"chantier": "Villa Beaumont", "etape": "Réception chape carreleur",
         "responsable": "CDT Martin",           "date_echeance": (TODAY + timedelta(days=14)).strftime("%Y-%m-%d"),
         "statut": "En cours", "priorite": "Normale"},
        {"chantier": "Immeuble Colbert", "etape": "Commande matériaux plomberie",
         "responsable": "CDT Lefèvre",          "date_echeance": (TODAY + timedelta(days=4)).strftime("%Y-%m-%d"),
         "statut": "À faire", "priorite": "Haute"},
        {"chantier": "Lotissement Verdure", "etape": "Levée réserves CONSUEL",
         "responsable": "Élec. Moreau",         "date_echeance": (TODAY - timedelta(days=3)).strftime("%Y-%m-%d"),
         "statut": "En retard", "priorite": "Haute"},
        {"chantier": "Résidence Les Pins", "etape": "Réunion de chantier hebdo",
         "responsable": "Tous corps d'état",    "date_echeance": (TODAY + timedelta(days=6)).strftime("%Y-%m-%d"),
         "statut": "À faire", "priorite": "Normale"},
    ])

def _default_documents():
    return pd.DataFrame([
        {"chantier": "Résidence Les Pins", "type": "Devis", "nom": "Devis gros oeuvre lot 1",
         "date": "2025-01-10", "statut_doc": "Validé", "montant": 142500, "fichier": "devis_pins_lot1.pdf"},
        {"chantier": "Résidence Les Pins", "type": "Facture", "nom": "Facture acompte 50%",
         "date": "2025-02-15", "statut_doc": "Envoyée", "montant": 71250, "fichier": "fact_pins_acompte.pdf"},
        {"chantier": "Villa Beaumont", "type": "Devis", "nom": "Devis rénovation complète",
         "date": "2025-02-20", "statut_doc": "Validé", "montant": 67000, "fichier": "devis_beaumont.pdf"},
        {"chantier": "Villa Beaumont", "type": "Plan", "nom": "Plans architecte RDC + R1",
         "date": "2025-02-25", "statut_doc": "Validé", "montant": 0, "fichier": "plans_beaumont.pdf"},
        {"chantier": "Immeuble Colbert", "type": "Devis", "nom": "Devis plomberie sanitaire",
         "date": "2025-03-15", "statut_doc": "En attente", "montant": 38500, "fichier": "devis_colbert_plomb.pdf"},
        {"chantier": "Lotissement Verdure", "type": "Facture", "nom": "Facture situation 1",
         "date": "2025-03-01", "statut_doc": "Payée", "montant": 45000, "fichier": "fact_verdure_sit1.pdf"},
        {"chantier": "Lotissement Verdure", "type": "CR", "nom": "CR réunion chantier 12/02",
         "date": "2025-02-12", "statut_doc": "Validé", "montant": 0, "fichier": "cr_verdure_120225.pdf"},
        {"chantier": "École Pasteur", "type": "Facture", "nom": "Facture solde ravalement",
         "date": "2024-12-20", "statut_doc": "Payée", "montant": 52000, "fichier": "fact_pasteur_solde.pdf"},
        {"chantier": "École Pasteur", "type": "PV", "nom": "PV réception travaux",
         "date": "2024-12-22", "statut_doc": "Signé", "montant": 0, "fichier": "pv_pasteur.pdf"},
    ])

if "tdb_chantiers" not in st.session_state:
    st.session_state.tdb_chantiers = _default_chantiers()
if "tdb_etapes" not in st.session_state:
    st.session_state.tdb_etapes = _default_etapes()
if "tdb_documents" not in st.session_state:
    st.session_state.tdb_documents = _default_documents()

df_c = st.session_state.tdb_chantiers.copy()
df_e = st.session_state.tdb_etapes.copy()

# Parse dates
for col in ["date_debut", "date_fin"]:
    df_c[col + "_dt"] = pd.to_datetime(df_c[col], errors="coerce")
df_e["date_dt"] = pd.to_datetime(df_e["date_echeance"], errors="coerce")

# ─────────────────────────────────────────────────────────────────────────────────
# EN-TÊTE
# ─────────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-header">
    <h2>🏗️ Tableau de bord — ConducteurPro</h2>
    <p>Vue globale de vos chantiers · Planning · Finances · Alertes · {TODAY.strftime('%A %d %B %Y').capitalize()}</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────────
# KPI ROW
# ─────────────────────────────────────────────────────────────────────────────────
nb_actifs    = int((df_c["statut"] == "En cours").sum())
nb_planifies = int((df_c["statut"] == "Planifié").sum())
nb_termines  = int((df_c["statut"] == "Terminé").sum())
ca_total     = float(df_c["budget_ht"].fillna(0).sum())
facture_tot  = float(df_c["facture_ht"].fillna(0).sum())
encaisse_tot = float(df_c["encaisse_ht"].fillna(0).sum())
reste_fact   = ca_total - facture_tot

taches_urgentes = df_e[df_e["date_dt"].notna() & (df_e["date_dt"] <= TODAY + timedelta(days=7))]
taches_retard   = df_e[df_e["date_dt"].notna() & (df_e["date_dt"] < TODAY)]
nb_urgent = len(taches_urgentes)
nb_retard = len(taches_retard)

def fmt_k(val):
    """Format number as k€ or €"""
    v = float(val)
    if v >= 1000:
        return f"{v/1000:.0f}k€"
    return f"{v:.0f}€"

pct_fact = (facture_tot / ca_total * 100) if ca_total else 0
pct_enc  = (encaisse_tot / facture_tot * 100) if facture_tot else 0
color_r  = "#D97706" if reste_fact > 0 else "#6B7280"
color_u  = "#DC2626" if nb_retard > 0 else ("#D97706" if nb_urgent > 0 else "#059669")
icon_u   = "🚨" if nb_retard > 0 else ("⚠️" if nb_urgent > 0 else "✅")

k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    with st.popover(f"**{nb_actifs}** ⚡ En cours", use_container_width=True):
        st.markdown("#### Répartition des chantiers")
        for statut_label, count, clr in [
            ("En cours", nb_actifs, "#059669"), ("Planifié", nb_planifies, "#1E40AF"),
            ("Terminé", nb_termines, "#6B7280"),
        ]:
            st.markdown(f"<span style='color:{clr};font-weight:700;font-size:1.1rem;'>{count}</span> {statut_label}", unsafe_allow_html=True)
        st.divider()
        st.markdown("**Chantiers en cours :**")
        for _, r in df_c[df_c["statut"] == "En cours"].iterrows():
            av = float(r.get("avancement_pct", 0) or 0)
            st.markdown(f"- **{r['nom']}** — {r.get('client','')}\n  📍 {r.get('localisation','')} · Avancement {av:.0f}%")
    st.markdown(f'<div style="text-align:center;font-size:.72rem;color:#6B7280;margin-top:-.5rem;">{nb_planifies} planifié · {nb_termines} terminé</div>', unsafe_allow_html=True)

with k2:
    with st.popover(f"**{fmt_k(ca_total)}** 💼 CA total", use_container_width=True):
        st.markdown("#### Budget par chantier")
        for _, r in df_c.sort_values("budget_ht", ascending=False).iterrows():
            b = float(r.get("budget_ht", 0) or 0)
            st.markdown(f"- **{r['nom'][:30]}** — {fmt_k(b)}")
        st.divider()
        st.metric("CA total HT", f"{ca_total:,.0f} €".replace(",", " "))
    st.markdown(f'<div style="text-align:center;font-size:.72rem;color:#6B7280;margin-top:-.5rem;">{len(df_c)} chantier(s)</div>', unsafe_allow_html=True)

with k3:
    with st.popover(f"**{fmt_k(facture_tot)}** 📄 Facturé", use_container_width=True):
        st.markdown("#### Détail facturation par chantier")
        for _, r in df_c.iterrows():
            b = float(r.get("budget_ht", 0) or 0)
            f_ht = float(r.get("facture_ht", 0) or 0)
            pct = (f_ht / b * 100) if b else 0
            st.markdown(f"**{r['nom'][:28]}**")
            st.progress(min(pct / 100, 1.0), text=f"{fmt_k(f_ht)} / {fmt_k(b)} ({pct:.0f}%)")
        st.divider()
        st.metric("Taux de facturation", f"{pct_fact:.0f}%")
    st.markdown(f'<div style="text-align:center;font-size:.72rem;color:#059669;margin-top:-.5rem;">{pct_fact:.0f}% du CA</div>', unsafe_allow_html=True)

with k4:
    with st.popover(f"**{fmt_k(encaisse_tot)}** ✅ Encaissé", use_container_width=True):
        st.markdown("#### Encaissement par chantier")
        for _, r in df_c.iterrows():
            f_ht = float(r.get("facture_ht", 0) or 0)
            e_ht = float(r.get("encaisse_ht", 0) or 0)
            reste_e = f_ht - e_ht
            st.markdown(f"**{r['nom'][:28]}**")
            col_a, col_b = st.columns(2)
            col_a.metric("Encaissé", fmt_k(e_ht))
            col_b.metric("Reste", fmt_k(reste_e), delta=f"-{fmt_k(reste_e)}" if reste_e > 0 else "OK")
    st.markdown(f'<div style="text-align:center;font-size:.72rem;color:#059669;margin-top:-.5rem;">{pct_enc:.0f}% du facturé</div>', unsafe_allow_html=True)

with k5:
    with st.popover(f"**{fmt_k(reste_fact)}** ⏳ Reste", use_container_width=True):
        st.markdown("#### Reste à facturer par chantier")
        for _, r in df_c.iterrows():
            b = float(r.get("budget_ht", 0) or 0)
            f_ht = float(r.get("facture_ht", 0) or 0)
            reste = b - f_ht
            if reste > 0:
                st.markdown(f"- **{r['nom'][:28]}** — **{fmt_k(reste)}** à facturer")
        st.divider()
        st.metric("Total reste à facturer", f"{reste_fact:,.0f} €".replace(",", " "))
    st.markdown(f'<div style="text-align:center;font-size:.72rem;color:{color_r};margin-top:-.5rem;">À encaisser</div>', unsafe_allow_html=True)

with k6:
    with st.popover(f"**{nb_urgent}** {icon_u} Urgent 7j", use_container_width=True):
        st.markdown("#### Tâches urgentes (prochains 7 jours)")
        if taches_retard.empty and taches_urgentes.empty:
            st.success("Aucune tâche urgente !")
        for _, t in taches_retard.iterrows():
            jours = abs(int((t["date_dt"] - TODAY).days))
            st.error(f"🚨 **{t.get('etape','')}** — {t.get('chantier','')}\n{jours}j de retard · {t.get('responsable','')}")
        for _, t in taches_urgentes[~taches_urgentes.index.isin(taches_retard.index)].iterrows():
            jours = int((t["date_dt"] - TODAY).days)
            st.warning(f"⚠️ **{t.get('etape','')}** — {t.get('chantier','')}\nDans {jours}j · {t.get('responsable','')}")
    st.markdown(f'<div style="text-align:center;font-size:.72rem;color:#DC2626;margin-top:-.5rem;">{nb_retard} en retard !</div>', unsafe_allow_html=True)

st.markdown("<div style='margin-top:1.3rem;'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────────
# 🤖 ASSISTANT / DEMANDE RAPIDE
# ─────────────────────────────────────────────────────────────────────────────────
with st.expander("🤖 Assistant ConducteurPro — Demande rapide", expanded=True):
    st.markdown(
        "<p style='color:#374151;font-size:.92rem;margin-bottom:.6rem;'>"
        "Décrivez votre besoin en langage naturel — devis, planning, analyse technique, question BTP… "
        "L'assistant génère directement le contenu ou vous guide vers le bon outil."
        "</p>",
        unsafe_allow_html=True,
    )
    col_req, col_btn = st.columns([5, 1])
    with col_req:
        demande = st.text_area(
            "Demande",
            placeholder="Ex : Crée-moi un devis pour la rénovation d'une salle de bain 8m² à Lyon, client M. Dupont, peinture + carrelage. Budget estimé 4 500 €…",
            height=80,
            key="tdb_demande",
            label_visibility="collapsed",
        )
    with col_btn:
        st.markdown("<div style='margin-top:.35rem;'></div>", unsafe_allow_html=True)
        send = st.button("🚀 Envoyer", type="primary", use_container_width=True, key="tdb_send")

    if send and demande.strip():
        with st.spinner("L'assistant analyse votre demande…"):
            try:
                import anthropic
                _api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
                if not _api_key:
                    raise ValueError("Clé ANTHROPIC_API_KEY manquante dans les secrets Streamlit.")
                ai = anthropic.Anthropic(api_key=_api_key)
                _system = (
                    "Tu es l'assistant IA de ConducteurPro, une application pour professionnels du BTP français.\n"
                    "Ton rôle : analyser la demande et fournir une réponse directement utile et opérationnelle.\n\n"
                    "Si c'est une demande de DEVIS : génère un devis structuré (sections, postes, quantités, prix unitaires HT, total HT).\n"
                    "Si c'est une demande de PLANNING : génère un planning par phases avec durées et responsables.\n"
                    "Si c'est une question TECHNIQUE (béton, structure, thermique, acoustique) : réponds précisément.\n"
                    "Si c'est une analyse de DCE / PLU / document : explique la démarche et les points clés.\n"
                    "Sinon : réponds professionnellement en français.\n\n"
                    "Termine TOUJOURS par : 🔗 **Outil recommandé :** [nom de la page ConducteurPro] — [raison courte]\n"
                    "Pages disponibles : Tableau de bord, Devis, Métrés, DCE, Études, Planning, PLU, Synthèse, Abonnement."
                )
                resp = ai.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=2500,
                    system=_system,
                    messages=[{"role": "user", "content": demande}],
                )
                st.session_state["tdb_answer"]  = resp.content[0].text
                st.session_state["tdb_question"] = demande
            except Exception as ex:
                st.error(f"Erreur : {ex}")
                st.session_state["tdb_answer"] = None

    if st.session_state.get("tdb_answer"):
        st.markdown("---")
        st.markdown(
            f"<p style='font-size:.85rem;color:#6B7280;margin-bottom:.4rem;'>"
            f"📝 <em>{st.session_state.get('tdb_question','')[:120]}</em></p>",
            unsafe_allow_html=True,
        )
        st.markdown(st.session_state["tdb_answer"])

        c1, c2 = st.columns([2, 1])
        with c1:
            st.download_button(
                "📥 Télécharger la réponse (.txt)",
                data=st.session_state["tdb_answer"].encode("utf-8"),
                file_name=f"conducteurpro_{TODAY.strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True,
                key="dl_answer",
            )
        with c2:
            if st.button("🗑️ Effacer", use_container_width=True, key="clear_answer"):
                st.session_state["tdb_answer"]  = None
                st.session_state["tdb_question"] = None
                st.rerun()

st.markdown("<div style='margin-top:.8rem;'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────── PLANNING INTERACTIF ──────────────────

st.markdown("""---""")
st.markdown("## 📅 Planning Global — Vue Interactive")
st.markdown('<p style="font-size:0.92rem;color:#666;">Visualisez l\'avancement de tous vos chantiers. Cliquez sur un chantier pour voir les détails.</p>', unsafe_allow_html=True)

# ── Gantt Chart Plotly ──────────────────────────────────────────────
df_c = st.session_state.tdb_chantiers.copy()
df_e_all = st.session_state.tdb_etapes.copy()

color_map_statut = {
    "En cours": "#2196F3",
    "Planifié": "#FF9800",
    "Terminé": "#4CAF50",
}

gantt_data = []
for _, row in df_c.iterrows():
    gantt_data.append({
        "Chantier": row["nom"].split("—")[0].strip() if "—" in row["nom"] else row["nom"],
        "Début": row["date_debut"],
        "Fin": row["date_fin"],
        "Statut": row["statut"],
        "Avancement": f'{row["avancement_pct"]}%',
        "Client": row.get("client", ""),
    })

df_gantt = pd.DataFrame(gantt_data)
df_gantt["Début"] = pd.to_datetime(df_gantt["Début"])
df_gantt["Fin"] = pd.to_datetime(df_gantt["Fin"])

fig = px.timeline(
    df_gantt,
    x_start="Début",
    x_end="Fin",
    y="Chantier",
    color="Statut",
    color_discrete_map=color_map_statut,
    hover_data=["Client", "Avancement"],
    title="",
)
fig.update_yaxes(autorange="reversed")
fig.update_layout(
    height=55 * len(df_gantt) + 80,
    margin=dict(l=10, r=10, t=10, b=30),
    font=dict(size=13),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, title_text=""),
    xaxis=dict(
        title="",
        showgrid=True,
        gridcolor="#eee",
    ),
    yaxis=dict(title=""),
    plot_bgcolor="white",
)
# Ligne rouge pour aujourd'hui
today_ts = pd.Timestamp.now()
fig.add_shape(type="line", x0=today_ts, x1=today_ts, y0=0, y1=1, yref="paper",
             line=dict(color="red", width=2, dash="dash"))
fig.add_annotation(x=today_ts, y=1, yref="paper", text="Aujourd'hui",
                   showarrow=False, font=dict(color="red", size=11), yshift=10)

# Afficher le pourcentage sur les barres
for i, row in df_gantt.iterrows():
    mid_date = row["Début"] + (row["Fin"] - row["Début"]) / 2
    fig.add_annotation(
        x=mid_date, y=row["Chantier"],
        text=f'<b>{row["Avancement"]}</b>',
        showarrow=False,
        font=dict(color="white", size=12),
    )

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── Détail par chantier (cartes cliquables) ────────────────────────
st.markdown("### 🔍 Détail par chantier")
st.markdown('<p style="font-size:0.88rem;color:#888;margin-top:-8px;">Cliquez sur un chantier pour voir budget, avancement et tâches associées.</p>', unsafe_allow_html=True)

# Calculer nombre de colonnes selon le nombre de chantiers
n_chantiers = len(df_c)
cols_per_row = min(n_chantiers, 3)

rows_needed = (n_chantiers + cols_per_row - 1) // cols_per_row
idx = 0
for r in range(rows_needed):
    cols = st.columns(cols_per_row, gap="medium")
    for c_idx in range(cols_per_row):
        if idx >= n_chantiers:
            break
        ch = df_c.iloc[idx]
        nom_court = ch["nom"].split("—")[0].strip() if "—" in ch["nom"] else ch["nom"]
        statut = ch["statut"]
        avance = ch["avancement_pct"]
        budget = ch["budget_ht"]
        facture = ch.get("facture_ht", 0)
        encaisse_val = ch.get("encaisse", 0)
        reste = budget - facture
        localisation = ch.get("localisation", "")
        client_name = ch.get("client", "")

        badge_color = {"En cours": "#2196F3", "Planifié": "#FF9800", "Terminé": "#4CAF50"}.get(statut, "#999")

        with cols[c_idx]:
            # Card with popover
            st.markdown(f"""<div style="background:#fff;border-radius:12px;padding:16px;border:1px solid #e0e0e0;
                box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:4px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <span style="font-weight:700;font-size:0.95rem;">{nom_court}</span>
                    <span style="background:{badge_color};color:#fff;padding:3px 10px;border-radius:20px;font-size:0.75rem;">{statut}</span>
                </div>
                <div style="font-size:0.82rem;color:#666;margin-bottom:6px;">📍 {localisation} · {client_name}</div>
                <div style="background:#eee;border-radius:8px;height:10px;overflow:hidden;margin-bottom:4px;">
                    <div style="background:{badge_color};height:100%;width:{avance}%;border-radius:8px;"></div>
                </div>
                <div style="font-size:0.78rem;color:#888;text-align:right;">{avance}% avancement</div>
            </div>""", unsafe_allow_html=True)

            with st.popover(f"📋 Détails {nom_court}", use_container_width=True):
                st.markdown(f"#### {ch['nom']}")
                st.markdown(f"**Client :** {client_name}")
                st.markdown(f"**Localisation :** {localisation}")
                st.markdown(f"**Période :** {ch['date_debut']} → {ch['date_fin']}")
                st.markdown("---")

                # Budget
                met1, met2, met3, met4 = st.columns(4)
                met1.metric("Budget HT", fmt_k(budget))
                met2.metric("Facturé", fmt_k(facture))
                met3.metric("Encaissé", fmt_k(encaisse_val))
                met4.metric("Reste", fmt_k(reste))

                # Progress bars
                pct_f = int(facture / budget * 100) if budget > 0 else 0
                st.markdown(f"""
                <div style="margin:8px 0;">
                  <div style="font-size:0.8rem;color:#555;">Facturation : {pct_f}%</div>
                  <div style="background:#eee;border-radius:6px;height:8px;overflow:hidden;">
                    <div style="background:#2196F3;height:100%;width:{pct_f}%;border-radius:6px;"></div>
                  </div>
                </div>
                <div style="margin:8px 0;">
                  <div style="font-size:0.8rem;color:#555;">Avancement : {avance}%</div>
                  <div style="background:#eee;border-radius:6px;height:8px;overflow:hidden;">
                    <div style="background:#4CAF50;height:100%;width:{avance}%;border-radius:6px;"></div>
                  </div>
                </div>""", unsafe_allow_html=True)

                # Tâches liées
                nom_base = nom_court.split("—")[0].strip() if "—" in nom_court else nom_court
                # Match tasks by partial name
                taches_ch = df_e_all[df_e_all["chantier"].str.contains(nom_base.split()[0], case=False, na=False)]
                if not taches_ch.empty:
                    st.markdown("**Prochaines tâches :**")
                    for _, t in taches_ch.iterrows():
                        prio_icon = "🔴" if t.get("priorite") == "Haute" else "🟡" if t.get("priorite") == "Moyenne" else "🟢"
                        st.markdown(f"- {prio_icon} **{t['etape']}** — {t.get('responsable', '')} · {t.get('date_echeance', '')}")
                else:
                    st.markdown("_Aucune tâche planifiée_")

                # Documents liés
                docs_ch = st.session_state.tdb_documents[
                    st.session_state.tdb_documents["chantier"].str.contains(nom_base.split()[0], case=False, na=False)
                ]
                if not docs_ch.empty:
                    st.markdown("**Documents associés :**")
                    for _, d in docs_ch.iterrows():
                        st.markdown(f"- 📄 {d['titre']} ({d.get('statut', '')})")

        idx += 1

# ── Tâches urgentes (section compacte) ─────────────────────────────
st.markdown("---")
col_taches_l, col_taches_r = st.columns([2, 1])

with col_taches_l:
    st.markdown("### ⚡ Tâches à venir")
    today = pd.Timestamp.now().normalize()
    df_etapes = st.session_state.tdb_etapes.copy()
    df_etapes["date_dt"] = pd.to_datetime(df_etapes["date_echeance"], errors="coerce")
    df_etapes_sorted = df_etapes.sort_values("date_dt")

    for _, t in df_etapes_sorted.iterrows():
        delta = (t["date_dt"] - today).days if pd.notna(t["date_dt"]) else 999
        if delta < 0:
            time_label = f"⚠️ {abs(delta)}j retard"
            time_color = "#e53935"
        elif delta == 0:
            time_label = "📌 Aujourd'hui"
            time_color = "#FF9800"
        elif delta <= 7:
            time_label = f"⏰ Dans {delta}j"
            time_color = "#FF9800"
        else:
            time_label = f"📅 {t.get('date_echeance', '')}"
            time_color = "#666"

        prio = t.get("priorite", "Normale")
        prio_dot = "🔴" if prio == "Haute" else "🟡" if prio == "Moyenne" else "🟢"

        st.markdown(f"""<div style="background:#fff;border-radius:10px;padding:10px 14px;margin-bottom:6px;
            border-left:4px solid {time_color};box-shadow:0 1px 4px rgba(0,0,0,0.05);">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-weight:600;font-size:0.9rem;">{prio_dot} {t['etape']}</span>
                <span style="font-size:0.78rem;color:{time_color};font-weight:600;">{time_label} · {prio_dot} {prio}</span>
            </div>
            <div style="font-size:0.8rem;color:#888;margin-top:2px;">{t['chantier']} · {t.get('responsable', '')}</div>
        </div>""", unsafe_allow_html=True)

with col_taches_r:
    st.markdown("### 📊 Résumé financier")
    total_budget = df_c["budget_ht"].sum()
    total_facture = df_c["facture_ht"].sum()
    total_encaisse = df_c["encaisse"].sum()
    total_reste = total_budget - total_facture

    st.metric("Budget total", fmt_k(total_budget))
    st.metric("Total facturé", fmt_k(total_facture), delta=f"{int(total_facture/total_budget*100)}% du budget" if total_budget > 0 else "")
    st.metric("Total encaissé", fmt_k(total_encaisse), delta=f"{int(total_encaisse/total_facture*100)}% du facturé" if total_facture > 0 else "")
    st.metric("Reste à facturer", fmt_k(total_reste))


st.markdown("### 📂 Documents & Pièces")
st.markdown("<p style='font-size:.85rem;color:#6B7280;margin-top:-.5rem;margin-bottom:.8rem;'>Retrouvez tous vos documents classés par type. Devis, factures, plans, comptes-rendus…</p>", unsafe_allow_html=True)

df_docs = st.session_state.tdb_documents.copy()
doc_type_icons = {"Devis": "📝", "Facture": "💰", "Plan": "📐", "CR": "📋", "PV": "✍️", "Photo": "📷", "Autre": "📎"}

col_f1, col_f2, col_f3 = st.columns([2, 2, 3])
with col_f1:
    filtre_type = st.selectbox("Type de document", ["Tous"] + sorted(df_docs["type"].unique().tolist()), key="doc_filtre_type")
with col_f2:
    filtre_chantier = st.selectbox("Chantier", ["Tous"] + sorted(df_docs["chantier"].unique().tolist()), key="doc_filtre_ch")
with col_f3:
    filtre_statut = st.selectbox("Statut", ["Tous"] + sorted(df_docs["statut_doc"].unique().tolist()), key="doc_filtre_statut")

df_docs_f = df_docs.copy()
if filtre_type != "Tous":
    df_docs_f = df_docs_f[df_docs_f["type"] == filtre_type]
if filtre_chantier != "Tous":
    df_docs_f = df_docs_f[df_docs_f["chantier"] == filtre_chantier]
if filtre_statut != "Tous":
    df_docs_f = df_docs_f[df_docs_f["statut_doc"] == filtre_statut]

if df_docs_f.empty:
    st.info("Aucun document ne correspond aux filtres sélectionnés.")
else:
    for _, doc in df_docs_f.sort_values("date", ascending=False).iterrows():
        icon = doc_type_icons.get(doc.get("type", ""), "📎")
        badge_cls = {"Validé": "doc-valid", "Payée": "doc-valid", "Signé": "doc-valid",
                     "En attente": "doc-attente", "Envoyée": "doc-attente"}.get(
                     str(doc.get("statut_doc", "")), "doc-brouillon")
        montant_str = f" — <strong>{fmt_k(float(doc.get('montant', 0) or 0))}</strong>" if float(doc.get("montant", 0) or 0) > 0 else ""
        st.markdown(f"""
        <div class="doc-card">
          <span class="doc-icon">{icon}</span>
          <div class="doc-info">
            <div class="doc-name">{doc.get('nom','')}</div>
            <div class="doc-meta">{doc.get('chantier','')} · {doc.get('date','')} · {doc.get('fichier','')}{montant_str}</div>
          </div>
          <span class="doc-badge {badge_cls}">{doc.get('statut_doc','')}</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown(f"<div style='font-size:.75rem;color:#9CA3AF;margin-top:.3rem;'>{len(df_docs_f)} document(s) affiché(s) sur {len(df_docs)}</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────────
# SECTION GESTION (expander)
# ─────────────────────────────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
with st.expander("⚙️ Gérer les chantiers, étapes et exporter", expanded=False):
    tab_ch, tab_et, tab_exp = st.tabs(["🏗️ Chantiers", "📋 Étapes & tâches", "📦 Export / Import"])

    with tab_ch:
        st.markdown("Ajoutez, modifiez ou supprimez vos chantiers. Chaque ligne = un chantier.")
        _ch_src = st.session_state.tdb_chantiers.copy()
        for _dc in ["date_debut", "date_fin"]:
            _ch_src[_dc] = pd.to_datetime(_ch_src[_dc], errors="coerce")
        df_ch_edit = st.data_editor(
            _ch_src,
            use_container_width=True, num_rows="dynamic",
            key="editor_tdb_chantiers",
            column_config={
                "nom":            st.column_config.TextColumn("Nom du chantier", width="large"),
                "client":         st.column_config.TextColumn("Client"),
                "statut":         st.column_config.SelectboxColumn("Statut",
                                      options=["En cours","Planifié","Terminé","En attente","En retard"]),
                "date_debut":     st.column_config.DateColumn("Début", format="DD/MM/YYYY"),
                "date_fin":       st.column_config.DateColumn("Fin prévue", format="DD/MM/YYYY"),
                "budget_ht":      st.column_config.NumberColumn("Budget HT (€)", format="%.0f €", min_value=0),
                "facture_ht":     st.column_config.NumberColumn("Facturé HT (€)", format="%.0f €", min_value=0),
                "encaisse_ht":    st.column_config.NumberColumn("Encaissé HT (€)", format="%.0f €", min_value=0),
                "avancement_pct": st.column_config.NumberColumn("Avancement %", min_value=0, max_value=100),
                "localisation":   st.column_config.TextColumn("Localisation"),
                "metier":         st.column_config.TextColumn("Métier"),
                "notes":          st.column_config.TextColumn("Notes"),
            }
        )
        if st.button("💾 Sauvegarder les chantiers", type="primary", key="save_tdb_ch"):
            st.session_state.tdb_chantiers = df_ch_edit
            st.success("✅ Chantiers mis à jour !")
            st.rerun()

    with tab_et:
        st.markdown("Planifiez les étapes clés et jalons de chaque chantier.")
        df_et_src  = st.session_state.tdb_etapes.drop(columns=["date_dt"], errors="ignore")
        df_et_src["date_echeance"] = pd.to_datetime(df_et_src["date_echeance"], errors="coerce")
        df_et_edit = st.data_editor(
            df_et_src, use_container_width=True, num_rows="dynamic",
            key="editor_tdb_etapes",
            column_config={
                "chantier":      st.column_config.TextColumn("Chantier", width="medium"),
                "etape":         st.column_config.TextColumn("Étape / Tâche", width="large"),
                "responsable":   st.column_config.TextColumn("Responsable"),
                "date_echeance": st.column_config.DateColumn("Échéance", format="DD/MM/YYYY"),
                "statut":        st.column_config.SelectboxColumn("Statut",
                                     options=["À faire","En cours","Terminé","Bloqué","En retard"]),
                "priorite":      st.column_config.SelectboxColumn("Priorité",
                                     options=["Haute","Normale","Basse"]),
            }
        )
        if st.button("💾 Sauvegarder les étapes", type="primary", key="save_tdb_et"):
            st.session_state.tdb_etapes = df_et_edit
            st.success("✅ Étapes mises à jour !")
            st.rerun()

    with tab_exp:
        c_ex1, c_ex2 = st.columns(2)
        with c_ex1:
            st.markdown("**📤 Exporter**")
            export_data = {
                "date_export": TODAY.strftime("%d/%m/%Y %H:%M"),
                "chantiers": st.session_state.tdb_chantiers.to_dict("records"),
                "etapes":    st.session_state.tdb_etapes.drop(columns=["date_dt"], errors="ignore").to_dict("records"),
            }
            st.download_button(
                "📥 Exporter tout (JSON)",
                data=json.dumps(export_data, ensure_ascii=False, indent=2, default=str).encode(),
                file_name=f"tableau_bord_{TODAY.strftime('%Y%m%d')}.json",
                mime="application/json", use_container_width=True, key="export_tdb_json",
            )
            csv_ch = st.session_state.tdb_chantiers.to_csv(index=False).encode("utf-8")
            st.download_button("📋 Chantiers (CSV)", data=csv_ch,
                               file_name="chantiers.csv", mime="text/csv",
                               use_container_width=True, key="export_tdb_csv")
        with c_ex2:
            st.markdown("**📥 Importer**")
            imp_file = st.file_uploader("Importer JSON", type=["json"], key="imp_tdb")
            if imp_file:
                try:
                    data_imp = json.loads(imp_file.read().decode())
                    if "chantiers" in data_imp:
                        st.session_state.tdb_chantiers = pd.DataFrame(data_imp["chantiers"])
                    if "etapes" in data_imp:
                        st.session_state.tdb_etapes = pd.DataFrame(data_imp["etapes"])
                    st.success("✅ Données importées !")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Erreur import : {ex}")
            if st.button("🔄 Réinitialiser aux données exemple", key="reset_tdb"):
                st.session_state.tdb_chantiers = _default_chantiers()
                st.session_state.tdb_etapes    = _default_etapes()
                st.success("✅ Données réinitialisées !")
                st.rerun()
