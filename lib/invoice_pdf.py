"""
Générateur de factures PDF professionnelles pour ConducteurPro.
Utilise fpdf2 pour créer des factures prêtes à envoyer aux clients.
"""
import io
from datetime import datetime
from fpdf import FPDF


class InvoicePDF(FPDF):
    """PDF de facture professionnelle avec en-tête et pied de page."""

    def __init__(self, company_info: dict = None):
        super().__init__()
        self.company = company_info or {}
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        # ── Bandeau bleu en haut ──
        self.set_fill_color(27, 79, 138)  # #1B4F8A
        self.rect(0, 0, 210, 8, "F")

        # ── Logo / Nom entreprise ──
        self.set_y(14)
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(27, 79, 138)
        company_name = self.company.get("company_name") or "ConducteurPro"
        self.cell(0, 10, company_name, ln=True)

        # ── Infos entreprise sous le nom ──
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 110, 120)
        siret = self.company.get("siret", "")
        address = self.company.get("address", "")
        phone = self.company.get("phone", "")
        email = self.company.get("email", "")
        infos = []
        if siret:
            infos.append(f"SIRET: {siret}")
        if address:
            infos.append(address)
        if phone:
            infos.append(phone)
        if email:
            infos.append(email)
        if infos:
            self.cell(0, 5, " | ".join(infos), ln=True)
        self.ln(4)

    def footer(self):
        self.set_y(-20)
        # Ligne séparatrice
        self.set_draw_color(200, 210, 220)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(130, 140, 150)
        company_name = self.company.get("company_name") or "ConducteurPro"
        siret = self.company.get("siret", "")
        footer_txt = f"{company_name}"
        if siret:
            footer_txt += f" - SIRET: {siret}"
        footer_txt += f"  |  Page {self.page_no()}/{{nb}}"
        self.cell(0, 5, footer_txt, align="C")


