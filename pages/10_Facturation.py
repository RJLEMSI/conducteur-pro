import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib import db
from utils import GLOBAL_CSS

user_id = page_setup(title="Facturation", icon="🧾")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.title("🧾 Facturation")

chantier = chantier_selector(key="facture_chantier")
if not chantier:
    st.stop()

# ─── Nouvelle facture ─────────────────────────────────────────────────────────
st.subheader("🆕 Créer une facture")
with st.form("new_facture"):
    col1, col2 = st.columns(2)
    numero = col1.text_input("N° Facture *", value=f"F-{datetime.now().strftime('%Y%m%d')}-001")
    date_emission = col2.date_input("Date d'émission", datetime.now())
    
    col3, col4 = st.columns(2)
    montant_ht = col3.number_input("Montant HT (€)", min_value=0.0, step=100.0)
    tva = col4.selectbox("TVA (%)", [20.0, 10.0, 5.5, 0.0])
    montant_ttc = montant_ht * (1 + tva / 100)
    st.info(f"Montant TTC: **{montant_ttc:,.2f} €**")
    
    col5, col6 = st.columns(2)
    statut = col5.selectbox("Statut", ["En attente", "Envoyée", "Payée", "En retard", "Annulée"])
    date_echeance = col6.date_input("Date d'échéance", datetime.now() + timedelta(days=30))
    
    description = st.text_area("Détails")
    
    if st.form_submit_button("Créer la facture") and numero:
        result = db.save_facture(user_id, chantier["id"], {
            "numero": numero, "montant_ht": montant_ht,
            "tva": tva, "montant_ttc": montant_ttc,
            "statut": statut.lower().replace(" ", "_").replace("é", "e"),
            "date_emission": date_emission.isoformat(),
            "date_echeance": date_echeance.isoformat(),
            "description": description
        })
        if result:
            st.success(f"Facture {numero} créée.")
            st.rerun()

# ─── Factures existantes ──────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Factures du chantier")
factures = db.get_factures(chantier_id=chantier["id"])
if factures:
    df = pd.DataFrame(factures)
    
    # KPIs
    total = sum(float(f.get("montant_ttc", 0) or 0) for f in factures)
    payees = sum(float(f.get("montant_ttc", 0) or 0) for f in factures if f.get("statut") == "payée")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total facturé", f"{total:,.2f} €")
    col2.metric("Total payé", f"{payees:,.2f} €")
    col3.metric("Reste à payer", f"{total - payees:,.2f} €")
    
    # Table
    cols_display = [c for c in ["numero", "montant_ttc", "statut", "date_emission", "date_echeance"] if c in df.columns]
    st.dataframe(df[cols_display] if cols_display else df, use_container_width=True)
    
    # Mise à jour statut
    st.subheader("🔄 Mettre à jour un statut")
    facture_options = {f"{f.get('numero', 'N/A')} - {f.get('montant_ttc', 0):,.2f}€": f for f in factures}
    selected = st.selectbox("Facture", list(facture_options.keys()))
    new_status = st.selectbox("Nouveau statut", ["en_attente", "envoyee", "payée", "en_retard", "annulee"])
    if st.button("Mettre à jour"):
        fac = facture_options[selected]
        db.update_facture(fac["id"], {"statut": new_status})
        st.success("Statut mis à jour.")
        st.rerun()
else:
    st.info("Aucune facture pour ce chantier.")
