"""
Page 10 — Facturation & Commandes
Gestion des factures, acomptes, situations, et suivi des commandes fournisseurs.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils import GLOBAL_CSS, render_sidebar

st.set_page_config(page_title="Facturation · ConducteurPro", page_icon="🧾", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_sidebar()

# ── Données de démonstration ────────────────────────────────────────
def _default_factures():
    return [
        {"ref": "FACT-2025-001", "chantier": "Résidence Les Pins", "type": "Situation",
         "objet": "Situation n°1 — Gros œuvre fondations", "montant_ht": 71250,
         "tva": 14250, "montant_ttc": 85500, "date_emission": "2025-02-15",
         "date_echeance": "2025-03-15", "statut": "Payée", "client": "SCI Les Pins"},
        {"ref": "FACT-2025-002", "chantier": "Résidence Les Pins", "type": "Situation",
         "objet": "Situation n°2 — Élévation RDC", "montant_ht": 71250,
         "tva": 14250, "montant_ttc": 85500, "date_emission": "2025-04-01",
         "date_echeance": "2025-05-01", "statut": "Envoyée", "client": "SCI Les Pins"},
        {"ref": "FACT-2025-003", "chantier": "Villa Beaumont", "type": "Acompte",
         "objet": "Acompte 30% — Rénovation complète", "montant_ht": 20100,
         "tva": 2010, "montant_ttc": 22110, "date_emission": "2025-03-10",
         "date_echeance": "2025-04-10", "statut": "Payée", "client": "M. Beaumont Jean"},
        {"ref": "FACT-2025-004", "chantier": "Lotissement Verdure", "type": "Situation",
         "objet": "Situation n°1 — Électricité lots 1-5", "montant_ht": 45000,
         "tva": 9000, "montant_ttc": 54000, "date_emission": "2025-03-01",
         "date_echeance": "2025-03-31", "statut": "En retard", "client": "Promoteur Verdure SAS"},
        {"ref": "FACT-2025-005", "chantier": "École Pasteur", "type": "Solde",
         "objet": "Facture solde — Ravalement façade", "montant_ht": 52000,
         "tva": 10400, "montant_ttc": 62400, "date_emission": "2024-12-20",
         "date_echeance": "2025-01-20", "statut": "Payée", "client": "Mairie de Meyzieu"},
        {"ref": "FACT-2025-006", "chantier": "Immeuble Colbert", "type": "Acompte",
         "objet": "Acompte démarrage — Plomberie", "montant_ht": 11550,
         "tva": 2310, "montant_ttc": 13860, "date_emission": "2025-04-05",
         "date_echeance": "2025-05-05", "statut": "Brouillon", "client": "Syndic Colbert"},
    ]

def _default_commandes():
    return [
        {"ref": "CMD-2025-001", "chantier": "Résidence Les Pins", "fournisseur": "Point P Lyon",
         "objet": "Béton C25/30 — 45 m³", "montant_ht": 6750, "date_commande": "2025-01-20",
         "date_livraison": "2025-02-05", "statut": "Livrée"},
        {"ref": "CMD-2025-002", "chantier": "Résidence Les Pins", "fournisseur": "AcierPlus",
         "objet": "Armatures HA — Lot fondations", "montant_ht": 12400, "date_commande": "2025-02-01",
         "date_livraison": "2025-03-10", "statut": "En cours"},
        {"ref": "CMD-2025-003", "chantier": "Villa Beaumont", "fournisseur": "Cedeo",
         "objet": "Sanitaires + robinetterie salle de bain", "montant_ht": 3200, "date_commande": "2025-03-05",
         "date_livraison": "2025-03-20", "statut": "Livrée"},
        {"ref": "CMD-2025-004", "chantier": "Lotissement Verdure", "fournisseur": "Rexel",
         "objet": "Câblage électrique lots 1-5", "montant_ht": 8900, "date_commande": "2025-02-15",
         "date_livraison": "2025-03-15", "statut": "En cours"},
        {"ref": "CMD-2025-005", "chantier": "Immeuble Colbert", "fournisseur": "Brossette",
         "objet": "Tubes cuivre + raccords plomberie", "montant_ht": 4600, "date_commande": "2025-04-10",
         "date_livraison": "2025-05-01", "statut": "Commandée"},
    ]

if "factures" not in st.session_state:
    st.session_state.factures = _default_factures()
if "commandes" not in st.session_state:
    st.session_state.commandes = _default_commandes()

df_f = pd.DataFrame(st.session_state.factures)
df_cmd = pd.DataFrame(st.session_state.commandes)

# ── En-tête ─────────────────────────────────────────────────────────
st.markdown("""<div style="background:linear-gradient(135deg,#1a5276,#2e86c1);border-radius:16px;padding:28px 32px;color:#fff;margin-bottom:20px;">
<h1 style="margin:0;font-size:1.8rem;">🧾 Facturation & Commandes</h1>
<p style="margin:4px 0 0;opacity:0.85;">Gérez vos factures clients, acomptes, situations de travaux et commandes fournisseurs.</p>
</div>""", unsafe_allow_html=True)

# ── KPI Facturation ─────────────────────────────────────────────────
total_facture = df_f["montant_ht"].sum()
total_paye = df_f[df_f["statut"] == "Payée"]["montant_ht"].sum()
total_attente = df_f[df_f["statut"].isin(["Envoyée", "En retard"])]["montant_ht"].sum()
total_retard = df_f[df_f["statut"] == "En retard"]["montant_ht"].sum()
nb_retard = len(df_f[df_f["statut"] == "En retard"])

k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 Total facturé", f"{total_facture/1000:.0f}k€")
k2.metric("✅ Encaissé", f"{total_paye/1000:.0f}k€", delta=f"{int(total_paye/total_facture*100)}%" if total_facture > 0 else "")
k3.metric("⏳ En attente", f"{total_attente/1000:.0f}k€")
k4.metric("🚨 En retard", f"{total_retard/1000:.0f}k€", delta=f"{nb_retard} facture(s)" if nb_retard > 0 else "0")

st.markdown("---")

# ── Onglets Factures / Commandes / Créer ─────────────────────────────
tab_fact, tab_cmd, tab_new = st.tabs(["📄 Factures", "📦 Commandes fournisseurs", "➕ Nouvelle facture"])

with tab_fact:
    # Filtres
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filtre_chantier = st.selectbox("Chantier", ["Tous"] + sorted(df_f["chantier"].unique().tolist()), key="fact_chantier")
    with col_f2:
        filtre_type = st.selectbox("Type", ["Tous", "Situation", "Acompte", "Solde"], key="fact_type")
    with col_f3:
        filtre_statut = st.selectbox("Statut", ["Tous", "Brouillon", "Envoyée", "Payée", "En retard"], key="fact_statut")

    df_ff = df_f.copy()
    if filtre_chantier != "Tous":
        df_ff = df_ff[df_ff["chantier"] == filtre_chantier]
    if filtre_type != "Tous":
        df_ff = df_ff[df_ff["type"] == filtre_type]
    if filtre_statut != "Tous":
        df_ff = df_ff[df_ff["statut"] == filtre_statut]

    statut_colors = {"Payée": "#4CAF50", "Envoyée": "#2196F3", "En retard": "#e53935", "Brouillon": "#9E9E9E"}

    for _, row in df_ff.iterrows():
        s_color = statut_colors.get(row["statut"], "#666")
        st.markdown(f"""<div style="background:#fff;border-radius:12px;padding:14px 18px;margin-bottom:8px;
            border-left:4px solid {s_color};box-shadow:0 2px 6px rgba(0,0,0,0.06);">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <span style="font-weight:700;font-size:0.95rem;">{row['ref']}</span>
                    <span style="margin-left:8px;font-size:0.85rem;color:#666;">{row['type']}</span>
                </div>
                <span style="background:{s_color};color:#fff;padding:3px 12px;border-radius:20px;font-size:0.75rem;">{row['statut']}</span>
            </div>
            <div style="font-size:0.88rem;color:#444;margin:4px 0;">{row['objet']}</div>
            <div style="display:flex;justify-content:space-between;font-size:0.82rem;color:#888;">
                <span>🏗️ {row['chantier']} · {row['client']}</span>
                <span><b>{row['montant_ht']:,.0f} € HT</b> · TTC {row['montant_ttc']:,.0f} €</span>
            </div>
            <div style="font-size:0.78rem;color:#aaa;margin-top:4px;">
                Émise le {row['date_emission']} · Échéance {row['date_echeance']}
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown(f"<p style='font-size:0.85rem;color:#888;margin-top:8px;'>{len(df_ff)} facture(s) affichée(s) sur {len(df_f)}</p>", unsafe_allow_html=True)

