"""
utils.py — Fonctions partagées : traitement PDF, images, appels IA Claude
"""

import io
import base64
import streamlit as st
import pdfplumber
import fitz  # PyMuPDF
from PIL import Image
import anthropic

# ─── CSS global réutilisable ───────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}

    .page-header {
        background: linear-gradient(135deg, #0D3B6E 0%, #1B6CA8 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(13, 59, 110, 0.3);
    }
    .page-header h2 {font-size: 2rem; font-weight: 800; margin: 0; letter-spacing: -0.5px;}
    .page-header p {opacity: 0.85; margin-top: 0.4rem; font-size: 1rem;}

    .upload-zone {
        background: white;
        border: 2px dashed #93C5FD;
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }

    .result-box {
        background: white;
        border: 1px solid #E2EBF5;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 2px 16px rgba(0,0,0,0.06);
        margin-top: 1.5rem;
    }
    .result-box h3 {color: #0D3B6E; font-size: 1.2rem; font-weight: 700; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid #E2EBF5;}

    .info-box {
        background: #EFF6FF;
        border-left: 4px solid #1B6CA8;
        padding: 0.9rem 1.2rem;
        border-radius: 0 10px 10px 0;
        margin: 1rem 0;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    .warning-box {
        background: #FFFBEB;
        border-left: 4px solid #F59E0B;
        padding: 0.9rem 1.2rem;
        border-radius: 0 10px 10px 0;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    .success-box {
        background: #F0FDF4;
        border-left: 4px solid #22C55E;
        padding: 0.9rem 1.2rem;
        border-radius: 0 10px 10px 0;
        margin: 1rem 0;
        font-size: 0.9rem;
    }

    .sidebar-brand {
        font-size: 1.4rem;
        font-weight: 800;
        color: #0D3B6E;
        padding: 0.5rem 0 1rem 0;
        border-bottom: 2px solid #E2EBF5;
        margin-bottom: 1.2rem;
    }

    .stButton>button {
        background: linear-gradient(135deg, #0D3B6E 0%, #1B6CA8 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
        box-shadow: 0 2px 8px rgba(13, 59, 110, 0.25) !important;
    }
    .stButton>button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(13, 59, 110, 0.35) !important;
    }
    .api-box {
        background: #FFF7ED;
        border: 1px solid #FCD34D;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin-bottom: 1rem;
        font-size: 0.85rem;
    }
</style>
"""


# ─── Sidebar standard ─────────────────────────────────────────────────────────
def render_sidebar():
    """Affiche la sidebar de navigation commune à toutes les pages."""
    with st.sidebar:
        st.markdown('<div class="sidebar-brand">🏗️ ConducteurPro</div>', unsafe_allow_html=True)

        if "api_key" not in st.session_state:
            st.session_state.api_key = ""

        try:
            if st.secrets.get("ANTHROPIC_API_KEY"):
                st.session_state.api_key = st.secrets["ANTHROPIC_API_KEY"]
        except Exception:
            pass

        if not st.session_state.api_key:
            st.markdown('<div class="api-box">⚠️ Clé API requise</div>', unsafe_allow_html=True)
            key_input = st.text_input("Clé API Anthropic", type="password", placeholder="sk-ant-...", key="api_sidebar")
            if key_input:
                st.session_state.api_key = key_input
                st.rerun()
            st.caption("🔑 [Créer une clé gratuite →](https://console.anthropic.com)")
        else:
            st.success("✅ Claude AI connecté")

        st.divider()
        st.markdown("**Navigation**")
        st.page_link("app.py", label="🏠 Accueil")
        st.page_link("pages/1_Metres.py", label="📐 Métrés automatiques")
        st.page_link("pages/2_DCE.py", label="📋 Synthèse DCE")
        st.page_link("pages/3_Etudes.py", label="🔬 Études techniques")
        st.page_link("pages/4_Planning.py", label="📅 Aide au planning")
        st.page_link("pages/5_PLU.py", label="🗺️ Analyse PLU")
        st.page_link("pages/6_Synthese.py", label="🧠 Synthèse Globale ★")

        st.divider()
        st.caption("ConducteurPro v1.0")
        st.caption("Propulsé par Claude AI")


# ─── Client Anthropic ─────────────────────────────────────────────────────────
def get_client():
    """Retourne un client Anthropic ou None si pas de clé."""
    api_key = st.session_state.get("api_key", "")
    if api_key:
        return anthropic.Anthropic(api_key=api_key)
    return None


def check_api_key():
    """Vérifie la clé API et affiche un message d'erreur si absente."""
    if not st.session_state.get("api_key"):
        st.markdown("""
        <div class="warning-box">
            ⚠️ <strong>Clé API manquante.</strong> Entrez votre clé API Anthropic dans la barre latérale pour utiliser cette fonctionnalité.<br>
            <a href="https://console.anthropic.com" target="_blank">→ Créer une clé gratuite sur console.anthropic.com</a>
        </div>
        """, unsafe_allow_html=True)
        return False
    return True


# ─── Traitement PDF ───────────────────────────────────────────────────────────
def extract_text_from_pdf(uploaded_file) -> str:
    """Extrait le texte complet d'un PDF uploadé via Streamlit."""
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
    """Convertit la 1ère page d'un PDF en image PNG haute résolution."""
    try:
        file_bytes = uploaded_file.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page = doc[0]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return pix.tobytes("png")
    except Exception as e:
        st.error(f"Erreur conversion PDF → image : {e}")
        return None


def encode_image_bytes_to_base64(image_bytes: bytes) -> str:
    """Encode des bytes image en base64 string."""
    return base64.b64encode(image_bytes).decode("utf-8")


def image_file_to_base64(uploaded_file) -> tuple[str, str]:
    """
    Retourne (base64_string, media_type) depuis un fichier image uploadé.
    Supporte PNG, JPEG, WEBP.
    """
    img = Image.open(uploaded_file)
    # Convertir en RGB si nécessaire
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    # Resize si trop grande (Claude Vision : max ~4MB recommandé)
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
    """Tronque le texte à max_chars caractères avec indication."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n[... Document tronqué à {max_chars} caractères pour l'analyse ...]"


# ─── Fonctions IA ─────────────────────────────────────────────────────────────

def analyze_plan_image(image_b64: str, media_type: str, client, extra_info: str = "") -> str:
    """
    Analyse un plan de construction via Claude Vision.
    Retourne un tableau de métrés en Markdown.
    """
    extra = f"\n\nInformations complémentaires fournies par l'utilisateur : {extra_info}" if extra_info else ""

    prompt = f"""Tu es un métreur expert du bâtiment et des travaux publics, avec 20 ans d'expérience.
Analyse ce plan de construction avec précision et professionnalisme.

MISSION : Extraire tous les ouvrages mesurables de ce plan et produire un tableau de métrés complet.

INSTRUCTIONS :
1. Identifie chaque ouvrage visible (cloisons, sols, plafonds, menuiseries, fondations, mígonnerie, etc.)
2. Estime les quantités en utilisant les dimensions lisibles ou les proportions visuelles
3. Indique l'unité appropriée (m², ml, m³, u, forfait)
4. Note les hypothèses faites si des cotes ne sont pas lisibles
5. Ajoute une colonne "Observations" pour les points importants

RÉPONDS AVEC :
- Un résumé du plan en 3 lignes (type de bâtiment, niveau, zone analysée)
- Un tableau Markdown complet avec colonnes : | N° | Ouvrage | Description | Unité | Quantité | Observations |
- Une section "Points d'attention" listant ce qui nécessite vérification sur site{extra}

Sois le plus exhaustif possible. Si une cote n'est pas lisible, estime avec une note."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_b64
                    }
                },
                {"type": "text", "text": prompt}
            ]
        }]
    )
    return response.content[0].text


