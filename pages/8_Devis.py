import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import json
import io
from datetime import datetime, date
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib import db, storage
from utils import GLOBAL_CSS

user_id = page_setup(title="Devis", icon="\U0001f4b0")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.markdown("## \U0001f4b0 Devis professionnel assiste par IA")
st.caption("Generez des devis detailles a partir de vos metres, etudes et descriptions de travaux. Export PDF personnalisable.")

chantier = chantier_selector(key="devis_chantier")
if not chantier:
    st.stop()

profile = db.get_profile(user_id) or {}

# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# Auto-action depuis le Tableau de bord
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
auto_query = st.session_state.pop("auto_query", None)
if auto_query:
    st.session_state["devis_desc_travaux"] = auto_query

# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# Personnalisation visuelle du devis
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def _generate_devis_pdf(devis, numero, nom_soc, siret_soc, adresse_soc, tel_soc, email_soc,
                         client_nom, client_adresse, tva_rate, validite_jours,
                         logo_bytes=None, cgv_text=None):
    """Genere un PDF professionnel pour le devis avec logo et CGV."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=15*mm, rightMargin=15*mm)
    styles = getSampleStyleSheet()
    elements = []
    
    title_style = ParagraphStyle('DevisTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1a5276'))
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#555555'))
    cgv_style = ParagraphStyle('CGV', parent=styles['Normal'], fontSize=7, textColor=colors.HexColor('#666666'), leading=9)
    
    # Logo
    if logo_bytes:
        try:
            logo_io = io.BytesIO(logo_bytes)
            logo_img = Image(logo_io, width=50*mm, height=20*mm)
            logo_img.hAlign = 'LEFT'
            elements.append(logo_img)
            elements.append(Spacer(1, 3*mm))
        except Exception:
            pass
    
    # En-tete societe
    if nom_soc:
        elements.append(Paragraph(f"<b>{nom_soc}</b>", styles['Heading2']))
        details = []
        if siret_soc:
            details.append(f"SIRET: {siret_soc}")
        if adresse_soc:
            details.append(adresse_soc)
        if tel_soc:
            details.append(f"Tel: {tel_soc}")
        if email_soc:
            details.append(email_soc)
        if details:
            elements.append(Paragraph(" | ".join(details), header_style))
    elements.append(Spacer(1, 5*mm))
    
    # Titre devis
    elements.append(Paragraph(f"<b>DEVIS N\u00b0 {numero}</b>", ParagraphStyle('Num', parent=styles['Heading2'], fontSize=14)))
    elements.append(Paragraph(f"Date: {date.today().strftime('%d/%m/%Y')} | Validite: {validite_jours} jours", header_style))
    elements.append(Spacer(1, 5*mm))
    
    # Client
    if client_nom:
        elements.append(Paragraph(f"<b>Client:</b> {client_nom}", styles['Normal']))
        if client_adresse:
            elements.append(Paragraph(client_adresse, header_style))
    elements.append(Spacer(1, 8*mm))
    
    # Tableau devis
    for lot in devis.get("lots", []):
        elements.append(Paragraph(f"<b>{lot['nom']}</b>", styles['Heading3']))
        table_data = [["Designation", "Unite", "Qte", "PU HT", "Total HT"]]
        for p in lot.get("postes", []):
            table_data.append([
                p["designation"], p.get("unite", "u"),
                f"{p['quantite']:.2f}", f"{p['prix_unitaire']:.2f} \u20ac",
                f"{p['total_ht']:.2f} \u20ac"
            ])
        table_data.append(["", "", "", "Sous-total:", f"{lot.get('sous_total_ht', 0):.2f} \u20ac"])
        
        t = Table(table_data, colWidths=[80*mm, 20*mm, 20*mm, 25*mm, 30*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 5*mm))
    
    # Totaux
    total_ht = devis.get("total_ht", 0)
    tva_montant = devis.get("tva_montant", total_ht * tva_rate / 100)
    total_ttc = devis.get("total_ttc", total_ht + tva_montant)
    
    totaux = [
        ["Total HT:", f"{total_ht:,.2f} \u20ac"],
        [f"TVA ({tva_rate}%):", f"{tva_montant:,.2f} \u20ac"],
        ["Total TTC:", f"{total_ttc:,.2f} \u20ac"],
    ]
    t_totaux = Table(totaux, colWidths=[130*mm, 45*mm])
    t_totaux.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#1a5276')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#eaf2f8')),
    ]))
    elements.append(t_totaux)
    
    # Conditions Generales de Vente (CGV)
    if cgv_text:
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph("<b>Conditions Generales de Vente</b>", styles['Heading4']))
        for line in cgv_text.split("\n"):
            if line.strip():
                elements.append(Paragraph(line.strip(), cgv_style))
    
    doc.build(elements)
    return buffer.getvalue()


with st.expander("\u2699\ufe0f Personnalisation du devis", expanded=False):
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("**En-tete societe**")
        nom_societe = st.text_input("Nom de la societe", value=profile.get("company_name", ""), key="devis_company")
        siret = st.text_input("SIRET", value=profile.get("siret", ""), key="devis_siret")
        adresse_societe = st.text_input("Adresse", value=profile.get("address", ""), key="devis_address")
        tel_societe = st.text_input("Telephone", value=profile.get("phone", ""), key="devis_phone")
        email_societe = st.text_input("Email", value=profile.get("email", ""), key="devis_email")
        logo_file = st.file_uploader("Logo de l'entreprise", type=["png", "jpg", "jpeg"], key="devis_logo", help="Votre logo apparaitra en haut du PDF")
        logo_bytes = logo_file.read() if logo_file else None
    with col_p2:
        st.markdown("**Informations client**")
        client_nom = st.text_input("Nom du client", value=chantier.get("client_nom", ""), key="devis_client_nom")
        client_adresse = st.text_input("Adresse du client", key="devis_client_adresse")
        tva_rate = st.number_input("Taux de TVA (%)", value=20.0, min_value=0.0, max_value=30.0, step=0.5, key="devis_tva")
        devise = st.selectbox("Devise", ["EUR (\u20ac)", "USD ($)"], key="devis_devise")
        date_validite = st.number_input("Validite (jours)", value=30, min_value=7, max_value=180, key="devis_validite")
        cgv_text = st.text_area("Conditions Generales de Vente", value="", height=120, key="devis_cgv", help="Ces conditions apparaitront en bas du PDF du devis", placeholder="Ex: Paiement a 30 jours. Acompte de 30% a la commande...")

st.markdown("---")

# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# Donnees existantes du chantier (metres, etudes)
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
metres = db.get_metres(chantier["id"])
etudes = db.get_etudes(chantier_id=chantier["id"])

col_info1, col_info2 = st.columns(2)
with col_info1:
    st.info(f"\U0001f4d0 {len(metres)} metre(s) disponible(s) pour ce chantier")
with col_info2:
    st.info(f"\U0001f4d1 {len(etudes)} etude(s) disponible(s) pour ce chantier")

# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# Generation du devis par IA
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
st.subheader("\U0001f916 Generer un devis")

desc_travaux = st.text_area(
    "Description des travaux",
    value=st.session_state.get("devis_desc_travaux", ""),
    placeholder="Decrivez les travaux : lot plomberie, gros oeuvre, facade...",
    height=120,
    key="devis_desc_input"
)

col_opt1, col_opt2 = st.columns(2)
with col_opt1:
    utiliser_metres = st.checkbox("Utiliser les metres du chantier", value=bool(metres), key="devis_use_metres")
with col_opt2:
    utiliser_etudes = st.checkbox("Utiliser les etudes du chantier", value=bool(etudes), key="devis_use_etudes")

if st.button("\U0001f916 Generer le devis IA", type="primary", disabled=not desc_travaux, width="stretch"):
    with st.spinner("Generation du devis en cours..."):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

            # Construire le contexte
            metres_ctx = ""
            if utiliser_metres and metres:
                metres_ctx = "\n\nMetres disponibles:\n" + json.dumps(metres[:10], indent=2, default=str)
            
            etudes_ctx = ""
            if utiliser_etudes and etudes:
                etudes_summary = [{"type": e.get("etude_type"), "titre": e.get("titre"), "contenu": str(e.get("contenu", ""))[:300]} for e in etudes[:5]]
                etudes_ctx = "\n\nEtudes disponibles:\n" + json.dumps(etudes_summary, indent=2, default=str)

            prompt = f"""Genere un devis detaille professionnel pour ces travaux BTP.
