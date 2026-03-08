"""
Page 0 — Tableau de bord global ConducteurPro
Vue d'ensemble : chantiers actifs, planning global, finances, alertes + assistant IA.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
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

witk k5:
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
# CORPS PRINCIPAL — 3 colonnes
# ─────────────────────────────────────────────────────────────────────────────────
col_left, col_mid, col_right = st.columns([2, 2, 1.3])

# ══════════════════════ COLONNE GAUCHE — Planning Gantt ══════════════════════════
with col_left:
    st.markdown("### 📅 Planning global — tous chantiers")
    df_gantt = df_c[df_c["date_debut_dt"].notna() & df_c["date_fin_dt"].notna()].copy()
    if df_gantt.empty:
        st.info("Aucun chantier avec dates renseignées.")
    else:
        min_d = min(df_gantt["date_debut_dt"].min(), TODAY - timedelta(days=7))
        max_d = max(df_gantt["date_fin_dt"].max(),   TODAY + timedelta(days=30))
        span  = max((max_d - min_d).days, 1)

        STATUS_COLOR = {
            "En cours":   "#1B6CA8",
            "Planifié":   "#6366F1",
            "Terminé":    "#9CA3AF",
            "En retard":  "#DC2626",
            "En attente": "#F59E0B",
        }
        today_pct = max(0, min(100, (TODAY - min_d).days / span * 100))

        for _, row in df_gantt.sort_values("date_debut_dt").iterrows():
            s_pct = max(0, (row["date_debut_dt"] - min_d).days / span * 100)
            d_pct = max(1, min(100 - s_pct, (row["date_fin_dt"] - row["date_debut_dt"]).days / span * 100))
            av    = float(row.get("avancement_pct", 0) or 0)
            color = STATUS_COLOR.get(str(row.get("statut", "")), "#1B6CA8")
            badge_cls = {
                "En cours": "badge-actif", "Planifié": "badge-planifie",
                "Terminé": "badge-termine", "En retard": "badge-retard",
                "En attente": "badge-attente",
            }.get(str(row.get("statut", "")), "badge-planifie")
            debut_str = row["date_debut_dt"].strftime("%d/%m")
            fin_str   = row["date_fin_dt"].strftime("%d/%m/%y")
            prog_full = d_pct
            prog_done = d_pct * av / 100

            st.markdown(f"""
            <div style="margin-bottom:.7rem;">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.25rem;gap:.5rem;">
                <span style="font-size:.8rem;font-weight:700;color:#0D3B6E;flex:1;
                             white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"
                      title="{row['nom']}">{str(row['nom'])[:42]}</span>
                <span style="display:flex;gap:.4rem;align-items:center;flex-shrink:0;">
                  <span class="badge {badge_cls}">{row.get('statut','')}</span>
                  <span style="font-size:.7rem;color:#9CA3AF;">{debut_str}→{fin_str}</span>
                </span>
              </div>
              <div style="background:#F1F5F9;border-radius:6px;height:18px;position:relative;overflow:visible;">
                <div style="position:absolute;left:{s_pct:.1f}%;width:{prog_full:.1f}%;height:100%;
                            background:{color};opacity:.2;border-radius:6px;"></div>
                <div style="position:absolute;left:{s_pct:.1f}%;width:{prog_done:.1f}%;height:100%;
                            background:{color};border-radius:6px;"></div>
                <div style="position:absolute;left:{today_pct:.1f}%;top:-3px;bottom:-3px;
                            width:2px;background:#EF4444;z-index:10;border-radius:2px;"></div>
                <div style="position:absolute;right:4px;top:0;bottom:0;display:flex;align-items:center;">
                  <span style="font-size:.67rem;font-weight:700;color:{color};">{av:.0f}%</span>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(
            f"<p style='font-size:.72rem;color:#9CA3AF;margin-top:.3rem;'>"
            f"🔴 Ligne rouge = aujourd'hui ({TODAY.strftime('%d/%m/%Y')})</p>",
            unsafe_allow_html=True,
        )

