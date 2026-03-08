"""
utils.py â Fonctions partagÃ©es : traitement PDF, images, appels IA Claude,
gÃ©nÃ©ration devis PDF, vÃ©rification abonnement Stripe.
"""
import io
import base64
import streamlit as st
import pdfplumber
import fitz  # PyMuPDF
from PIL import Image
import anthropic

# âââ CSS global rÃ©utilisable âââââââââââââââââââââââââââââââââââââââââââââââââââââ
GLOBAL_CSS = """
<style>
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 2rem; padding-bottom: 2rem;}
.page-header {
    background: linear-gradient(135deg, #0D3B6E 0%, #1B6CA8 100%);
    padding: 2rem 2.5rem; border-radius: 16px; color: white;
    margin-bottom: 2rem; box-shadow: 0 4px 20px rgba(13, 59, 110, 0.3);
}
.page-header h2 {font-size: 2rem; font-weight: 800; margin: 0; letter-spacing: -0.5px;}
.page-header p {opacity: 0.85; margin-top: 0.4rem; font-size: 1rem;}
.upload-zone {
    background: white; border: 2px dashed #93C5FD;
    border-radius: 16px; padding: 2rem; text-align: center; margin-bottom: 1.5rem;
}
.result-box {
    background: white; border: 1px solid #E2EBF5; border-radius: 16px;
    padding: 2rem; box-shadow: 0 2px 16px rgba(0,0,0,0.06); margin-top: 1.5rem;
}
.result-box h3 {color: #0D3B6E; font-size: 1.2rem; font-weight: 700; margin-bottom: 1rem;
    padding-bottom: 0.5rem; border-bottom: 2px solid #E2EBF5;}
.info-box {
    background: #EFF6FF; border-left: 4px solid #1B6CA8;
    padding: 0.9rem 1.2rem; border-radius: 0 10px 10px 0; margin: 1rem 0; font-size: 0.9rem; line-height: 1.6;
}
.warning-box {
    background: #FFFBEB; border-left: 4px solid #F59E0B;
    padding: 0.9rem 1.2rem; border-radius: 0 10px 10px 0; margin: 1rem 0; font-size: 0.9rem;
}
.success-box {
    background: #F0FDF4; border-left: 4px solid #22C55E;
    padding: 0.9rem 1.2rem; border-radius: 0 10px 10px 0; margin: 1rem 0; font-size: 0.9rem;
}
.sidebar-brand {
    font-size: 1.4rem; font-weight: 800; color: #0D3B6E;
    padding: 0.5rem 0 1rem 0; border-bottom: 2px solid #E2EBF5; margin-bottom: 1.2rem;
}
.stButton>button {
    background: linear-gradient(135deg, #0D3B6E 0%, #1B6CA8 100%) !important;
    color: white !important; border: none !important; border-radius: 10px !important;
    font-weight: 600 !important; transition: all 0.2s !important;
    box-shadow: 0 2px 8px rgba(13, 59, 110, 0.25) !important;
}
.stButton>button:hover {
    transform: translateY(-1px) !important; box-shadow: 0 4px 16px rgba(13, 59, 110, 0.35) !important;
}
.api-box {
    background: #FFF7ED; border: 1px solid #FCD34D;
    border-radius: 10px; padding: 0.8rem 1rem; margin-bottom: 1rem; font-size: 0.85rem;
}
</style>
"""

