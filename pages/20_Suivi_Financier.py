import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import json
from datetime import datetime, date
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib.supabase_client import get_supabase_client, is_authenticated
from utils import GLOBAL_CSS
import pandas as pd
import plotly.graph_objects as go
from collections import defaultdict

# Page setup
user_id = page_setup("Suivi Financier", icon="📈")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)
require_feature(user_id, "suivi_financier")

# Initialize Supabase client
sb = get_supabase_client()

# Formatting helpers
def fmt(val):
    try:
        return f"{float(val or 0):,.0f} €".replace(",", " ")
    except (ValueError, TypeError):
        return "0 €"

def fmt_pct(val):
    try:
        return f"{float(val or 0):.1f}%"
    except (ValueError, TypeError):
        return "0.0%"

st.title("📈 Suivi Financier")
st.markdown("Vue consolidée des finances par chantier et globale.")

# Load chantiers
try:
    resp = sb.table("chantiers").select("*").eq("user_id", user_id).execute()
    chantiers = resp.data or []
except Exception as e:
    st.error(f"Erreur chargement chantiers: {e}")
    chantiers = []

if not chantiers:
    st.info("Aucun chantier trouvé. Créez d'abord des chantiers dans le module Chantiers.")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Vue Globale",
    "🏗️ Par Chantier",
    "📋 Factures & Devis",
    "📈 Graphiques"
])