with tab_cmd:
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        filtre_ch_cmd = st.selectbox("Chantier", ["Tous"] + sorted(df_cmd["chantier"].unique().tolist()), key="cmd_chantier")
    with col_c2:
        filtre_st_cmd = st.selectbox("Statut", ["Tous", "Commandée", "En cours", "Livrée"], key="cmd_statut")

    df_cmdf = df_cmd.copy()
    if filtre_ch_cmd != "Tous":
        df_cmdf = df_cmdf[df_cmdf["chantier"] == filtre_ch_cmd]
    if filtre_st_cmd != "Tous":
        df_cmdf = df_cmdf[df_cmdf["statut"] == filtre_st_cmd]

    cmd_colors = {"Livrée": "#4CAF50", "En cours": "#FF9800", "Commandée": "#2196F3"}

    for _, row in df_cmdf.iterrows():
        c_color = cmd_colors.get(row["statut"], "#666")
        st.markdown(f"""<div style="background:#fff;border-radius:12px;padding:14px 18px;margin-bottom:8px;
            border-left:4px solid {c_color};box-shadow:0 2px 6px rgba(0,0,0,0.06);">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <span style="font-weight:700;font-size:0.95rem;">{row['ref']}</span>
                    <span style="margin-left:8px;font-size:0.85rem;color:#666;">{row['fournisseur']}</span>
                </div>
                <span style="background:{c_color};color:#fff;padding:3px 12px;border-radius:20px;font-size:0.75rem;">{row['statut']}</span>
            </div>
            <div style="font-size:0.88rem;color:#444;margin:4px 0;">{row['objet']}</div>
            <div style="display:flex;justify-content:space-between;font-size:0.82rem;color:#888;">
                <span>🏗️ {row['chantier']}</span>
                <span><b>{row['montant_ht']:,.0f} € HT</b></span>
            </div>
            <div style="font-size:0.78rem;color:#aaa;margin-top:4px;">
                Commandée le {row['date_commande']} · Livraison prévue {row['date_livraison']}
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown(f"<p style='font-size:0.85rem;color:#888;margin-top:8px;'>{len(df_cmdf)} commande(s) affichée(s) sur {len(df_cmd)}</p>", unsafe_allow_html=True)

# ── TAB 3: Formulaire Nouvelle Facture ──────────────────────────────
with tab_new:
    st.markdown("### ➕ Créer une nouvelle facture")
    st.caption("Remplissez les informations ci-dessous pour générer une nouvelle facture.")

    with st.form("form_new_facture", clear_on_submit=True):
        fc1, fc2 = st.columns(2)
        with fc1:
            new_chantier = st.text_input("Chantier *", placeholder="Ex : Résidence Les Pins")
            new_client = st.text_input("Client *", placeholder="Ex : SCI Les Pins")
            new_type = st.selectbox("Type de facture *", ["Situation", "Acompte", "Solde", "Avoir"])
            new_objet = st.text_input("Objet *", placeholder="Ex : Situation n°3 — Plomberie")
        with fc2:
            new_montant = st.number_input("Montant HT (€) *", min_value=0.0, step=100.0, format="%.2f")
            new_tva_rate = st.selectbox("Taux TVA", ["20%", "10%", "5.5%", "0%"])
            new_date_em = st.date_input("Date d'émission", value=datetime.now())
            new_echeance = st.number_input("Délai de paiement (jours)", value=30, min_value=0, step=1)

        submitted = st.form_submit_button("🧾 Créer la facture", use_container_width=True, type="primary")

        if submitted:
            if not new_chantier or not new_client or not new_objet or new_montant <= 0:
                st.error("Veuillez remplir tous les champs obligatoires (*) et saisir un montant supérieur à 0.")
            else:
                tva_rate = float(new_tva_rate.replace("%", "")) / 100
                tva_amount = round(new_montant * tva_rate, 2)
                ttc = round(new_montant + tva_amount, 2)
                date_ech = new_date_em + timedelta(days=new_echeance)

                # Générer la référence
                existing_refs = [f["ref"] for f in st.session_state.factures]
                num = len(existing_refs) + 1
                new_ref = f"FACT-{new_date_em.year}-{num:03d}"

                new_facture = {
                    "ref": new_ref,
                    "chantier": new_chantier,
                    "type": new_type,
                    "objet": new_objet,
                    "montant_ht": new_montant,
                    "tva": tva_amount,
                    "montant_ttc": ttc,
                    "date_emission": new_date_em.strftime("%Y-%m-%d"),
                    "date_echeance": date_ech.strftime("%Y-%m-%d"),
                    "statut": "Brouillon",
                    "client": new_client,
                }

                st.session_state.factures.append(new_facture)
                st.success(f"Facture **{new_ref}** créée avec succès ! Montant : {new_montant:,.0f} € HT ({ttc:,.0f} € TTC)")
                st.balloons()

    # Aperçu des dernières factures créées
    st.divider()
    st.markdown("#### 📋 Dernières factures")
    recent = pd.DataFrame(st.session_state.factures[-5:])
    if len(recent) > 0:
        display = recent[["ref", "chantier", "type", "objet", "montant_ht", "statut"]].rename(columns={
            "ref": "Réf.", "chantier": "Chantier", "type": "Type",
            "objet": "Objet", "montant_ht": "Montant HT", "statut": "Statut"
        })
        st.dataframe(display, use_container_width=True, hide_index=True)
