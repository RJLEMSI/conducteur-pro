"""
Generateur de factures PDF professionnelles pour ConducteurPro.
Utilise fpdf2 pour creer des factures pretes a envoyer aux clients.
"""
import io
import os
from datetime import datetime
from fpdf import FPDF


# Chercher la police DejaVu Sans sur le systeme
FONT_DIR = None
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/dejavu",
    "/usr/local/share/fonts",
]
for p in FONT_PATHS:
    if os.path.isdir(p):
        FONT_DIR = p
        break


class InvoicePDF(FPDF):
    """PDF de facture professionnelle avec en-tete et pied de page."""

    def __init__(self, company_info: dict = None):
        super().__init__()
        self.company = company_info or {}
        self.set_auto_page_break(auto=True, margin=25)

        # Ajouter police Unicode si disponible
        if FONT_DIR:
            regular = os.path.join(FONT_DIR, "DejaVuSans.ttf")
            bold = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
            if os.path.isfile(regular):
                self.add_font("DejaVu", "", regular, uni=True)
            if os.path.isfile(bold):
                self.add_font("DejaVu", "B", bold, uni=True)
            self._use_dejavu = os.path.isfile(regular)
        else:
            self._use_dejavu = False

    def _font(self, style="", size=10):
        """Set font - utilise DejaVu si disponible, sinon Helvetica."""
        name = "DejaVu" if self._use_dejavu else "Helvetica"
        self.set_font(name, style, size)

    def header(self):
        # Bandeau bleu en haut
        self.set_fill_color(27, 79, 138)
        self.rect(0, 0, 210, 8, "F")

        # Logo / Nom entreprise
        self.set_y(14)
        self._font("B", 22)
        self.set_text_color(27, 79, 138)
        company_name = self.company.get("company_name") or "ConducteurPro"
        self.cell(0, 10, company_name, ln=True)

        # Infos entreprise sous le nom
        self._font("", 9)
        self.set_text_color(100, 110, 120)
        siret = self.company.get("siret", "")
        phone = self.company.get("phone", "")
        email = self.company.get("email", "")
        address = self.company.get("address", "")

        if siret:
            self.cell(0, 5, f"SIRET : {siret}", ln=True)
        if phone:
            self.cell(0, 5, f"Tel : {phone}", ln=True)
        if email:
            self.cell(0, 5, f"Email : {email}", ln=True)
        if address:
            self.cell(0, 5, address, ln=True)
        self.ln(4)

    def footer(self):
        self.set_y(-20)
        self.set_fill_color(27, 79, 138)
        self.rect(0, self.h - 8, 210, 8, "F")
        self.set_y(-18)
        self._font("", 7)
        self.set_text_color(130, 140, 150)
        company_name = self.company.get("company_name") or "ConducteurPro"
        self.cell(0, 4, f"{company_name} - Document genere automatiquement", align="C", ln=True)
        self.cell(0, 4, f"Page {self.page_no()}/{{nb}}", align="C")