# âââ Sidebar standard âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def render_sidebar():
    """Affiche la sidebar de navigation commune Ã  toutes les pages."""
    with st.sidebar:
        st.markdown('<div class="sidebar-brand">ðï¸ ConducteurPro</div>', unsafe_allow_html=True)

        if "api_key" not in st.session_state:
            st.session_state.api_key = ""
        try:
            if st.secrets.get("ANTHROPIC_API_KEY"):
                st.session_state.api_key = st.secrets["ANTHROPIC_API_KEY"]
        except Exception:
            pass

        if not st.session_state.api_key:
            st.markdown('<div class="api-box">â ï¸ ClÃ© API requise</div>', unsafe_allow_html=True)
            key_input = st.text_input("ClÃ© API Anthropic", type="password", placeholder="sk-ant-...", key="api_sidebar")
            if key_input:
                st.session_state.api_key = key_input
                st.rerun()
            st.caption("ð [CrÃ©er une clÃ© gratuite â](https://console.anthropic.com)")
        else:
            st.success("â Claude AI connectÃ©")

        # Affichage du plan si connectÃ©
        if st.session_state.get("user_email"):
            plan_labels = {"free": "ð Gratuit", "pro": "ð Pro", "team": "ð¢ Ãquipe"}
            st.caption(f"ð¤ {st.session_state.user_email}")
            st.caption(f"Plan : {plan_labels.get(st.session_state.get('user_plan','free'), 'ð Gratuit')}")

        st.divider()
        st.markdown("**Navigation**")
        st.page_link("app.py", label="ð  Accueil")
        st.page_link("pages/1_Metres.py", label="ð MÃ©trÃ©s automatiques")
        st.page_link("pages/2_DCE.py", label="ð SynthÃ¨se DCE")
        st.page_link("pages/3_Etudes.py", label="ð¬ Ãtudes techniques")
        st.page_link("pages/4_Planning.py", label="ð Aide au planning")
        st.page_link("pages/5_PLU.py", label="ðºï¸ Analyse PLU")
        st.page_link("pages/6_Synthese.py", label="ð§  SynthÃ¨se Globale â")
        st.markdown("---")
        st.page_link("pages/8_Devis.py", label="ð° GÃ©nÃ©rateur de devis")
        st.page_link("pages/9_Abonnement.py", label="â­ Mon abonnement")
        st.divider()
        st.caption("ConducteurPro v2.0")
        st.caption("PropulsÃ© par Claude AI")


# âââ Client Anthropic ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def get_client():
    """Retourne un client Anthropic ou None si pas de clÃ©."""
    api_key = st.session_state.get("api_key", "")
    if api_key:
        return anthropic.Anthropic(api_key=api_key)
    return None


def check_api_key():
    """VÃ©rifie la clÃ© API et affiche un message d'erreur si absente."""
    if not st.session_state.get("api_key"):
        st.markdown("""
        <div class="warning-box">
        â ï¸ <strong>ClÃ© API manquante.</strong> Entrez votre clÃ© API Anthropic dans la barre latÃ©rale.<br>
        <a href="https://console.anthropic.com" target="_blank">â CrÃ©er une clÃ© gratuite sur console.anthropic.com</a>
        </div>
        """, unsafe_allow_html=True)
        return False
    return True


# âââ Traitement PDF ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def extract_text_from_pdf(uploaded_file) -> str:
    """Extrait le texte complet d'un PDF uploadÃ© via Streamlit."""
    text_pages = []
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(f"[Page {i+1}]\n{page_text}")
        return "\n\n".join(text_pages)
    except Exception as e:
        st.error(f"Erreur lecture PDF : {e}")
        return ""


def pdf_first_page_to_image(uploaded_file, zoom: float = 2.5) -> bytes:
    """Convertit la 1Ã¨re page d'un PDF en image PNG haute rÃ©solution."""
    try:
        file_bytes = uploaded_file.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page = doc[0]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return pix.tobytes("png")
    except Exception as e:
        st.error(f"Erreur conversion PDF â image : {e}")
        return None


def encode_image_bytes_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def image_file_to_base64(uploaded_file) -> tuple:
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    max_dim = 2000
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return b64, "image/jpeg"


def truncate_text(text: str, max_chars: int = 80000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n[... Document tronquÃ© Ã  {max_chars} caractÃ¨res pour l'analyse ...]"


# âââ Fonctions IA âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def analyze_plan_image(image_b64: str, media_type: str, client, extra_info: str = "") -> str:
    extra = f"\n\nInformations complÃ©mentaires : {extra_info}" if extra_info else ""
    prompt = f"""Tu es un mÃ©treur expert du bÃ¢timent et des travaux publics, avec 20 ans d'expÃ©rience.
Analyse ce plan de construction avec prÃ©cision et professionnalisme.

MISSION : Extraire tous les ouvrages mesurables de ce plan et produire un tableau de mÃ©trÃ©s complet.

INSTRUCTIONS :
1. Identifie chaque ouvrage visible (cloisons, sols, plafonds, menuiseries, fondations, maÃ§onnerie, etc.)
2. Estime les quantitÃ©s en utilisant les dimensions lisibles ou les proportions visuelles
3. Indique l'unitÃ© appropriÃ©e (mÂ², ml, mÂ³, u, forfait)
4. Note les hypothÃ¨ses faites si des cotes ne sont pas lisibles
5. Ajoute une colonne "Observations" pour les points importants

RÃPONDS AVEC :
- Un rÃ©sumÃ© du plan en 3 lignes (type de bÃ¢timent, niveau, zone analysÃ©e)
- Un tableau Markdown complet avec colonnes : | NÂ° | Ouvrage | Description | UnitÃ© | QuantitÃ© | Observations |
- Une section "Points d'attention" listant ce qui nÃ©cessite vÃ©rification sur site{extra}

Sois le plus exhaustif possible. Si une cote n'est pas lisible, estime avec une note."""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
                {"type": "text", "text": prompt}
            ]
        }]
    )
    return response.content[0].text


