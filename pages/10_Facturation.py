"""
Page 10 — Facturation
Création de factures avec génération automatique de PDF professionnels.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib import db
from lib.invoice_pdf import generate_invoice_pdf
from utils import GLOBAL_CSS

page_setup(title="Facturation", icon="🧾")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
user_id = st.session_state.get("user_id")
render_saas_sidebar(user_id)

st.title("🧾 Facturation")

chantier = chantier_selector(key="facture_chantier")
if not chantier:
    st.stop()

# ─── Infos entreprise (pour PDF) ────────────────────────────────────────────────
profile = db.get_profile(user_id) or {}
company_info = {
    "company_name": profile.get("company_name", ""),
    "siret": profile.get("siret", ""),
    "address": profile.get("address", ""),
    "phone": profile.get("phone", ""),
    "email": profile.get("email", ""),
}
client_info = {
    "nom": chantier.get("client_nom", ""),
    "adresse": f"{chantier.get('adresse', '')} {chantier.get('code_postal', '')} {chantier.get('ville', '')}".strip(),
    "email": chantier.get("client_email", ""),
    "tel": chantier.get("client_tel", ""),
}
chantier_info_dict = {
    "nom": chantier.get("nom", ""),
    "adresse": f"{chantier.get('adresse', '')} {chantier.get('code_postal', '')} {chantier.get('ville', '')}".strip(),
}

# ─── Créer une facture ────────────────────────────────────────────────────
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
    date_echeance = col6.date_input("Échéance", datetime.now() + timedelta(days=30))

    objet = st.text_input("Objet de la facture", value=chantier.get("nom", ""))
    description = st.text_area("Détails / lignes supplémentaires")

    if st.form_submit_button("Créer la facture", type="primary") and numero:
        tva_montant = round(montant_ht * tva / 100, 2)
        facture_data = {
            "numero": numero,
            "montant_ht": montant_ht,
            "tva_pct": tva,
            "tva_montant": tva_montant,
            "montant_ttc": round(montant_ttc, 2),
            "client_nom": chantier.get("client_nom", ""),
            "objet": objet,
            "statut": statut.lower().replace(" ", "_").replace("é", "e"),
            "date_facture": date_emission.isoformat(),
            "date_echeance": date_echeance.isoformat(),
        }
        result = db.save_facture(user_id, chantier["id"], facture_data)
        if result:
            st.success(f"✅ Facture {numero} créée avec succès !")
            st.rerun()
        else:
            st.error("Erreur lors de la création de la facture.")

# ─── Factures existantes ─────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Factures du chantier")
factures = db.get_factures(chantier_id=chantier["id"])
if factures:
    # KPIs
    total = sum(float(f.get("montant_ttc", 0) or 0) for f in factures)
    payees = sum(float(f.get("montant_ttc", 0) or 0) for f in factures if f.get("statut") in ("payee", "payée"))
    col1, col2, col3 = st.columns(3)
    col1.metric("Total facturé", f"{total:,.2f} €")
    col2.metric("Total payé", f"{payees:,.2f} €")
    col3.metric("Reste à payer", f"{total - payees:,.2f} €")

    # Tableau des factures avec boutons PDF
    for i, fac in enumerate(factures):
        num = fac.get("numero", "N/A")
        client = fac.get("client_nom", "")
        obj = fac.get("objet", "")
        mt = float(fac.get("montant_ttc", 0) or 0)
        stat = fac.get("statut", "")
        date_f = str(fac.get("date_facture", ""))[:10]
        date_e = str(fac.get("date_echeance", ""))[:10]

        # Icône statut
        stat_icon = {"en_attente": "⏳", "envoyee": "📨", "payee": "✅", "en_retard": "⚠️", "annulee": "❌"}.get(stat, "📄")
        stat_display = {"en_attente": "En attente", "envoyee": "Envoyée", "payee": "Payée", "en_retard": "En retard", "annulee": "Annulée"}.get(stat, stat)

        with st.container():
            c1, c2, c3, c4, c5 = st.columns([2, 2, 1.5, 1.5, 1.5])
            c1.markdown(f"**{num}**")
            c1.caption(f"{client} — {obj}")
            c2.markdown(f"**{mt:,.2f} €** TTC")
            c2.caption(f"Du {date_f} — Éch. {date_e}")
            c3.markdown(f"{stat_icon} {stat_display}")

            # Bouton Générer PDF
            pdf_bytes = generate_invoice_pdf(
                facture=fac,
                company_info=company_info,
                client_info=client_info,
                chantier_info=chantier_info_dict,
            )
            c4.download_button(
                label="📄 PDF",
                data=pdf_bytes,
                file_name=f"Facture_{num}.pdf",
                mime="application/pdf",
                key=f"pdf_{i}",
            )

            # Bouton Mettre à jour statut
            with c5.popover("✏️ Statut"):
                new_stat = st.selectbox(
                    "Nouveau statut",
                    ["en_attente", "envoyee", "payee", "en_retard", "annulee"],
                    key=f"stat_{i}",
                    index=["en_attente", "envoyee", "payee", "en_retard", "annulee"].index(stat) if stat in ["en_attente", "envoyee", "payee", "en_retard", "annulee"] else 0,
                )
                if st.button("Mettre à jour", key=f"upd_{i}"):
                    db.update_facture(fac["id"], {"statut": new_stat})
                    st.success("Mis à jour !")
                    st.rerun()

            st.markdown("---")
else:
    st.info("Aucune facture pour ce chantier.")