def synthesize_dce(text: str, client) -> str:
    """Synthétise un DCE et extrait les informations clés pour le CDT."""
    prompt = f"""Tu es un conducteur de travaux senior avec 15 ans d'expérience. Analyse ce DCE (Dossier de Consultation des Entreprises) et fournis une synthèse opérationnelle.

STRUCTURE TA RÉPONSE AINSI :

## 📌 Fiche de synthèse rapide
- **Maître d'ouvrage** :
- **Maître d'œuvre** :
- **Nature des travaux** :
- **Montant estimatif** :
- **Délai d'exécution** :

## 📅 Dates critiques
(Liste toutes les dates importantes : remise d'offre, démarrage, réception, etc.)

## ⚙️ Exigences techniques principales
(Les 5-10 points techniques les plus importants pour l'exécution)

## ⚠️ Points de vigilance
(Ce qui pourrait poser problème, clauses particulières, pénalités, etc.)

## 📄 Documents à fournir
(Liste des documents à remettre avec l'offre ou pendant les travaux)

## 💰 Critères de sélection de l'offre
(Comment sera noté le dossier)

## 🔧 Recommandations pour la préparation du chantier
(Conseils pratiques basés sur ce DCE)

DCE À ANALYSER :
{truncate_text(text)}"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def analyze_technical_study(text: str, study_type: str, client) -> str:
    """Analyse une étude technique et extrait l'essentiel pour le CDT."""
    study_contexts = {
        "béton / fondations": "étude béton armé, fondations et structures en béton. Tu maîtrises les Eurocodes, le BAEL, les classes d'exposition béton, les dosages et la résistance.",
        "structure / charpente": "étude de structure et charpente (bois, métal, béton). Tu maîtrises les charges, les contreventements, les assemblages et les descentes de charges.",
        "thermique / RE2020": "étude thermique et performance énergétique (RE2020, RT2012, BBC). Tu maîtrises les Bbio, Cep, Ic, ponts thermiques et déperditions.",
        "acoustique": "étude acoustique et isolement aux bruits. Tu maîtrises les DnT,A, L'nT,W, les affaiblissements acoustiques et les réglementations NRA."
    }
    context = study_contexts.get(study_type, "étude technique du bâtiment")

    prompt = f"""Tu es un expert en {context}

Analyse cette étude technique et synthétise les informations essentielles pour un conducteur de travaux sur chantier.

STRUCTURE TA RÉPONSE :

## 📋 Résumé exécutif
(3-5 lignes : de quoi traite cette étude, quels sont les enjeux principaux)

## 📊 Données et valeurs clés
(Tableau des valeurs importantes : résistances, indices, coefficients, classes, etc.)

## 🏗️ Contraintes d'exécution
(Ce qui impacte directement le travail sur chantier : séquences obligatoires, produits imposés, tolérances, délais de cure, etc.)

## ⚠️ Points de vigilance critiques
(Ce qu'il ne faut SURTOUT PAS rater, risques de non-conformité)

## 📐 Interfaces avec autres corps d'état
(Ce que cette étude impose aux autres entreprises : mígonnerie, menuiseries, isolation, etc.)

## 📚 Normes et DTU de référence
(Liste les normes citées avec leur objet)

## 📅 Impact sur le planning
(Ce qui conditionne la planification : délais de séchage, contrôles obligatoires, etc.)

ÉTUDE À ANALYSER :
{truncate_text(text)}"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def generate_planning(context: str, client) -> str:
    """Génère une aide au planning basée sur le contexte du projet."""
    prompt = f"""Tu es un planificateur de chantier expert. Basé sur les informations suivantes, aide le conducteur de travaux à organiser son chantier.