def generate_invoice_pdf(
    facture: dict,
    company_info: dict = None,
    client_info: dict = None,
    chantier_info: dict = None,
    lignes: list = None,
) -> bytes:
    """
    Génère un PDF de facture professionnel.

    Args:
        facture: dict avec numero, date_facture, date_echeance, montant_ht, tva_pct, tva_montant, montant_ttc, statut, objet
        company_info: dict avec company_name, siret, address, phone, email
        client_info: dict avec nom, adresse, email, tel
        chantier_info: dict avec nom, adresse
        lignes: liste de dicts avec description, quantite, prix_unitaire, montant

    Returns:
        bytes du PDF généré
    """
    company_info = company_info or {}
    client_info = client_info or {}
    chantier_info = chantier_info or {}
    lignes = lignes or []

    pdf = InvoicePDF(company_info=company_info)
    pdf.alias_nb_pages()
    pdf.add_page()

    # ── TITRE FACTURE ──
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(27, 79, 138)
    pdf.cell(0, 10, "FACTURE", ln=True)

    # Numéro et dates
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(40, 50, 60)
    pdf.cell(0, 7, f"N\u00b0 {facture.get('numero', 'N/A')}", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 90, 100)
    date_facture = facture.get("date_facture", datetime.now().strftime("%Y-%m-%d"))
    date_echeance = facture.get("date_echeance", "")
    pdf.cell(0, 6, f"Date : {date_facture}", ln=True)
    if date_echeance:
        pdf.cell(0, 6, f"\u00c9ch\u00e9ance : {date_echeance}", ln=True)
    pdf.ln(6)

    # ── BLOC CLIENT ──
    # Cadre gris clair pour le client
    y_start = pdf.get_y()
    pdf.set_fill_color(245, 247, 250)
    pdf.rect(110, y_start, 90, 35, "F")
    pdf.set_draw_color(220, 225, 230)
    pdf.rect(110, y_start, 90, 35, "D")

    # Label
    pdf.set_xy(112, y_start + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(100, 110, 120)
    pdf.cell(0, 4, "FACTURER \u00c0", ln=True)

    # Nom client
    pdf.set_x(112)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 40, 50)
    client_nom = client_info.get("nom") or facture.get("client_nom", "Client")
    pdf.cell(0, 6, client_nom, ln=True)

    # Adresse client
    pdf.set_x(112)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 90, 100)
    client_addr = client_info.get("adresse", "")
    if client_addr:
        pdf.cell(0, 5, client_addr[:45], ln=True)

    client_email = client_info.get("email", "")
    if client_email:
        pdf.set_x(112)
        pdf.cell(0, 5, client_email, ln=True)

    client_tel = client_info.get("tel", "")
    if client_tel:
        pdf.set_x(112)
        pdf.cell(0, 5, client_tel, ln=True)

    # Chantier info (côté gauche)
    pdf.set_xy(10, y_start)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(100, 110, 120)
    pdf.cell(0, 4, "CHANTIER", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(30, 40, 50)
    chantier_nom = chantier_info.get("nom", "")
    chantier_addr = chantier_info.get("adresse", "")
    if chantier_nom:
        pdf.cell(0, 6, chantier_nom, ln=True)
    if chantier_addr:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(80, 90, 100)
        pdf.cell(0, 5, chantier_addr, ln=True)

    pdf.set_y(y_start + 40)

    # ── OBJET ──
    objet = facture.get("objet", "")
    if objet:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(40, 50, 60)
        pdf.cell(30, 7, "Objet :")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, objet, ln=True)
        pdf.ln(4)

    # ── TABLEAU DES LIGNES ──
    # En-tête du tableau
    pdf.set_fill_color(27, 79, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    col_widths = [90, 20, 35, 45]
    headers = ["Description", "Qt\u00e9", "Prix unit. HT", "Montant HT"]
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, border=0, fill=True, align="C" if i > 0 else "L")
    pdf.ln()

    # Lignes du tableau
    pdf.set_text_color(40, 50, 60)
    pdf.set_font("Helvetica", "", 9)
    fill = False

    if lignes:
        for ligne in lignes:
            if fill:
                pdf.set_fill_color(248, 250, 252)
            else:
                pdf.set_fill_color(255, 255, 255)
            desc = str(ligne.get("description", ""))[:55]
            qte = str(ligne.get("quantite", 1))
            pu = f"{float(ligne.get('prix_unitaire', 0)):,.2f} \u20ac"
            mt = f"{float(ligne.get('montant', 0)):,.2f} \u20ac"
            pdf.cell(col_widths[0], 7, desc, fill=True)
            pdf.cell(col_widths[1], 7, qte, fill=True, align="C")
            pdf.cell(col_widths[2], 7, pu, fill=True, align="R")
            pdf.cell(col_widths[3], 7, mt, fill=True, align="R")
            pdf.ln()
            fill = not fill
    else:
        # Pas de lignes détaillées — afficher une ligne résumé
        pdf.set_fill_color(255, 255, 255)
        desc = objet or "Prestations selon devis"
        pdf.cell(col_widths[0], 7, desc[:55], fill=True)
        pdf.cell(col_widths[1], 7, "1", fill=True, align="C")
        montant_ht = float(facture.get("montant_ht", 0))
        pdf.cell(col_widths[2], 7, f"{montant_ht:,.2f} \u20ac", fill=True, align="R")
        pdf.cell(col_widths[3], 7, f"{montant_ht:,.2f} \u20ac", fill=True, align="R")
        pdf.ln()

    # Ligne séparatrice
    pdf.set_draw_color(200, 210, 220)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # ── TOTAUX ──
    montant_ht = float(facture.get("montant_ht", 0))
    tva_pct = float(facture.get("tva_pct", 20))
    tva_montant = float(facture.get("tva_montant", montant_ht * tva_pct / 100))
    montant_ttc = float(facture.get("montant_ttc", montant_ht + tva_montant))

    x_label = 120
    x_val = 165
    w_val = 35

    # Total HT
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 90, 100)
    pdf.set_x(x_label)
    pdf.cell(45, 7, "Total HT")
    pdf.cell(w_val, 7, f"{montant_ht:,.2f} \u20ac", align="R", ln=True)

    # TVA
    pdf.set_x(x_label)
    pdf.cell(45, 7, f"TVA ({tva_pct:.1f}%)")
    pdf.cell(w_val, 7, f"{tva_montant:,.2f} \u20ac", align="R", ln=True)

    # Ligne
    pdf.set_draw_color(27, 79, 138)
    pdf.line(x_label, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    # Total TTC (en gras et en bleu)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(27, 79, 138)
    pdf.set_x(x_label)
    pdf.cell(45, 9, "TOTAL TTC")
    pdf.cell(w_val, 9, f"{montant_ttc:,.2f} \u20ac", align="R", ln=True)

    pdf.ln(10)

    # ── CONDITIONS DE PAIEMENT ──
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(40, 50, 60)
    pdf.cell(0, 6, "Conditions de paiement", ln=True)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(100, 110, 120)

    if date_echeance:
        pdf.cell(0, 5, f"Paiement attendu avant le {date_echeance}.", ln=True)
    else:
        pdf.cell(0, 5, "Paiement \u00e0 30 jours \u00e0 compter de la date de facturation.", ln=True)

    pdf.cell(0, 5, "En cas de retard, des p\u00e9nalit\u00e9s de 3 fois le taux d'int\u00e9r\u00eat l\u00e9gal seront appliqu\u00e9es.", ln=True)
    pdf.cell(0, 5, "Indemnit\u00e9 forfaitaire de recouvrement : 40,00 \u20ac.", ln=True)

    pdf.ln(8)

    # ── MENTION TVA ──
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(150, 160, 170)
    pdf.cell(0, 4, "TVA non applicable, art. 293 B du CGI" if tva_pct == 0 else f"TVA \u00e0 {tva_pct:.1f}% incluse dans le montant TTC.", ln=True)

    # Return PDF bytes
    return pdf.output()