def synthesize_dce(text: str, client) -> str:
    prompt = f"""Tu es un conducteur de travaux senior avec 15 ans d'expÃ©rience.
Analyse ce DCE (Dossier de Consultation des Entreprises) et fournis une synthÃ¨se opÃ©rationnelle.

STRUCTURE TA RÃPONSE AINSI :

## ð Fiche de synthÃ¨se rapide
- **MaÃ¯tre d'ouvrage** :
- **MaÃ®tre d'Åuvre** :
- **Nature des travaux** :
- **Montant estimatif** :
- **DÃ©lai d'exÃ©cution** :

## ð Dates critiques

## âï¸ Exigences techniques principales

## â ï¸ Points de vigilance

## ð Documents Ã  fournir

## ð° CritÃ¨res de sÃ©lection de l'offre

## ð§ Recommandations pour la prÃ©paration du chantier

DCE Ã ANALYSER :
{truncate_text(text)}"""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def analyze_technical_study(text: str, study_type: str, client) -> str:
    study_contexts = {
        "bÃ©ton / fondations": "Ã©tude bÃ©ton armÃ©, fondations et structures en bÃ©ton. Tu maÃ®trises les Eurocodes, le BAEL, les classes d'exposition bÃ©ton, les dosages et la rÃ©sistance.",
        "structure / charpente": "Ã©tude de structure et charpente (bois, mÃ©tal, bÃ©ton). Tu maÃ®trises les charges, les contreventements, les assemblages et les descentes de charges.",
        "thermique / RE2020": "Ã©tude thermique et performance Ã©nergÃ©tique (RE2020, RT2012, BBC). Tu maÃ®trises les Bbio, Cep, Ic, ponts thermiques et dÃ©perditions.",
        "acoustique": "Ã©tude acoustique et isolement aux bruits. Tu maÃ®trises les DnT,A, L'nT,W, les affaiblissements acoustiques et les rÃ©glementations NRA.",
    }
    context = study_contexts.get(study_type, "Ã©tude technique du bÃ¢timent")
    prompt = f"""Tu es un expert en {context}
Analyse cette Ã©tude technique et synthÃ©tise les informations essentielles pour un conducteur de travaux sur chantier.

STRUCTURE TA RÃPONSE :

## ð RÃ©sumÃ© exÃ©cutif
## ð DonnÃ©es et valeurs clÃ©s
## ðï¸ Contraintes d'exÃ©cution
## â ï¸ Points de vigilance critiques
## ð Interfaces avec autres corps d'Ã©tat
## ð Normes et DTU de rÃ©fÃ©rence
## ð Impact sur le planning

ÃTUDE Ã ANALYSER :
{truncate_text(text)}"""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def generate_planning(context: str, client) -> str:
    """GÃ©nÃ¨re une aide au planning basÃ©e sur le contexte du projet."""
    prompt = f"""Tu es un planificateur de chantier expert.
BasÃ© sur les informations suivantes, aide le conducteur de travaux Ã  organiser son chantier.

STRUCTURE TA RÃPONSE :

## ðï¸ Phasage recommandÃ© des travaux
(Tableau avec : Phase | Description | DurÃ©e estimÃ©e | Conditions prÃ©alables)

## â±ï¸ Planning simplifiÃ©
(Vue chronologique : semaines ou mois selon la taille du projet)

## ð· Ressources humaines estimÃ©es
(Effectifs par phase : ouvriers, chefs d'Ã©quipe, sous-traitants)

## ðï¸ MatÃ©riaux et matÃ©riel clÃ©s
(Approvisionnements critiques Ã  anticiper, dÃ©lais de livraison Ã  prÃ©voir)

## â ï¸ Risques et marges Ã  prÃ©voir
(Risques climatiques, techniques, administratifs et les marges correspondantes)

## â Checklist de dÃ©marrage de chantier
(Liste des actions Ã  faire avant le premier coup de pelleteuse, cochable)

## ð RÃ©unions et jalons clÃ©s
(Points de contrÃ´le, OPR, rÃ©ceptions partielles, RICT, DOE, etc.)

CONTEXTE DU PROJET :
{context}"""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def analyze_plu(text: str, projet_context: str, client) -> str:
    prompt = f"""Tu es un expert en droit de l'urbanisme et en rÃ¨gles PLU/PLUi franÃ§ais, avec 20 ans d'expÃ©rience.
Analyse ce rÃ¨glement PLU et extrait toutes les rÃ¨gles applicables au projet dÃ©crit.

CONTEXTE DU PROJET : {projet_context}

STRUCTURE TA RÃPONSE :

## ðºï¸ Zone applicable et caractÃ¨re
## â Usages autorisÃ©s / â Interdits
## ð Tableau des rÃ¨gles chiffrÃ©es applicables
| RÃ¨gle | Valeur PLU | Valeur projet | ConformitÃ© |
|-------|-----------|---------------|------------|
## â ï¸ Points de vigilance et contraintes spÃ©cifiques
## ð Documents Ã  fournir pour le dÃ©pÃ´t de permis de construire
## ð VÃ©rifications terrain indispensables
## ð¡ Recommandations pour optimiser le projet dans cette zone

RÃGLEMENT PLU Ã ANALYSER :
{truncate_text(text, max_chars=70000)}"""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=5000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def generate_synthese_globale(context: str, options: str, client) -> str:
    prompt = f"""Tu es un conducteur de travaux senior et expert en gestion de projets de construction, avec 25 ans d'expÃ©rience.
Tu as accÃ¨s Ã  l'ensemble des documents du projet ci-dessous.
Produis un RAPPORT DE SYNTHÃSE GLOBALE complet et opÃ©rationnel.

OPTIONS DU RAPPORT : {options}

STRUCTURE OBLIGATOIRE DU RAPPORT :

## ð 1. FICHE PROJET SYNTHÃTIQUE
## â 2. CONFORMITÃ URBANISTIQUE (PLU)
## â ï¸ 3. POINTS CRITIQUES ET ALERTES
## ð 4. CONTRADICTIONS ET INTERFACES IDENTIFIÃES
## ð 5. SYNTHÃSE DES MÃTRÃS ET QUANTITÃS CLÃS
## ð 6. PLANNING DIRECTEUR RECOMMANDÃ
## ð° 7. BUDGET ESTIMATIF PAR LOT
## ðï¸ 8. CONTRAINTES D'EXÃCUTION MAJEURES
## â 9. CHECKLIST DE MISE EN CHANTIER
## â ï¸ 10. ANALYSE DES RISQUES
## ð 11. CE QUI RESTE Ã VÃRIFIER PAR LE CDT

DOCUMENTS ET CONTEXTE DU PROJET :
{truncate_text(context, max_chars=90000)}"""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


