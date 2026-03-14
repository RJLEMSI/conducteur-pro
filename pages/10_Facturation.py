import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import json
import io
from datetime import datetime, date
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib import db, storage
from utils import GLOBAL_CSS

user_id = page_setup(title="Facturation", icon="\U0001f9fe")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.markdown("## \U0001f9fe Facturation")
st.caption("Creez des factures professionnelles en PDF personnalisable avec en-tete de votre societe.")

chantier = chantier_selector(key="facture_chantier")
if not chantier:
    st.stop()

profile = db.get_profile(user_id) or {}

# Auto-action
auto_query = st.session_state.pop("auto_query", None)

# ═══════════════════════════════════════════════════════════════════════════════
# Personnalisation en-tete societe
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("\u2699\ufe0f En-tete de votre societe", expanded=False):
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        nom_societe = st.text_input("Nom societe", value=profile.get("company_name", ""), key="fac_company")
        siret = st.text_input("SIRET", value=profile.get("siret", ""), key="fac_siret")
        adresse_societe = st.text_input("Adresse", value=profile.get("address", ""), key="fac_address")
    with col_h2:
        tel_societe = st.text_input("Telephone", value=profile.get("phone", ""), key="fac_phone")
        email_societe = st.text_input("Email", value=profile.get("email", ""), key="fac_email")
        tva_intra = st.text_input("N\u00b0 TVA intracommunautaire", key="fac_tva_intra")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# Nouvelle facture
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("\U0001f4dd Creer une facture")

# Charger les devis existants pour facturation rapide
devis_existants = db.get_devis(chantier_id=chantier["id"])
devis_non_factures = [d for d in devis_existants if d.get("statut") != "facture"]

source_facture = st.radio(
    "Source de la facture",
    ["\U0001f4cb A partir d'un devis existant", "\U0001f4dd Saisie manuelle"],
    horizontal=True, key="fac_source"
)

facture_lignes = []
client_nom = chantier.get("client_nom", "")
objet_facture = ""
montant_ht = 0.0

if "devis existant" in source_facture:
    if devis_non_factures:
        devis_options = {f"{d.get('numero', '?')} - {d.get('objet', 'Sans objet')} ({float(d.get('montant_ht', 0)):,.2f} \u20ac HT)": d for d in devis_non_factures}
        selected_devis_label = st.selectbox("Selectionner le devis", list(devis_options.keys()), key="fac_devis_select")
        selected_devis = devis_options[selected_devis_label]
        
        client_nom = selected_devis.get("client_nom", client_nom)
        objet_facture = selected_devis.get("objet", "")
        montant_ht = float(selected_devis.get("montant_ht", 0))
        
        # Charger les lots du devis si disponible
        contenu = selected_devis.get("contenu")
        if contenu:
            try:
                devis_content = json.loads(contenu) if isinstance(contenu, str) else contenu
                facture_lignes = []
                for lot in devis_content.get("lots", []):
                    for p in lot.get("postes", []):
                        facture_lignes.append(p)
            except Exception:
                pass
        
        st.info(f"\U0001f4b0 Devis {selected_devis.get('numero')} - Montant HT: {montant_ht:,.2f} \u20ac")
    else:
        st.warning("Aucun devis non facture pour ce chantier. Creez d'abord un devis.")
else:
    objet_facture = st.text_input("Objet de la facture", key="fac_objet")
    client_nom = st.text_input("Client", value=client_nom, key="fac_client")
    
    nb_lignes = st.number_input("Nombre de lignes", min_value=1, max_value=50, value=3, key="fac_nb_lignes")
    for i in range(int(nb_lignes)):
        cols = st.columns([4, 1, 1, 1])
        with cols[0]:
            des = st.text_input(f"Ligne {i+1}", key=f"fac_des_{i}", label_visibility="collapsed", placeholder="Designation")
        with cols[1]:
            qte = st.number_input("Qte", value=1.0, key=f"fac_qte_{i}", label_visibility="collapsed")
        with cols[2]:
            pu = st.number_input("PU HT", value=0.0, key=f"fac_pu_{i}", label_visibility="collapsed")
        with cols[3]:
            total = qte * pu
            st.text_input("Total", value=f"{total:.2f}", key=f"fac_tot_{i}", disabled=True, label_visibility="collapsed")
        if des:
            facture_lignes.append({"designation": des, "quantite": qte, "prix_unitaire": pu, "total_ht": total})
    
    montant_ht = sum(l["total_ht"] for l in facture_lignes)