# ─── TAB 1: Vue Globale ──────────────────────────────────────────
with tab1:
    st.subheader("Vue Globale — Tous Chantiers")

    total_budget = sum(float(c.get("budget_ht") or 0) for c in chantiers)
    total_facture = sum(float(c.get("facture_ht") or 0) for c in chantiers)
    total_encaisse = sum(float(c.get("encaisse_ht") or 0) for c in chantiers)
    nb_chantiers = len(chantiers)
    nb_actifs = sum(1 for c in chantiers if c.get("statut") == "En cours")
    nb_termines = sum(1 for c in chantiers if c.get("statut") == "Terminé")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Budget Total", fmt(total_budget))
    with col2:
        st.metric("📄 Facturé Total", fmt(total_facture))
    with col3:
        st.metric("✅ Encaissé Total", fmt(total_encaisse))
    with col4:
        reste = total_facture - total_encaisse
        st.metric("⏳ Reste à Encaisser", fmt(reste))

    col5, col6, col7 = st.columns(3)
    with col5:
        st.metric("🏗️ Chantiers Totaux", nb_chantiers)
    with col6:
        st.metric("🔄 En Cours", nb_actifs)
    with col7:
        st.metric("✅ Terminés", nb_termines)

    if total_budget > 0:
        taux_fact = (total_facture / total_budget) * 100
        st.progress(min(taux_fact / 100, 1.0), text=f"Taux de facturation global: {taux_fact:.1f}%")

    st.subheader("Détail par Chantier")
    rows = []
    for c in chantiers:
        budget = float(c.get("budget_ht") or 0)
        facture = float(c.get("facture_ht") or 0)
        encaisse = float(c.get("encaisse_ht") or 0)
        reste_c = facture - encaisse
        taux = (facture / budget * 100) if budget > 0 else 0
        rows.append({
            "Chantier": c.get("nom", ""),
            "Client": c.get("client_nom", ""),
            "Statut": c.get("statut", ""),
            "Budget HT": fmt(budget),
            "Facturé HT": fmt(facture),
            "Encaissé HT": fmt(encaisse),
            "Reste à Enc.": fmt(reste_c),
            "Taux Fact.": fmt_pct(taux),
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

# ─── TAB 2: Par Chantier ─────────────────────────────────────────
with tab2:
    st.subheader("Analyse par Chantier")

    # Build name -> id mapping to avoid passing dict to Supabase
    chantier_options = {c["nom"]: c["id"] for c in chantiers}
    selected_nom = st.selectbox("Sélectionner un chantier", list(chantier_options.keys()))
    selected_id = chantier_options[selected_nom]  # Always a clean UUID string

    chantier_data = next((c for c in chantiers if c["id"] == selected_id), {})
    budget = float(chantier_data.get("budget_ht") or 0)
    facture = float(chantier_data.get("facture_ht") or 0)
    encaisse = float(chantier_data.get("encaisse_ht") or 0)
    avancement = float(chantier_data.get("avancement_pct") or 0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Budget HT", fmt(budget))
    with col2:
        st.metric("📄 Facturé HT", fmt(facture))
    with col3:
        st.metric("✅ Encaissé HT", fmt(encaisse))
    with col4:
        marge = budget - facture
        delta_val = f"{(marge/budget*100):.1f}%" if budget > 0 else "N/A"
        st.metric("📊 Marge Restante", fmt(marge), delta=delta_val)

    st.markdown(f"**Avancement physique:** {fmt_pct(avancement)}")
    st.progress(min(avancement / 100, 1.0))

    try:
        resp_f = sb.table("factures").select("*").eq("user_id", user_id).eq("chantier_id", selected_id).execute()
        factures = resp_f.data or []
    except Exception as e:
        st.warning(f"Erreur factures: {e}")
        factures = []

    try:
        resp_d = sb.table("devis").select("*").eq("user_id", user_id).eq("chantier_id", selected_id).execute()
        devis_list = resp_d.data or []
    except Exception as e:
        st.warning(f"Erreur devis: {e}")
        devis_list = []

    col_f, col_d = st.columns(2)
    with col_f:
        st.subheader(f"📄 Factures ({len(factures)})")
        if factures:
            rows_f = []
            for f in factures:
                rows_f.append({
                    "N°": f.get("numero", ""),
                    "Montant TTC": fmt(f.get("montant_ttc") or f.get("montant_ht") or 0),
                    "Statut": f.get("statut", ""),
                    "Date": str(f.get("date_emission", ""))[:10],
                })
            st.dataframe(pd.DataFrame(rows_f), use_container_width=True)
        else:
            st.info("Aucune facture pour ce chantier.")

    with col_d:
        st.subheader(f"📋 Devis ({len(devis_list)})")
        if devis_list:
            rows_d = []
            for d in devis_list:
                rows_d.append({
                    "N°": d.get("numero", ""),
                    "Montant TTC": fmt(d.get("montant_ttc") or d.get("montant_ht") or 0),
                    "Statut": d.get("statut", "Brouillon"),
                    "Date": str(d.get("date_creation", ""))[:10],
                })
            st.dataframe(pd.DataFrame(rows_d), use_container_width=True)
        else:
            st.info("Aucun devis pour ce chantier.")

    try:
        resp_a = sb.table("achats").select("*, fournisseurs(nom)").eq("user_id", user_id).eq("chantier_id", selected_id).execute()
        achats = resp_a.data or []
    except Exception:
        achats = []

    if achats:
        st.subheader(f"🛒 Achats ({len(achats)})")
        total_achats = sum(float(a.get("montant_ttc") or a.get("montant_ht") or 0) for a in achats)
        st.metric("Total Achats TTC", fmt(total_achats))
        rows_a = []
        for a in achats:
            fourn_nom = ""
            if isinstance(a.get("fournisseurs"), dict):
                fourn_nom = a["fournisseurs"].get("nom", "")
            rows_a.append({
                "Référence": a.get("reference", ""),
                "Fournisseur": fourn_nom,
                "Montant TTC": fmt(a.get("montant_ttc") or a.get("montant_ht") or 0),
                "Statut": a.get("statut", ""),
            })
        st.dataframe(pd.DataFrame(rows_a), use_container_width=True)

# ─── TAB 3: Factures & Devis ─────────────────────────────────────
with tab3:
    st.subheader("Toutes Factures & Devis")

    col_gauche, col_droite = st.columns(2)

    with col_gauche:
        st.markdown("### 📄 Factures")
        try:
            resp_all_f = sb.table("factures").select("*, chantiers(nom)").eq("user_id", user_id).order("created_at", desc=True).execute()
            all_factures = resp_all_f.data or []
        except Exception as e:
            st.warning(f"Erreur: {e}")
            all_factures = []

        if all_factures:
            statuts_f = ["Tous"] + list(set(f.get("statut", "") for f in all_factures if f.get("statut")))
            filtre_statut_f = st.selectbox("Statut facture", statuts_f, key="filtre_f")
            if filtre_statut_f != "Tous":
                all_factures = [f for f in all_factures if f.get("statut") == filtre_statut_f]
            rows_af = []
            for f in all_factures:
                chantier_nom = ""
                if isinstance(f.get("chantiers"), dict):
                    chantier_nom = f["chantiers"].get("nom", "")
                rows_af.append({
                    "N°": f.get("numero", ""),
                    "Chantier": chantier_nom,
                    "Montant TTC": fmt(f.get("montant_ttc") or f.get("montant_ht") or 0),
                    "Statut": f.get("statut", ""),
                    "Date": str(f.get("date_emission", ""))[:10],
                })
            st.dataframe(pd.DataFrame(rows_af), use_container_width=True)
            total_f = sum(float(f.get("montant_ttc") or f.get("montant_ht") or 0) for f in all_factures)
            st.metric("Total affiché", fmt(total_f))
        else:
            st.info("Aucune facture.")

    with col_droite:
        st.markdown("### 📋 Devis")
        try:
            resp_all_d = sb.table("devis").select("*, chantiers(nom)").eq("user_id", user_id).order("created_at", desc=True).execute()
            all_devis = resp_all_d.data or []
        except Exception as e:
            st.warning(f"Erreur: {e}")
            all_devis = []

        if all_devis:
            rows_ad = []
            for d in all_devis:
                chantier_nom = ""
                if isinstance(d.get("chantiers"), dict):
                    chantier_nom = d["chantiers"].get("nom", "")
                rows_ad.append({
                    "N°": d.get("numero", ""),
                    "Chantier": chantier_nom,
                    "Montant TTC": fmt(d.get("montant_ttc") or d.get("montant_ht") or 0),
                    "Statut": d.get("statut", "Brouillon"),
                    "Date": str(d.get("date_creation", ""))[:10],
                })
            st.dataframe(pd.DataFrame(rows_ad), use_container_width=True)
            total_d = sum(float(d.get("montant_ttc") or d.get("montant_ht") or 0) for d in all_devis)
            st.metric("Total affiché", fmt(total_d))
        else:
            st.info("Aucun devis.")

# ─── TAB 4: Graphiques ───────────────────────────────────────────
with tab4:
    st.subheader("Graphiques Financiers")

    if chantiers:
        noms = [c.get("nom", "")[:20] for c in chantiers]
        budgets_v = [float(c.get("budget_ht") or 0) for c in chantiers]
        factures_v = [float(c.get("facture_ht") or 0) for c in chantiers]
        encaisses_v = [float(c.get("encaisse_ht") or 0) for c in chantiers]

        fig = go.Figure(data=[
            go.Bar(name="Budget HT", x=noms, y=budgets_v, marker_color="#1f77b4"),
            go.Bar(name="Facturé HT", x=noms, y=factures_v, marker_color="#ff7f0e"),
            go.Bar(name="Encaissé HT", x=noms, y=encaisses_v, marker_color="#2ca02c"),
        ])
        fig.update_layout(
            title="Budget vs Facturé vs Encaissé par Chantier",
            barmode="group",
            height=400,
            template="plotly_white",
        )
        st.plotly_chart(fig, use_container_width=True)

        statuts_count = defaultdict(int)
        for c in chantiers:
            statuts_count[c.get("statut", "Inconnu")] += 1

        if statuts_count:
            fig2 = go.Figure(data=[go.Pie(
                labels=list(statuts_count.keys()),
                values=list(statuts_count.values()),
                hole=0.4,
            )])
            fig2.update_layout(title="Répartition des Chantiers par Statut", height=350)
            st.plotly_chart(fig2, use_container_width=True)

        with_avancement = [c for c in chantiers if c.get("avancement_pct")]
        if with_avancement:
            st.subheader("Avancement des Chantiers")
            rows_av = []
            for c in with_avancement:
                rows_av.append({
                    "Chantier": c.get("nom", "")[:25],
                    "Avancement (%)": float(c.get("avancement_pct") or 0),
                })
            df_av = pd.DataFrame(rows_av)
            st.bar_chart(df_av.set_index("Chantier")["Avancement (%)"])
    else:
        st.info("Aucune donnée à afficher.")
