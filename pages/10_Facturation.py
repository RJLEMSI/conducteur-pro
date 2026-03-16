import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import json
import io
from datetime import datetime, date
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib import db, storage
from utils import GLOBAL_CSS


# ===============================================================================
# Fonction generation PDF facture (DOIT etre definie AVANT son utilisation)
# ===============================================================================
def _generate_facture_pdf(facture_data, lignes, nom_soc, siret_soc, adresse_soc,
                          tel_soc, email_soc, tva_intra, client_nom, tva_rate, conditions,
                          logo_bytes=None, cgv_text=None):
    """Genere un PDF professionnel pour la facture avec logo et CGV."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm,
                            leftMargin=15*mm, rightMargin=15*mm)
    styles = getSampleStyleSheet()
    elements = []

    # Logo
    if logo_bytes:
        try:
            from reportlab.lib.utils import ImageReader
            logo_stream = io.BytesIO(logo_bytes)
            img = Image(logo_stream, width=50*mm, height=25*mm)
            img.hAlign = 'LEFT'
            elements.append(img)
            elements.append(Spacer(1, 5*mm))
        except Exception:
            pass

    # En-tete societe
    from reportlab.lib.styles import ParagraphStyle
    soc_style = ParagraphStyle('Soc', parent=styles['Normal'], fontSize=9, leading=12)
    soc_info = f"<b>{nom_soc}</b><br/>SIRET: {siret_soc}<br/>{adresse_soc}<br/>Tel: {tel_soc} | Email: {email_soc}"
    if tva_intra:
        soc_info += f"<br/>TVA: {tva_intra}"
    elements.append(Paragraph(soc_info, soc_style))
    elements.append(Spacer(1, 8*mm))

    # Titre facture
    titre = facture_data.get("objet", facture_data.get("titre", "Facture"))
    numero = facture_data.get("numero", "")
    date_fac = facture_data.get("date", datetime.now().strftime("%d/%m/%Y"))
    title_style = ParagraphStyle('Title2', parent=styles['Heading1'],
                                  fontSize=16, textColor=colors.HexColor('#2c3e50'))
    elements.append(Paragraph(f"FACTURE {numero}", title_style))
    elements.append(Paragraph(f"<b>Objet :</b> {titre}", soc_style))
    elements.append(Paragraph(f"<b>Date :</b> {date_fac}", soc_style))
    elements.append(Spacer(1, 5*mm))

    # Client
    elements.append(Paragraph(f"<b>Client :</b> {client_nom}", soc_style))
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

    # Conditions de paiement
    if conditions:
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph(f"<b>Conditions:</b> {conditions}",
                                  ParagraphStyle('Cond', parent=styles['Normal'],
                                                 fontSize=8, textColor=colors.grey)))

    # CGV en pied de page
    if cgv_text:
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph("<b>Conditions Generales de Vente :</b>",
                                  ParagraphStyle('CGVTitle', parent=styles['Normal'],
                                                 fontSize=7, textColor=colors.HexColor('#2c3e50'))))
        elements.append(Paragraph(cgv_text,
                                  ParagraphStyle('CGV', parent=styles['Normal'],
                                                 fontSize=6, leading=8, textColor=colors.grey)))

    doc.build(elements)
    return buffer.getvalue()


# ===============================================================================
# Page principale
# ===============================================================================
page_setup("Facturation", icon="\U0001f9fe")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar()

require_feature("facturation")

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Connectez-vous pour acceder a la facturation.")
    st.stop()

chantier = chantier_selector()
if not chantier:
    st.info("Selectionnez ou creez un chantier pour commencer.")
    st.stop()

profile = db.get_profile(user_id) or {}
client_nom = chantier.get("client_nom", "Client")
conditions = "Paiement a 30 jours"

# ===============================================================================
# Informations societe + Logo + CGV
# ===============================================================================
with st.expander("\U0001f3e2 Informations societe & Personnalisation", expanded=False):
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

    # Logo upload
    logo_file = st.file_uploader("\U0001f5bc Logo de l'entreprise (PNG, JPG)", type=["png", "jpg", "jpeg"], key="fac_logo_upload")
    logo_bytes = None
    if logo_file is not None:
        logo_bytes = logo_file.read()
        st.image(logo_bytes, width=150, caption="Apercu du logo")
    elif st.session_state.get("fac_logo_bytes"):
        logo_bytes = st.session_state["fac_logo_bytes"]

    if logo_bytes:
        st.session_state["fac_logo_bytes"] = logo_bytes

    # CGV
    cgv_text = st.text_area(
        "\U0001f4dc Conditions Generales de Vente (pied de page PDF)",
        value=st.session_state.get("fac_cgv_text", ""),
        key="fac_cgv_input",
        height=100,
        placeholder="Ex: Tout retard de paiement entrainera des penalites de retard..."
    )
    if cgv_text:
        st.session_state["fac_cgv_text"] = cgv_text

st.markdown("---")

# ===============================================================================
# Nouvelle facture
# ===============================================================================
st.subheader("\U0001f4dd Creer une facture")

# Titre editable
facture_titre = st.text_input(
    "\U0001f4dd Titre / objet de la facture",
    value=st.session_state.get("facture_titre", f"Facture travaux - {chantier.get('nom', '')}"),
    key="facture_titre_input",
    placeholder="Ex: Facture acompte lot gros oeuvre"
)
st.session_state["facture_titre"] = facture_titre

# Charger les devis existants pour facturation rapide
devis_existants = db.get_devis(chantier_id=chantier["id"])
devis_non_factures = [d for d in devis_existants if d.get("statut") != "facture"]

source_facture = st.radio(
    "Source de la facture",
    ["A partir d'un devis", "Saisie libre"],
    key="fac_source",
    horizontal=True
)

facture_lignes = []
montant_ht = 0

if source_facture == "A partir d'un devis":
    if devis_non_factures:
        devis_options = {f"{d.get('numero', '?')} - {d.get('objet', 'Devis')} ({float(d.get('montant_ht', 0)):,.2f} \u20ac HT)": d for d in devis_non_factures}
        selected_label = st.selectbox("Selectionner un devis", list(devis_options.keys()), key="fac_devis_select")
        selected_devis = devis_options[selected_label]

        montant_ht = float(selected_devis.get("montant_ht", 0) or 0)
        client_nom = selected_devis.get("client_nom", client_nom)

        # Extraire les lignes du devis
        contenu = selected_devis.get("contenu", "{}")
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

    # Nombre de lignes dynamique avec bouton ajouter
    nb_extra = st.session_state.get("fac_nb_extra", 0)
    nb_lignes = 3 + nb_extra

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

    if st.button("\u2795 Ajouter une ligne", key="add_fac_line"):
        st.session_state["fac_nb_extra"] = nb_extra + 1
        st.rerun()

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

# ===============================================================================
# Enregistrer + generer PDF
# ===============================================================================
if st.button("\U0001f4be Enregistrer et generer la facture", type="primary", use_container_width=True):
    if montant_ht > 0:
        # Numerotation structuree FAC-YYYYMM-NNN
        existing_facs = db.get_factures(chantier_id=chantier["id"])
        _prefix = f"FAC-{datetime.now().strftime('%Y%m')}"
        _nums = []
        for f in existing_facs:
            fn = f.get("numero", "")
            if fn.startswith(_prefix):
                try:
                    _nums.append(int(fn.split("-")[-1]))
                except (ValueError, IndexError):
                    pass
        numero = f"{_prefix}-{max(_nums, default=0)+1:03d}"

        # Contenu JSON pour re-affichage ulterieur
        contenu_json = json.dumps({
            "lignes": facture_lignes,
            "titre": facture_titre,
            "client_nom": client_nom,
            "tva_rate": tva_rate,
            "conditions": conditions,
            "nom_societe": nom_societe if 'nom_societe' in dir() else "",
            "siret": siret if 'siret' in dir() else "",
            "adresse_societe": adresse_societe if 'adresse_societe' in dir() else "",
            "tel_societe": tel_societe if 'tel_societe' in dir() else "",
            "email_societe": email_societe if 'email_societe' in dir() else "",
            "tva_intra": tva_intra if 'tva_intra' in dir() else "",
        }, default=str)

        facture_record = {
            "numero": numero,
            "objet": facture_titre,
            "client_nom": client_nom,
            "montant_ht": montant_ht,
            "montant_tva": tva_montant,
            "montant_ttc": total_ttc,
            "statut": "brouillon",
            "contenu": contenu_json,
        }

        # Si source = devis, lier le devis
        if source_facture == "A partir d'un devis" and devis_non_factures:
            facture_record["devis_id"] = selected_devis.get("id")

        result = db.save_facture(user_id, chantier["id"], facture_record)

        if result:
            st.success(f"\u2705 Facture {numero} enregistree !")

            # Generer et stocker le PDF
            try:
                pdf_bytes = _generate_facture_pdf(
                    {"numero": numero, "objet": facture_titre, "date": datetime.now().strftime("%d/%m/%Y"),
                     "montant_ht": montant_ht, "montant_ttc": total_ttc},
                    facture_lignes,
                    nom_societe if 'nom_societe' in dir() else "",
                    siret if 'siret' in dir() else "",
                    adresse_societe if 'adresse_societe' in dir() else "",
                    tel_societe if 'tel_societe' in dir() else "",
                    email_societe if 'email_societe' in dir() else "",
                    tva_intra if 'tva_intra' in dir() else "",
                    client_nom, tva_rate, conditions,
                    logo_bytes=logo_bytes if 'logo_bytes' in dir() else None,
                    cgv_text=cgv_text if 'cgv_text' in dir() else None
                )
                st.download_button(
                    "\U0001f4e5 Telecharger PDF",
                    data=pdf_bytes,
                    file_name=f"{numero}.pdf",
                    mime="application/pdf",
                    type="secondary",
                    use_container_width=True
                )

                # Upload dans Supabase Storage
                try:
                    storage.upload_generated_document(
                        pdf_bytes, f"{numero}.pdf", chantier["id"], "factures", doc_type="facture"
                    )
                except Exception:
                    pass

            except Exception:
                pass

            # Marquer le devis comme facture si applicable
            if source_facture == "A partir d'un devis" and devis_non_factures:
                try:
                    db.update_devis(selected_devis["id"], {"statut": "facture"})
                except Exception:
                    pass

            st.rerun()
        else:
            st.error("Erreur lors de l'enregistrement de la facture.")
    else:
        st.warning("Le montant HT doit etre superieur a 0.")

st.markdown("---")

# ===============================================================================
# Historique factures (expandable avec re-telechargement PDF)
# ===============================================================================
st.subheader("\U0001f4cb Historique des factures")

factures = db.get_factures(chantier_id=chantier["id"])

if factures:
    # Resume global du chantier
    total_fac_ttc = sum(float(f.get("montant_ttc", 0) or 0) for f in factures)
    total_fac_payees = sum(float(f.get("montant_ttc", 0) or 0) for f in factures if f.get("statut") == "payee")
    total_devis_ttc = sum(
        float(d.get("montant_ht", 0) or 0) * 1.2
        for d in devis_existants
    )
    budget_ref = float(chantier.get("budget_ht", 0) or 0) * 1.2
    ref_ttc = total_devis_ttc if total_devis_ttc > 0 else budget_ref
    reste = ref_ttc - total_fac_ttc

    if ref_ttc > 0:
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            st.metric("\U0001f9fe Total facture", f"{total_fac_ttc:,.2f} \u20ac")
        with col_s2:
            st.metric("\U0001f7e2 Paye", f"{total_fac_payees:,.2f} \u20ac")
        with col_s3:
            st.metric("\U0001f4b8 Reste a facturer", f"{max(reste, 0):,.2f} \u20ac")
        with col_s4:
            impaye = total_fac_ttc - total_fac_payees
            st.metric("\U0001f534 Impaye", f"{impaye:,.2f} \u20ac")

    st.markdown("---")

    # Liste expandable des factures
    for fac in factures:
        fac_id = fac.get("id", "")
        fac_num = fac.get("numero", "?")
        fac_objet = fac.get("objet", "Sans objet")
        fac_ht = float(fac.get("montant_ht", 0) or 0)
        fac_ttc = float(fac.get("montant_ttc", 0) or 0)
        fac_statut = fac.get("statut", "brouillon")
        fac_date = fac.get("created_at", "")[:10] if fac.get("created_at") else ""

        color_map = {"brouillon": "\U0001f7e1", "envoyee": "\U0001f535", "payee": "\U0001f7e2", "annulee": "\U0001f534", "en_attente": "\U0001f7e0"}
        default_color = "\u26aa"
        status_color = color_map.get(fac_statut, default_color)

        with st.expander(f"{status_color} **{fac_num}** \u2014 {fac_objet} \u2014 {fac_ht:,.2f} \u20ac HT \u2014 {fac_statut} \u2014 {fac_date}"):
            # Informations detaillees
            col_i1, col_i2, col_i3 = st.columns(3)
            with col_i1:
                st.markdown(f"**Numero:** {fac_num}")
                st.markdown(f"**Objet:** {fac_objet}")
            with col_i2:
                st.markdown(f"**Montant HT:** {fac_ht:,.2f} \u20ac")
                st.markdown(f"**Montant TTC:** {fac_ttc:,.2f} \u20ac")
            with col_i3:
                st.markdown(f"**Statut:** {fac_statut}")
                st.markdown(f"**Date:** {fac_date}")

            # Afficher le contenu detaille si disponible
            contenu_raw = fac.get("contenu", "{}")
            try:
                contenu_data = json.loads(contenu_raw) if isinstance(contenu_raw, str) else (contenu_raw or {})
                lignes_hist = contenu_data.get("lignes", [])
                if lignes_hist:
                    st.markdown("**Detail des lignes :**")
                    for idx_l, lg in enumerate(lignes_hist):
                        lg_des = lg.get("designation", "")
                        lg_qte = lg.get("quantite", 0)
                        lg_pu = lg.get("prix_unitaire", 0)
                        lg_tot = lg.get("total_ht", 0)
                        st.caption(f"  {idx_l+1}. {lg_des} | Qte: {lg_qte} | PU: {lg_pu:.2f} \u20ac | Total: {lg_tot:.2f} \u20ac")
            except Exception:
                contenu_data = {}

            # Changement de statut
            new_statut = st.selectbox(
                "Changer le statut",
                ["brouillon", "envoyee", "payee", "annulee", "en_attente"],
                index=["brouillon", "envoyee", "payee", "annulee", "en_attente"].index(fac_statut) if fac_statut in ["brouillon", "envoyee", "payee", "annulee", "en_attente"] else 0,
                key=f"fac_statut_{fac_id}"
            )
            if new_statut != fac_statut:
                if st.button(f"\u2705 Valider statut \u2192 {new_statut}", key=f"fac_val_statut_{fac_id}"):
                    db.update_facture(fac_id, {"statut": new_statut})
                    st.success(f"Statut mis a jour: {new_statut}")
                    st.rerun()

            # Boutons d'action
            col_a1, col_a2, col_a3 = st.columns(3)
            with col_a1:
                # Re-telecharger le PDF
                try:
                    if contenu_data and contenu_data.get("lignes"):
                        _soc = contenu_data.get("nom_societe", nom_societe if 'nom_societe' in dir() else "")
                        _siret = contenu_data.get("siret", siret if 'siret' in dir() else "")
                        _addr = contenu_data.get("adresse_societe", adresse_societe if 'adresse_societe' in dir() else "")
                        _tel = contenu_data.get("tel_societe", tel_societe if 'tel_societe' in dir() else "")
                        _email = contenu_data.get("email_societe", email_societe if 'email_societe' in dir() else "")
                        _tva_i = contenu_data.get("tva_intra", tva_intra if 'tva_intra' in dir() else "")
                        _tva_r = contenu_data.get("tva_rate", tva_rate)
                        _cond = contenu_data.get("conditions", conditions)
                        _client = contenu_data.get("client_nom", client_nom)

                        _pdf = _generate_facture_pdf(
                            {"numero": fac_num, "objet": fac_objet,
                             "date": fac_date, "montant_ht": fac_ht, "montant_ttc": fac_ttc},
                            contenu_data["lignes"],
                            _soc, _siret, _addr, _tel, _email, _tva_i,
                            _client, _tva_r, _cond,
                            logo_bytes=logo_bytes if 'logo_bytes' in dir() else None,
                            cgv_text=cgv_text if 'cgv_text' in dir() else None
                        )
                        st.download_button("\U0001f4e5 Telecharger PDF", data=_pdf, file_name=f"{fac_num}.pdf", mime="application/pdf", key=f"dl_pdf_{fac_id}")
                    else:
                        st.caption("Contenu non disponible pour PDF")
                except Exception:
                    st.caption("PDF non disponible")

            with col_a2:
                # Recharger dans editeur
                if st.button("\U0001f504 Recharger dans editeur", key=f"reload_fac_{fac_id}"):
                    try:
                        if contenu_data and contenu_data.get("lignes"):
                            st.session_state["facture_titre"] = fac_objet
                            st.rerun()
                    except Exception:
                        pass

            with col_a3:
                # Supprimer
                if st.button("\U0001f5d1 Supprimer", key=f"del_fac_{fac_id}", type="secondary"):
                    st.session_state[f"confirm_del_fac_{fac_id}"] = True

                if st.session_state.get(f"confirm_del_fac_{fac_id}"):
                    st.warning(f"Confirmer la suppression de {fac_num} ?")
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        if st.button("\u2705 Oui, supprimer", key=f"confirm_yes_fac_{fac_id}"):
                            db.delete_facture(fac_id)
                            st.session_state.pop(f"confirm_del_fac_{fac_id}", None)
                            st.success(f"Facture {fac_num} supprimee.")
                            st.rerun()
                    with col_c2:
                        if st.button("\u274c Annuler", key=f"confirm_no_fac_{fac_id}"):
                            st.session_state.pop(f"confirm_del_fac_{fac_id}", None)
                            st.rerun()
else:
    st.info("Aucune facture enregistree pour ce chantier.")