# TVA et totaux
tva_rate = st.number_input("Taux TVA (%)", value=20.0, min_value=0.0, max_value=30.0, step=0.5, key="fac_tva_rate")
tva_montant = montant_ht * (tva_rate / 100)
total_ttc = montant_ht + tva_montant

col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric("Total HT", f"{montant_ht:,.2f} \u20ac")
with col_m2:
    st.metric(f"TVA ({tva_rate}%)", f"{tva_montant:,.2f} \u20ac")
with col_m3:
    st.metric("Total TTC", f"{total_ttc:,.2f} \u20ac")

conditions = st.text_area("Conditions de paiement", value="Paiement a 30 jours date de facture. Penalites de retard: 3x taux legal.", key="fac_conditions")

st.markdown("---")

col_save, col_dl = st.columns(2)

with col_save:
    if st.button("\U0001f4be Enregistrer et stocker PDF", type="primary", width="stretch"):
        if objet_facture or montant_ht > 0:
            # Generer numero
            existing_fac = db.get_factures(chantier_id=chantier["id"])
            numero = f"FAC-{datetime.now().strftime('%Y%m')}-{len(existing_fac)+1:03d}"
            
            facture_data = {
                "numero": numero,
                "objet": objet_facture,
                "client_nom": client_nom,
                "montant_ht": montant_ht,
                "montant_ttc": total_ttc,
                "tva_taux": tva_rate,
                "statut": "emise",
                "conditions": conditions,
                "lignes": json.dumps(facture_lignes, default=str),
            }
            
            result = db.save_facture(user_id, chantier["id"], facture_data)
            if result:
                # Marquer le devis comme facture si applicable
                if "devis existant" in source_facture and devis_non_factures:
                    try:
                        db.update_devis(selected_devis["id"], {"statut": "facture"})
                    except Exception:
                        pass
                
                st.success(f"Facture {numero} enregistree !")
                
                # Auto-stockage PDF
                try:
                    pdf_bytes = _generate_facture_pdf(
                        facture_data, facture_lignes,
                        nom_societe, siret, adresse_societe, tel_societe, email_societe, tva_intra,
                        client_nom, tva_rate, conditions
                    )
                    storage.upload_generated_document(
                        file_bytes=pdf_bytes,
                        filename=f"{numero}.pdf",
                        chantier_id=chantier["id"],
                        famille="Factures",
                        doc_type="Facture PDF",
                    )
                    db.create_document({
                        "nom": f"{numero}.pdf",
                        "type": "Facture",
                        "famille": "Factures",
                        "statut": "Generee",
                        "chantier_id": chantier["id"],
                    })
                    st.info("\U0001f4c4 PDF auto-stocke dans les Documents")
                except Exception as e:
                    st.warning(f"Facture enregistree mais erreur PDF: {e}")
                
                st.rerun()
            else:
                st.error("Erreur lors de l'enregistrement")
        else:
            st.warning("Remplissez au moins l'objet ou ajoutez des lignes")

with col_dl:
    if montant_ht > 0:
        try:
            pdf_bytes = _generate_facture_pdf(
                {"numero": "APERCU", "objet": objet_facture, "client_nom": client_nom,
                 "montant_ht": montant_ht, "montant_ttc": total_ttc},
                facture_lignes,
                nom_societe, siret, adresse_societe, tel_societe, email_societe, tva_intra,
                client_nom, tva_rate, conditions
            )
            st.download_button(
                "\U0001f4e5 Telecharger PDF",
                data=pdf_bytes,
                file_name=f"facture_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                type="secondary",
                width="stretch"
            )
        except Exception:
            pass

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# Historique factures
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("\U0001f4cb Historique des factures")
factures = db.get_factures(chantier_id=chantier["id"])
if factures:
    import pandas as pd
    for fac in factures:
        col_f1, col_f2, col_f3, col_f4 = st.columns([3, 2, 2, 1])
        with col_f1:
            st.markdown(f"**{fac.get('numero', '?')}** — {fac.get('objet', 'Sans objet')}")
        with col_f2:
            st.markdown(f"{float(fac.get('montant_ttc', 0)):,.2f} \u20ac TTC")
        with col_f3:
            statut = fac.get("statut", "emise")
            color = {"payee": "\U0001f7e2", "emise": "\U0001f7e1", "en_retard": "\U0001f534"}.get(statut, "\u26aa")
            new_statut = st.selectbox(f"Statut", ["emise", "payee", "en_retard", "annulee"],
                                      index=["emise", "payee", "en_retard", "annulee"].index(statut) if statut in ["emise", "payee", "en_retard", "annulee"] else 0,
                                      key=f"fac_stat_{fac['id']}", label_visibility="collapsed")
            if new_statut != statut:
                db.update_facture(fac["id"], {"statut": new_statut})
                st.rerun()
        with col_f4:
            st.markdown(f"{color} {statut}")