# âââ GÃ©nÃ©ration de devis : lots par IA ââââââââââââââââââââââââââââââââââââââââââââ
def generate_devis_lots(projet_desc: str, client) -> list:
    """GÃ©nÃ¨re les lignes de devis (lots + estimations) pour un projet donnÃ©."""
    import json
    prompt = f"""Tu es un Ã©conomiste de la construction expert. Pour le projet suivant, gÃ©nÃ¨re une liste
de lots de travaux avec des estimations de prix unitaires rÃ©alistes (prix 2024-2025 en France).

PROJET : {projet_desc}

RÃ©ponds UNIQUEMENT avec un tableau JSON valide, sans markdown, sans explication.
Format exact :
[
  {{"lot": "Lot 01", "designation": "Installation de chantier et clÃ´ture de chantier", "unite": "Fft", "quantite": 1, "prix_unitaire_ht": 3500}},
  {{"lot": "Lot 02", "designation": "Terrassements et fouilles", "unite": "mÂ³", "quantite": 50, "prix_unitaire_ht": 45}}
]

Inclure tous les lots standards pour ce type de projet (8 Ã  15 lots). Prix rÃ©alistes France 2024."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())


# âââ GÃ©nÃ©ration PDF du devis âââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def generate_devis_pdf(entreprise: dict, devis: dict, lignes, logo_b64: str = None) -> bytes:
    """GÃ©nÃ¨re un PDF professionnel du devis. Retourne les bytes du PDF."""
    from fpdf import FPDF
    import tempfile, os

    df = lignes.copy()
    df["total_ht"] = df["quantite"].fillna(0) * df["prix_unitaire_ht"].fillna(0)
    total_ht = df["total_ht"].sum()
    tva_taux = float(devis.get("tva_taux", 20.0))
    tva_montant = total_ht * tva_taux / 100
    total_ttc = total_ht + tva_montant

    BLEU = (13, 59, 110)
    BLEU_CLAIR = (235, 244, 255)
    GRIS = (245, 247, 250)
    BLANC = (255, 255, 255)

    class DevisPDF(FPDF):
        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "I", 7.5)
            self.set_text_color(150, 150, 150)
            self.cell(0, 5, f"Page {self.page_no()} â {entreprise.get('nom', '')} â SIRET {entreprise.get('siret', '')}", align="C")

    pdf = DevisPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Logo
    if logo_b64:
        try:
            logo_bytes = base64.b64decode(logo_b64)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(logo_bytes)
                tmp_path = tmp.name
            pdf.image(tmp_path, x=14, y=14, w=32)
            os.unlink(tmp_path)
        except:
            pass

    # Infos entreprise
    pdf.set_xy(14, 50)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*BLEU)
    pdf.cell(90, 6, entreprise.get("nom", ""), ln=True)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(70, 70, 70)
    for field in ["adresse", "code_postal", "ville", "telephone", "email", "siret"]:
        val = entreprise.get(field, "")
        if val:
            label = "SIRET : " if field == "siret" else ""
            pdf.set_x(14)
            pdf.cell(90, 4.5, f"{label}{val}", ln=True)

    # Badge DEVIS
    pdf.set_fill_color(*BLEU)
    pdf.set_text_color(*BLANC)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_xy(128, 14)
    pdf.cell(68, 12, "DEVIS", align="C", fill=True)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*BLEU)
    pdf.set_xy(128, 28)
    pdf.cell(68, 5.5, f"N\u00b0 {devis.get('numero','')}", align="C")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(70, 70, 70)
    pdf.set_xy(128, 34)
    pdf.cell(68, 5, f"Date : {devis.get('date','')}", align="C")
    pdf.set_xy(128, 39)
    pdf.cell(68, 5, f"Validit\u00e9 : {devis.get('validite','')}", align="C")

    # Client
    pdf.set_fill_color(*BLEU_CLAIR)
    pdf.set_xy(115, 50)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*BLEU)
    pdf.cell(81, 5.5, "CLIENT", fill=True)
    pdf.set_xy(115, 56)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(81, 5.5, devis.get("client_nom", ""))
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(60, 60, 60)
    for f in ["client_adresse", "client_cp", "client_ville", "client_tel"]:
        val = devis.get(f, "")
        if val:
            pdf.set_x(115)
            pdf.cell(81, 4.5, val, ln=True)

    # Objet
    pdf.set_xy(14, 88)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*BLEU)
    pdf.cell(25, 5.5, "Objet :")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(155, 5.5, devis.get("objet", "")[:95])

    # Tableau
    y0 = 100
    pdf.set_xy(14, y0)
    col_widths = [24, 78, 14, 14, 26, 26]
    headers = ["Lot", "D\u00e9signation", "Qt\u00e9", "Unit\u00e9", "P.U. HT", "Total HT"]
    aligns_h = ["L", "L", "C", "C", "R", "R"]

    pdf.set_fill_color(*BLEU)
    pdf.set_text_color(*BLANC)
    pdf.set_font("Helvetica", "B", 8.5)
    for h, w, a in zip(headers, col_widths, aligns_h):
        pdf.cell(w, 7.5, h, fill=True, align=a)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    alt = False
    for _, row in df.iterrows():
        if pdf.get_y() > 255:
            pdf.add_page()
        pdf.set_fill_color(*GRIS) if alt else pdf.set_fill_color(*BLANC)
        pdf.set_text_color(30, 30, 30)
        vals = [
            str(row.get("lot", ""))[:20],
            str(row.get("designation", ""))[:58],
            f"{row.get('quantite', 0):.1f}",
            str(row.get("unite", ""))[:6],
            f"{row.get('prix_unitaire_ht', 0):.2f} \u20ac",
            f"{row.get('total_ht', 0):.2f} \u20ac",
        ]
        aligns_r = ["L", "L", "C", "C", "R", "R"]
        for v, w, a in zip(vals, col_widths, aligns_r):
            pdf.cell(w, 6.5, v, fill=True, align=a)
        pdf.ln()
        alt = not alt

    # Totaux
    y_tot = pdf.get_y() + 5
    pdf.set_xy(118, y_tot)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(46, 5.5, "Total HT :", align="R")
    pdf.cell(32, 5.5, f"{total_ht:,.2f} \u20ac", align="R")
    pdf.ln()
    pdf.set_x(118)
    pdf.cell(46, 5.5, f"TVA {tva_taux:.1f}% :", align="R")
    pdf.cell(32, 5.5, f"{tva_montant:,.2f} \u20ac", align="R")
    pdf.ln()

    y_ttc = pdf.get_y() + 2
    pdf.set_fill_color(*BLEU)
    pdf.set_text_color(*BLANC)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_xy(114, y_ttc)
    pdf.cell(82, 8.5, f"TOTAL TTC : {total_ttc:,.2f} \u20ac", align="R", fill=True)
    pdf.ln()

    # Conditions
    y_c = pdf.get_y() + 8
    if y_c > 255:
        pdf.add_page()
        y_c = 20
    pdf.set_xy(14, y_c)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*BLEU)
    pdf.cell(180, 5, "Conditions de paiement :", ln=True)
    pdf.set_x(14)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(180, 4.5, devis.get("conditions_paiement", ""))

    if devis.get("notes"):
        pdf.set_x(14)
        pdf.multi_cell(180, 4.5, devis.get("notes", ""))

    # Signatures
    y_sig = pdf.get_y() + 12
    if y_sig > 258:
        pdf.add_page()
        y_sig = 175
    pdf.set_xy(14, y_sig)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(90, 4.5, "Signature du prestataire :")
    pdf.cell(90, 4.5, "Bon pour accord â signature client :")
    pdf.ln()
    pdf.set_x(14)
    pdf.cell(90, 18, "", border=1)
    pdf.cell(90, 18, "", border=1)

    # Mentions
    pdf.set_xy(14, pdf.get_y() + 4)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(180, 3.5, entreprise.get("mentions", ""))

    return bytes(pdf.output())


# âââ VÃ©rification abonnement Stripe âââââââââââââââââââââââââââââââââââââââââââââââ
def check_subscription_status(email: str) -> str:
    """
    VÃ©rifie le statut d'abonnement d'un utilisateur via l'API Stripe.
    Retourne : 'free', 'pro', ou 'team'
    """
    stripe_key = st.secrets.get("STRIPE_SECRET_KEY", "")
    if not stripe_key:
        return "free"

    try:
        import stripe
        stripe.api_key = stripe_key

        customers = stripe.Customer.list(email=email, limit=1)
        if not customers.data:
            return "free"

        customer_id = customers.data[0].id
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status="active",
            limit=10
        )

        if not subscriptions.data:
            return "free"

        team_price_ids = [p.strip() for p in st.secrets.get("STRIPE_PRICE_TEAM", "").split(",") if p.strip()]
        pro_price_ids = [p.strip() for p in st.secrets.get("STRIPE_PRICE_PRO", "").split(",") if p.strip()]

        for sub in subscriptions.data:
            for item in sub["items"]["data"]:
                price_id = item["price"]["id"]
                if price_id in team_price_ids:
                    return "team"
                if price_id in pro_price_ids:
                    return "pro"

        return "pro"  # Abonnement actif mais price non reconnu

    except Exception as e:
        st.warning(f"Impossible de vÃ©rifier l'abonnement : {e}")
        return "free"