def generate_invoice_pdf(
    facture: dict,
    company_info: dict = None,
    client_info: dict = None,
    chantier_info: dict = None,
    lignes: list = None,
) -> bytes:
    """Genere un PDF de facture professionnelle et retourne les bytes."""
    if company_info is None:
        company_info = {}
    if client_info is None:
        client_info = {}
    if chantier_info is None:
        chantier_info = {}
    if lignes is None:
        lignes = []

    # Symbole monnaie - utilise EUR si pas de police Unicode
    euro = "EUR"
    if FONT_DIR:
        euro = "\u20ac"

    pdf = InvoicePDF(company_info=company_info)
    pdf.alias_nb_pages()
    pdf.add_page()

    # TITRE FACTURE
    pdf._font("B", 18)
    pdf.set_text_color(27, 79, 138)
    pdf.cell(0, 10, "FACTURE", ln=True)

    # Numero et dates
    pdf._font("B", 11)
    pdf.set_text_color(40, 50, 60)
    numero = facture.get("numero", "N/A")
    pdf.cell(0, 7, f"N. {numero}", ln=True)

    pdf._font("", 10)
    pdf.set_text_color(80, 90, 100)
    date_facture = facture.get("date_facture", datetime.now().strftime("%Y-%m-%d"))
    date_echeance = facture.get("date_echeance", "")
    pdf.cell(0, 6, f"Date : {date_facture}", ln=True)
    if date_echeance:
        pdf.cell(0, 6, f"Echeance : {date_echeance}", ln=True)
    pdf.ln(6)

    # BLOC CLIENT
    y_start = pdf.get_y()
    pdf.set_fill_color(245, 247, 250)
    pdf.rect(110, y_start, 90, 35, "F")
    pdf.set_draw_color(220, 225, 230)
    pdf.rect(110, y_start, 90, 35, "D")

    pdf.set_xy(114, y_start + 3)
    pdf._font("B", 10)
    pdf.set_text_color(27, 79, 138)
    pdf.cell(0, 5, "FACTURER A :", ln=True)

    pdf.set_x(114)
    pdf._font("B", 10)
    pdf.set_text_color(40, 50, 60)
    client_nom = client_info.get("nom") or facture.get("client_nom", "Client")
    pdf.cell(0, 5, client_nom, ln=True)

    pdf.set_x(114)
    pdf._font("", 9)
    pdf.set_text_color(80, 90, 100)
    client_email = client_info.get("email", "")
    client_tel = client_info.get("tel", "")
    client_adresse = client_info.get("adresse", "")

    if client_adresse:
        pdf.cell(0, 5, client_adresse, ln=True)
        pdf.set_x(114)
    if client_email:
        pdf.cell(0, 5, client_email, ln=True)
        pdf.set_x(114)
    if client_tel:
        pdf.cell(0, 5, client_tel, ln=True)

    # Chantier reference
    pdf.set_y(y_start + 40)
    chantier_nom = chantier_info.get("nom", "")
    if chantier_nom:
        pdf._font("", 9)
        pdf.set_text_color(80, 90, 100)
        pdf.cell(0, 6, f"Chantier : {chantier_nom}", ln=True)

    objet = facture.get("objet", "")
    if objet:
        pdf.cell(0, 6, f"Objet : {objet}", ln=True)
    pdf.ln(8)

    # TABLEAU DES PRESTATIONS
    # En-tete tableau
    pdf.set_fill_color(27, 79, 138)
    pdf.set_text_color(255, 255, 255)
    pdf._font("B", 9)
    col_widths = [90, 20, 35, 45]
    headers_txt = ["Description", "Qte", "Prix unit. HT", "Montant HT"]
    for i, h in enumerate(headers_txt):
        pdf.cell(col_widths[i], 8, h, border=0, fill=True, align="C" if i > 0 else "L")
    pdf.ln()

    # Lignes du tableau
    pdf.set_text_color(40, 50, 60)
    pdf._font("", 9)
    fill = False

    if lignes:
        for ligne in lignes:
            if fill:
                pdf.set_fill_color(248, 250, 252)
            else:
                pdf.set_fill_color(255, 255, 255)
            desc = str(ligne.get("description", ""))[:55]
            qte = str(ligne.get("quantite", 1))
            pu = f"{float(ligne.get('prix_unitaire', 0)):,.2f} {euro}"
            mt = f"{float(ligne.get('montant', 0)):,.2f} {euro}"
            pdf.cell(col_widths[0], 7, desc, fill=True)
            pdf.cell(col_widths[1], 7, qte, fill=True, align="C")
            pdf.cell(col_widths[2], 7, pu, fill=True, align="R")
            pdf.cell(col_widths[3], 7, mt, fill=True, align="R")
            pdf.ln()
            fill = not fill
    else:
        # Ligne unique avec le montant total
        montant_ht = float(facture.get("montant_ht", 0))
        objet_line = facture.get("objet", "Prestation")
        pdf.set_fill_color(255, 255, 255)
        pdf.cell(col_widths[0], 7, objet_line[:55], fill=True)
        pdf.cell(col_widths[1], 7, "1", fill=True, align="C")
        pdf.cell(col_widths[2], 7, f"{montant_ht:,.2f} {euro}", fill=True, align="R")
        pdf.cell(col_widths[3], 7, f"{montant_ht:,.2f} {euro}", fill=True, align="R")
        pdf.ln()

    # Ligne separatrice
    pdf.set_draw_color(27, 79, 138)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # TOTAUX
    montant_ht = float(facture.get("montant_ht", 0))
    tva_pct = float(facture.get("tva_pct", 20))
    tva_montant = float(facture.get("tva_montant", montant_ht * tva_pct / 100))
    montant_ttc = float(facture.get("montant_ttc", montant_ht + tva_montant))

    x_label = 120
    x_val = 165
    w_val = 35

    pdf._font("", 10)
    pdf.set_text_color(60, 70, 80)

    pdf.set_x(x_label)
    pdf.cell(45, 7, "Total HT :", align="R")
    pdf.cell(w_val, 7, f"{montant_ht:,.2f} {euro}", align="R", ln=True)

    pdf.set_x(x_label)
    pdf.cell(45, 7, f"TVA ({tva_pct:.1f}%) :", align="R")
    pdf.cell(w_val, 7, f"{tva_montant:,.2f} {euro}", align="R", ln=True)

    # Ligne TTC en gras avec fond
    pdf.set_fill_color(27, 79, 138)
    pdf.set_text_color(255, 255, 255)
    pdf._font("B", 12)
    pdf.set_x(x_label)
    pdf.cell(45, 9, "TOTAL TTC :", align="R", fill=True)
    pdf.cell(w_val, 9, f"{montant_ttc:,.2f} {euro}", align="R", fill=True, ln=True)

    pdf.ln(10)

    # CONDITIONS DE PAIEMENT
    pdf.set_text_color(40, 50, 60)
    pdf._font("B", 9)
    pdf.cell(0, 7, "Conditions de paiement", ln=True)
    pdf._font("", 8)
    pdf.set_text_color(100, 110, 120)

    if date_echeance:
        pdf.cell(0, 5, f"Paiement attendu avant le {date_echeance}.", ln=True)
    else:
        pdf.cell(0, 5, "Paiement a 30 jours a compter de la date de facturation.", ln=True)

    pdf.cell(0, 5, "En cas de retard, des penalites de 3 fois le taux d'interet legal seront appliquees.", ln=True)
    pdf.cell(0, 5, f"Indemnite forfaitaire de recouvrement : 40,00 {euro}.", ln=True)

    pdf.ln(8)

    # MENTION TVA
    pdf._font("", 7)
    pdf.set_text_color(150, 160, 170)
    if tva_pct == 0:
        pdf.cell(0, 4, "TVA non applicable, art. 293 B du CGI", ln=True)
    else:
        pdf.cell(0, 4, f"TVA a {tva_pct:.1f}% incluse dans le montant TTC.", ln=True)

    # Return PDF bytes
    return pdf.output()