Chantier: {chantier.get('nom', '')} - {chantier.get('adresse', '')}
Description des travaux: {desc_travaux}
{metres_ctx}
{etudes_ctx}

Reponds UNIQUEMENT en JSON avec cette structure exacte:
{{
  "titre": "Titre du devis",
  "lots": [
    {{
      "nom": "Nom du lot",
      "postes": [
        {{"designation": "Description", "unite": "m2/ml/u/forfait", "quantite": 10.0, "prix_unitaire": 50.0, "total_ht": 500.0}}
      ],
      "sous_total_ht": 500.0
    }}
  ],
  "total_ht": 1000.0,
  "tva_taux": {tva_rate},
  "tva_montant": 200.0,
  "total_ttc": 1200.0,
  "conditions": "Conditions de paiement et validite"
}}"""

            response = client.messages.create(
                model="claude-sonnet-4-20250514", max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.content[0].text
            # Extraire le JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                devis_data = json.loads(json_match.group())
                st.session_state["devis_generated"] = devis_data
                st.success("Devis genere avec succes !")
                st.rerun()
            else:
                st.error("Format de reponse invalide")
                st.code(result_text)
        except Exception as e:
            st.error(f"Erreur: {e}")

# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# Affichage et personnalisation du devis genere
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
if "devis_generated" in st.session_state:
    devis_data = st.session_state["devis_generated"]
    
    st.markdown("---")
    st.subheader("\U0001f4cb " + devis_data.get("titre", "Devis"))
    
    # Tableau editable des lots
    total_ht_global = 0
    edited_lots = []
    
    for lot_idx, lot in enumerate(devis_data.get("lots", [])):
        with st.expander(f"\U0001f4e6 {lot['nom']} â {lot.get('sous_total_ht', 0):,.2f} \u20ac HT", expanded=True):
            postes_edites = []
            for p_idx, poste in enumerate(lot.get("postes", [])):
                cols = st.columns([4, 1, 1, 1, 1])
                with cols[0]:
                    designation = st.text_input("Designation", value=poste["designation"], key=f"des_{lot_idx}_{p_idx}", label_visibility="collapsed")
                with cols[1]:
                    unite = st.text_input("Unite", value=poste.get("unite", "u"), key=f"uni_{lot_idx}_{p_idx}", label_visibility="collapsed")
                with cols[2]:
                    qte = st.number_input("Qte", value=float(poste.get("quantite", 0)), key=f"qte_{lot_idx}_{p_idx}", label_visibility="collapsed", step=0.1)
                with cols[3]:
                    pu = st.number_input("PU HT", value=float(poste.get("prix_unitaire", 0)), key=f"pu_{lot_idx}_{p_idx}", label_visibility="collapsed", step=0.01)
                with cols[4]:
                    total_p = qte * pu
                    st.metric("Total", f"{total_p:,.2f} \u20ac", label_visibility="collapsed")
                
                postes_edites.append({
                    "designation": designation, "unite": unite,
                    "quantite": qte, "prix_unitaire": pu, "total_ht": total_p
                })
            
            sous_total = sum(p["total_ht"] for p in postes_edites)
            total_ht_global += sous_total
            edited_lots.append({"nom": lot["nom"], "postes": postes_edites, "sous_total_ht": sous_total})
    
    # Recalcul totaux
    tva_montant = total_ht_global * (tva_rate / 100)
    total_ttc = total_ht_global + tva_montant
    
    st.markdown("---")
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.metric("Total HT", f"{total_ht_global:,.2f} \u20ac")
    with col_t2:
        st.metric(f"TVA ({tva_rate}%)", f"{tva_montant:,.2f} \u20ac")
    with col_t3:
        st.metric("Total TTC", f"{total_ttc:,.2f} \u20ac")
    
    st.markdown("---")
    
    # âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    # Export PDF + Sauvegarde
    # âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("\U0001f4be Enregistrer le devis", type="primary", width="stretch"):
          try:
            # Sauvegarder en base
            devis_final = {
                "titre": devis_data.get("titre", "Devis"),
                "lots": edited_lots,
                "total_ht": total_ht_global,
                "tva_taux": tva_rate,
                "tva_montant": tva_montant,
                "total_ttc": total_ttc,
                "client_nom": client_nom,
                "description": desc_travaux,
            }
            existing = db.get_devis(user_id=user_id)
            numero = f"DEV-{datetime.now().strftime('%Y%m')}-{len(existing)+1:03d}"
            
            result = db.save_devis(user_id, chantier["id"], {
                "numero": numero,
                "objet": devis_data.get("titre", "Devis"),
                "client_nom": client_nom,
                "montant_ht": total_ht_global,
                "montant_ttc": total_ttc,
                "statut": "brouillon",
            })
            if result:
                st.success(f"Devis {numero} enregistre !")
                
                # Auto-stockage PDF
                try:
                    pdf_bytes = _generate_devis_pdf(
                        devis_final, numero,
                        nom_societe, siret, adresse_societe, tel_societe, email_societe,
                        client_nom, client_adresse, tva_rate, date_validite,
                        logo_bytes=logo_bytes, cgv_text=cgv_text
                    )
                    storage.upload_generated_document(
                        file_bytes=pdf_bytes,
                        filename=f"{numero}.pdf",
                        chantier_id=chantier["id"],
                        famille="Devis",
                        doc_type="Devis PDF",
                    )
                    db.create_document({
                        "nom": f"{numero}.pdf",
                        "type": "Devis",
                        "famille": "Devis",
                        "statut": "Genere",
                        "chantier_id": chantier["id"],
                        "metadata": json.dumps({"montant_ht": total_ht_global, "montant_ttc": total_ttc}),
                    })
                    st.info("\U0001f4c4 PDF auto-stocke dans les Documents du chantier")
                except Exception as e:
                    st.warning(f"Devis enregistre mais erreur PDF: {e}")
            else:
                st.error("Erreur lors de l'enregistrement. Verifiez les donnees.")
          except Exception as save_err:
                st.error(f"Erreur: {save_err}")
    
    with col_btn2:
        # Telecharger PDF
        try:
            pdf_bytes = _generate_devis_pdf(
                {"titre": devis_data.get("titre"), "lots": edited_lots,
                 "total_ht": total_ht_global, "tva_taux": tva_rate,
                 "tva_montant": tva_montant, "total_ttc": total_ttc},
                "APERCU",
                nom_societe, siret, adresse_societe, tel_societe, email_societe,
                client_nom, client_adresse, tva_rate, date_validite,
                logo_bytes=logo_bytes, cgv_text=cgv_text
            )
            st.download_button(
                "\U0001f4e5 Telecharger PDF",
                data=pdf_bytes,
                file_name=f"devis_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                type="secondary",
                width="stretch"
            )
        except Exception as e:
            st.warning(f"Erreur generation PDF: {e}")

st.markdown("---")

# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# Historique des devis
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
st.subheader("\U0001f4cb Historique des devis")
devis_list = db.get_devis(chantier_id=chantier["id"])
if devis_list:
    import pandas as pd
    df = pd.DataFrame(devis_list)
    cols_show = [c for c in ["numero", "objet", "client_nom", "montant_ht", "montant_ttc", "statut", "created_at"] if c in df.columns]
    if cols_show:
        df_show = df[cols_show].copy()
        if "montant_ht" in df_show.columns:
            df_show["montant_ht"] = df_show["montant_ht"].apply(lambda x: f"{float(x or 0):,.2f} \u20ac")
        if "montant_ttc" in df_show.columns:
            df_show["montant_ttc"] = df_show["montant_ttc"].apply(lambda x: f"{float(x or 0):,.2f} \u20ac")
        st.dataframe(df_show, width="stretch", hide_index=True)
else:
    st.info("Aucun devis pour ce chantier.")


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# Fonction generation PDF
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