STRUCTURE TA RÉPONSE :

## 🗓️ Phasage recommandé des travaux
(Tableau avec : Phase | Description | Durée estimée | Conditions préalables)

## ⏱️ Planning simplifié
(Vue chronologique : semaines ou mois selon la taille du projet)

## 👷 Ressources humaines estimées
(Effectifs par phase : ouvriers, chefs d'équipe, sous-traitants)

## 🏗️ Matériaux et matériel clés
(Approvisionnements critiques à anticiper, délais de livraison à prévoir)

## ⚠️ Risques et marges à prévoir
(Risques climatiques, techniques, administratifs et les marges correspondantes)

## ✅ Checklist de démarrage de chantier
(Liste des actions à faire avant le premier coup de pelleteuse, cochable)

## 📋 Réunions et jalons clés
(Points de contrôle, OPR, réceptions partielles, RICT, DOE, etc.)

CONTEXTE DU PROJET :
{context}"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def analyze_plu(text: str, projet_context: str, client) -> str:
    """Analyse un règlement PLU et vérifie la conformité du projet."""
    prompt = f"""Tu es un expert en droit de l'urbanisme et en règles PLU/PLUi français, avec 20 ans d'expérience.
Analyse ce règlement PLU et extrait toutes les règles applicables au projet décrit.

CONTEXTE DU PROJET :
{projet_context}

STRUCTURE TA RÉPONSE :

## 🗺️ Zone applicable et caractère
(Identifie la zone, son caractère, les destinations autorisées)

## ✅ Usages autorisés / ❌ Interdits
(Liste claire des constructions/usages permis et interdits dans cette zone)

## 📐 Tableau des règles chiffrées applicables
| Règle | Valeur PLU | Valeur projet | Conformité |
|-------|-----------|---------------|------------|
(Emprise au sol, hauteur max, retraits voie, retraits limites, COS si applicable, espaces verts min, stationnement...)

## ⚠️ Points de vigilance et contraintes spécifiques
(Servitudes, secteurs sauvegardés, zones inondables, prescriptions architecturales, matériaux imposés...)

## 📋 Documents à fournir pour le dépôt de permis de construire
(Liste des pièces obligatoires selon ce PLU)

## 🔍 Vérifications terrain indispensables
(Ce que l'IA ne peut pas vérifier et qui nécessite une visite ou une consultation spécifique)

## 💡 Recommandations pour optimiser le projet dans cette zone
(Comment tirer le meilleur parti des règles, maximiser SHAB, variantes possibles...)

RÈGLEMENT PLU À ANALYSER :
{truncate_text(text, max_chars=70000)}"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=5000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def generate_synthese_globale(context: str, options: str, client) -> str:
    """
    Génère une synthèse globale du projet en croisant TOUS les documents disponibles.
    C'est le cerveau central qui mâche 90% du boulot.
    """
    prompt = f"""Tu es un conducteur de travaux senior et expert en gestion de projets de construction,
avec 25 ans d'expérience sur tous types de chantiers (logement, tertiaire, ERP, réhabilitation).

Tu as accès à l'ensemble des documents du projet ci-dessous. Ton rôle est de produire un
RAPPORT DE SYNTHÈSE GLOBALE complet et opérationnel pour le conducteur de travaux.
Ce rapport doit couvrir 90% du travail d'analyse, de sorte que le CDT n'ait plus qu'à
vérifier, ajuster selon son expérience terrain et compléter les informations manquantes.

OPTIONS DU RAPPORT :
{options}

STRUCTURE OBLIGATOIRE DU RAPPORT :

## 📋 1. FICHE PROJET SYNTHÉTIQUE
(Tableau récapitulatif : maître d'ouvrage, MOE, nature, surface, structure, budget, délais, zone PLU, commune)

## ✅ 2. CONFORMITÉ URBANISTIQUE (PLU)
(Pour chaque règle PLU : valeur réglementaire vs valeur projet → CONFORME / ⚠️ À VÉRIFIER / ❌ NON CONFORME)

## ⚠️ 3. POINTS CRITIQUES ET ALERTES
(Les 5-10 points les plus importants classés par criticité que le CDT DOIT absolument gérer)

## 🔗 4. CONTRADICTIONS ET INTERFACES IDENTIFIÉES
(Conflits entre documents, incohérences entre études, interfaces corps d'état critiques)

## 📐 5. SYNTHÈSE DES MÉTRÉS ET QUANTITÉS CLÉS
(Résumé des quantités principales par lot. Sinon estimation à partir des autres documents)

## 📅 6. PLANNING DIRECTEUR RECOMMANDÉ
(Phasage synthétique avec durées, jalons clés, points de contrôle obligatoires)

## 💰 7. BUDGET ESTIMATIF PAR LOT
(Estimation des coûts par lot/corps d'état. Indiquer clairement que ce sont des estimations indicatives)

## 🏗️ 8. CONTRAINTES D'EXÉCUTION MAJEURES
(Séquences imposées, délais de séchage, réservations critiques, interfaces sous-traitants)

## ✅ 9. CHECKLIST DE MISE EN CHANTIER
(Liste cochable de toutes les actions à réaliser avant le premier jour de chantier)

## ⚠️ 10. ANALYSE DES RISQUES
(Tableau : Risque | Probabilité | Impact | Mesure préventive)

## 📌 11. CE QUI RESTE À VÉRIFIER PAR LE CDT
(Liste honnête des éléments que l'IA n'a pas pu analyser ou qui nécessitent vérification terrain)

DOCUMENTS ET CONTEXTE DU PROJET :
{truncate_text(context, max_chars=90000)}"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text