else:
    st.info("Aucune facture pour ce chantier.")


# ═══════════════════════════════════════════════════════════════════════════════
# Fonction generation PDF facture
# ═══════════════════════════════════════════════════════════════════════════════
def _generate_facture_pdf(facture_data, lignes, nom_soc, siret_soc, adresse_soc, tel_soc, email_soc, tva_intra,
                           client_nom, tva_rate, conditions):
    """Genere un PDF professionnel pour la facture."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=15*mm, rightMargin=15*mm)
    styles = getSampleStyleSheet()
    elements = []
    
    title_style = ParagraphStyle('FacTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#2c3e50'))
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#555555'))
    
    # En-tete societe
    if nom_soc:
        elements.append(Paragraph(f"<b>{nom_soc}</b>", title_style))
        parts = []
        if siret_soc: parts.append(f"SIRET: {siret_soc}")
        if tva_intra: parts.append(f"TVA: {tva_intra}")
        if parts:
            elements.append(Paragraph(" | ".join(parts), header_style))
        if adresse_soc:
            elements.append(Paragraph(adresse_soc, header_style))
        info_parts = []
        if tel_soc: info_parts.append(f"Tel: {tel_soc}")
        if email_soc: info_parts.append(f"Email: {email_soc}")
        if info_parts:
            elements.append(Paragraph(" | ".join(info_parts), header_style))
        elements.append(Spacer(1, 10*mm))
    
    # Titre facture
    numero = facture_data.get("numero", "")
    elements.append(Paragraph(f"<b>FACTURE N\u00b0 {numero}</b>", ParagraphStyle('Num', parent=styles['Heading2'], fontSize=14)))
    elements.append(Paragraph(f"Date: {date.today().strftime('%d/%m/%Y')}", header_style))
    elements.append(Spacer(1, 5*mm))
    
    # Client
    if client_nom:
        elements.append(Paragraph(f"<b>Client:</b> {client_nom}", styles['Normal']))
    if facture_data.get("objet"):
        elements.append(Paragraph(f"<b>Objet:</b> {facture_data['objet']}", styles['Normal']))
    elements.append(Spacer(1, 8*mm))
    
    # Tableau lignes
    if lignes:
        table_data = [["Designation", "Qte", "PU HT", "Total HT"]]
        for l in lignes:
            table_data.append([
                l.get("designation", ""),
                f"{l.get('quantite', 0):.2f}",
                f"{l.get('prix_unitaire', 0):.2f} \u20ac",
                f"{l.get('total_ht', 0):.2f} \u20ac"
            ])
        t = Table(table_data, colWidths=[250, 50, 80, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(t)
    
    # Totaux
    elements.append(Spacer(1, 8*mm))
    montant_ht = float(facture_data.get("montant_ht", 0))
    tva_montant = montant_ht * (tva_rate / 100)
    montant_ttc = float(facture_data.get("montant_ttc", montant_ht + tva_montant))
    
    totaux_data = [
        ["Total HT", f"{montant_ht:.2f} \u20ac"],
        [f"TVA ({tva_rate}%)", f"{tva_montant:.2f} \u20ac"],
        ["TOTAL TTC", f"{montant_ttc:.2f} \u20ac"],
    ]
    t_tot = Table(totaux_data, colWidths=[350, 80])
    t_tot.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor('#2c3e50')),
    ]))
    elements.append(t_tot)
    
    # Conditions
    if conditions:
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph(f"<b>Conditions:</b> {conditions}", ParagraphStyle('Cond', parent=styles['Normal'], fontSize=8, textColor=colors.grey)))
    
    doc.build(elements)
    return buffer.getvalue()