# ══════════════════════ COLONNE MILIEU — Finances & Chantiers ════════════════════
with col_mid:
    st.markdown("### 💰 Avancement financier")
    df_actifs = df_c[df_c["statut"] != "Terminé"].sort_values("budget_ht", ascending=False)
    if df_actifs.empty:
        st.info("Aucun chantier actif.")
    else:
        for _, row in df_actifs.iterrows():
            budget   = float(row.get("budget_ht", 0) or 0)
            fact     = float(row.get("facture_ht", 0) or 0)
            encaisse = float(row.get("encaisse_ht", 0) or 0)
            av       = float(row.get("avancement_pct", 0) or 0)
            p_fact   = (fact / budget * 100) if budget else 0
            reste    = budget - fact
            badge_cls = {
                "En cours": "badge-actif", "Planifié": "badge-planifie",
                "En retard": "badge-retard", "En attente": "badge-attente",
            }.get(str(row.get("statut", "")), "badge-planifie")

            st.markdown(f"""
            <div class="ch-card">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.45rem;">
                <div style="flex:1;min-width:0;">
                  <div style="font-weight:700;font-size:.85rem;color:#0D3B6E;
                              white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"
                       title="{row['nom']}">{str(row['nom'])[:38]}</div>
                  <div style="font-size:.73rem;color:#6B7280;">{row.get('client','')} · {row.get('localisation','')}</div>
                </div>
                <span class="badge {badge_cls}" style="margin-left:.5rem;flex-shrink:0;">{row.get('statut','')}</span>
              </div>
              <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:.3rem;margin-bottom:.45rem;">
                <div style="text-align:center;">
                  <div style="font-size:.65rem;color:#9CA3AF;">Budget HT</div>
                  <div style="font-size:.82rem;font-weight:700;color:#0D3B6E;">{fmt_k(budget)}</div>
                </div>
                <div style="text-align:center;">
                  <div style="font-size:.65rem;color:#9CA3AF;">Facturé</div>
                  <div style="font-size:.82rem;font-weight:700;color:#1B6CA8;">{fmt_k(fact)}</div>
                </div>
                <div style="text-align:center;">
                  <div style="font-size:.65rem;color:#9CA3AF;">Encaissé</div>
                  <div style="font-size:.82rem;font-weight:700;color:#059669;">{fmt_k(encaisse)}</div>
                </div>
                <div style="text-align:center;">
                  <div style="font-size:.65rem;color:#9CA3AF;">Reste fact.</div>
                  <div style="font-size:.82rem;font-weight:700;color:#D97706;">{fmt_k(reste)}</div>
                </div>
              </div>
              <div style="display:flex;align-items:center;gap:.4rem;margin-bottom:.2rem;">
                <span style="font-size:.65rem;color:#6B7280;width:72px;">Facturation</span>
                <div class="prog-wrap" style="flex:1;">
                  <div class="prog-bar" style="width:{p_fact:.0f}%;background:#1B6CA8;"></div>
                </div>
                <span style="font-size:.65rem;color:#1B6CA8;width:30px;text-align:right;">{p_fact:.0f}%</span>
              </div>
              <div style="display:flex;align-items:center;gap:.4rem;">
                <span style="font-size:.65rem;color:#6B7280;width:72px;">Avancement</span>
                <div class="prog-wrap" style="flex:1;">
                  <div class="prog-bar" style="width:{av:.0f}%;background:#059669;"></div>
                </div>
                <span style="font-size:.65rem;color:#059669;width:30px;text-align:right;">{av:.0f}%</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════ COLONNE DROITE — Tâches & Alertes ════════════════════════
with col_right:
    st.markdown("### 🗓️ Tâches à venir")
    if df_e.empty:
        st.info("Aucune tâche planifiée.")
    else:
        for _, etape in df_e.sort_values("date_dt").iterrows():
            date_v    = etape.get("date_dt")
            days_left = int((date_v - TODAY).days) if pd.notna(date_v) else 999
            if days_left < 0:
                bg = "#FEF2F2"; border = "#EF4444"; tag = f"🚨 {abs(days_left)}j retard"
            elif days_left == 0:
                bg = "#FFF7ED"; border = "#F59E0B"; tag = "⚠️ Aujourd'hui"
            elif days_left <= 3:
                bg = "#FFF7ED"; border = "#F59E0B"; tag = f"⚠️ Dans {days_left}j"
            elif days_left <= 7:
                bg = "#FFFBEB"; border = "#D97706"; tag = f"⏰ Dans {days_left}j"
            else:
                bg = "#F8FAFF"; border = "#CBD5E1"
                tag = f"📅 {date_v.strftime('%d/%m') if pd.notna(date_v) else '—'}"
            prio_c = {"Haute": "#DC2626", "Normale": "#6B7280", "Basse": "#9CA3AF"}.get(
                etape.get("priorite", ""), "#6B7280"
            )
            st.markdown(f"""
            <div class="task-item" style="background:{bg};border-color:{border};">
              <div style="font-weight:700;font-size:.8rem;color:#0D3B6E;margin-bottom:.1rem;">
                {etape.get('etape','')}</div>
              <div style="font-size:.7rem;color:#6B7280;">{etape.get('chantier','')}</div>
              <div style="font-size:.7rem;color:#6B7280;">{etape.get('responsable','')}</div>
              <div style="display:flex;justify-content:space-between;margin-top:.3rem;">
                <span style="font-size:.7rem;font-weight:700;color:{border};">{tag}</span>
                <span style="font-size:.68rem;color:{prio_c};">◆ {etape.get('priorite','')}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════ SECTION DOCUMENTS ═══════════════════════════════════════
st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
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
