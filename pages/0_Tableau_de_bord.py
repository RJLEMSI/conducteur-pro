import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date
from lib.helpers import page_setup, render_saas_sidebar
from lib import db
from utils import GLOBAL_CSS

# Mapping statuts pour affichage
STATUT_DISPLAY = {
    "en_cours": "En cours", "termine": "Termine", "en_attente": "En attente",
    "annule": "Annule", "brouillon": "Brouillon", "envoye": "Envoye",
    "envoyÃÂÃÂ©e": "Envoyee", "accepte": "Accepte", "refuse": "Refuse",
    "payee": "Payee", "en_retard": "En retard", "valide": "Valide",
}


# Phases BTP par defaut pour generation rapide
PHASES_BTP = [
    {"nom": "Installation chantier", "duree": 7, "couleur": "#FF6B6B", "categorie": "preparation"},
    {"nom": "Terrassement / Fondations", "duree": 14, "couleur": "#4ECDC4", "categorie": "gros_oeuvre"},
    {"nom": "Gros oeuvre / Maconnerie", "duree": 28, "couleur": "#45B7D1", "categorie": "gros_oeuvre"},
    {"nom": "Charpente / Couverture", "duree": 21, "couleur": "#2D6BB4", "categorie": "gros_oeuvre"},
    {"nom": "Menuiseries exterieures", "duree": 14, "couleur": "#45B7D1", "categorie": "second_oeuvre"},
    {"nom": "Electricite", "duree": 21, "couleur": "#E8A838", "categorie": "second_oeuvre"},
    {"nom": "Plomberie / CVC", "duree": 21, "couleur": "#96CEB4", "categorie": "second_oeuvre"},
    {"nom": "Isolation / Platrerie", "duree": 18, "couleur": "#FFEAA7", "categorie": "second_oeuvre"},
    {"nom": "Revetements sols et murs", "duree": 14, "couleur": "#DDA0DD", "categorie": "finitions"},
    {"nom": "Peinture", "duree": 14, "couleur": "#88D8B0", "categorie": "finitions"},
    {"nom": "Amenagements exterieurs", "duree": 14, "couleur": "#FF6B6B", "categorie": "finitions"},
    {"nom": "Nettoyage / Reception", "duree": 7, "couleur": "#4ECDC4", "categorie": "finitions"},
]

def _fmt_date(val):
    if pd.isna(val) or val is None:
        return ""
    return str(val)[:10]

def _fmt_statut(val):
    return STATUT_DISPLAY.get(str(val), str(val).replace("_", " ").capitalize())


user_id = page_setup(title="Tableau de bord", icon="\U0001f4ca")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.title("\U0001f4ca Tableau de bord")

# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ
# ASSISTANT IA - Barre de commande intelligente
# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ

st.markdown("""
<style>
/* Assistant IA styling */
.ai-section {
    background: linear-gradient(135deg, #0D3B6E 0%, #1a5fb4 50%, #2563eb 100%);
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 24px;
    color: white;
    box-shadow: 0 4px 20px rgba(13, 59, 110, 0.3);
}
.ai-title {
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 4px;
    color: white;
}
.ai-subtitle {
    font-size: 0.85rem;
    color: rgba(255,255,255,0.75);
    margin-bottom: 16px;
}
.quick-action {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 0.78rem;
    color: white;
    margin: 3px;
    cursor: pointer;
    transition: all 0.2s;
}
.quick-action:hover {
    background: rgba(255,255,255,0.3);
}
.ai-response {
    background: #f0f7ff;
    border: 1px solid #bfdbfe;
    border-radius: 12px;
    padding: 16px 20px;
    margin-top: 12px;
    color: #1e293b;
}
.ai-response-header {
    font-weight: 600;
    color: #0D3B6E;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# Section Assistant IA
st.markdown("""
<div class="ai-section">
    <div class="ai-title">\U0001f916 Assistant IA ConducteurPro</div>
    <div class="ai-subtitle">Posez une question ou demandez une tache : metre, devis, analyse de plan, etude thermique...</div>
</div>
""", unsafe_allow_html=True)

# Actions rapides
st.markdown("**Actions rapides :**")
qcol1, qcol2, qcol3, qcol4 = st.columns(4)

quick_actions = {
    "\U0001f4d0 Faire un metre": "Fait un metre a partir du dernier plan depose",
    "\U0001f4b0 Creer un devis": "Cree un devis pour le chantier en cours",
    "\U0001f50d Analyser un plan": "Analyse le dernier plan depose et extrait les informations",
    "\U0001f4ca Analyser une etude": "Analyse la derniere etude deposee",
}

with qcol1:
    if st.button("\U0001f4d0 Faire un metre", width="stretch"):
        st.session_state["ai_input"] = "Fait un metre a partir du dernier plan depose"
with qcol2:
    if st.button("\U0001f4b0 Creer un devis", width="stretch"):
        st.session_state["ai_input"] = "Cree un devis pour le chantier en cours"
with qcol3:
    if st.button("\U0001f50d Analyser un plan", width="stretch"):
        st.session_state["ai_input"] = "Analyse le dernier plan depose"
with qcol4:
    if st.button("\U0001f4ca Etude / PLU", width="stretch"):
        st.session_state["ai_input"] = "Analyse la derniere etude deposee"

# Barre de saisie avec bouton micro
input_col, mic_col = st.columns([9, 1])

with input_col:
    ai_query = st.text_input(
        "\U0001f4ac Posez votre question a l'assistant IA",
        value=st.session_state.get("ai_input", ""),
        placeholder="Ex: Fait un metre du plan facade RDC, Analyse l'etude thermique, Cree un devis lot plomberie...",
        key="ai_text_input",
        label_visibility="collapsed",
    )

with mic_col:
    st.markdown("<div style='padding-top:2px;'>", unsafe_allow_html=True)
    mic_clicked = st.button("\U0001f3a4", key="mic_btn", help="Parler au lieu d'ecrire (reconnaissance vocale)")
    st.markdown("</div>", unsafe_allow_html=True)

# Script de reconnaissance vocale (Web Speech API)
if mic_clicked:
    st.markdown("""
    <div id="voice-status" style="background:#fff3cd;border:1px solid #ffc107;border-radius:8px;padding:10px;margin:8px 0;text-align:center;">
        \U0001f3a4 <strong>Ecoute en cours...</strong> Parlez maintenant.
    </div>
    <script>
    (function() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            document.getElementById('voice-status').innerHTML = '\u274c Votre navigateur ne supporte pas la reconnaissance vocale. Utilisez Chrome ou Edge.';
            return;
        }
        const recognition = new SpeechRecognition();
        recognition.lang = 'fr-FR';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('voice-status').innerHTML = '\u2705 Reconnu : <strong>' + transcript + '</strong>';
            // Inject into Streamlit input
            const inputs = window.parent.document.querySelectorAll('input[data-testid="stTextInput"]');
            if (inputs.length > 0) {
                const input = inputs[0];
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
                nativeInputValueSetter.call(input, transcript);
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        };

        recognition.onerror = function(event) {
            document.getElementById('voice-status').innerHTML = '\u274c Erreur : ' + event.error + '. Reessayez.';
        };

        recognition.onend = function() {
            setTimeout(function() {
                const el = document.getElementById('voice-status');
                if (el && el.innerHTML.includes('Ecoute')) {
                    el.innerHTML = '\u23f0 Ecoute terminee. Cliquez \U0001f3a4 pour reessayer.';
                }
            }, 2000);
        };

        recognition.start();
    })();
    </script>
    """, unsafe_allow_html=True)

# Traitement de la requete IA
if ai_query and ai_query.strip():
    query_lower = ai_query.lower().strip()

    st.markdown("---")

    # Routing intelligent vers les bonnes pages
    if any(kw in query_lower for kw in ["metre", "metrÃÂÃÂ©", "metr", "quantitatif"]):
        st.markdown("""
        <div class="ai-response">
            <div class="ai-response-header">\U0001f4d0 Metre automatique</div>
            Je vais lancer l'analyse de metre. Vous allez etre redirige vers la page <strong>Metres</strong>
            ou vous pouvez charger votre plan (PDF ou image) pour que l'IA extrait les ouvrages mesurables.
        </div>
        """, unsafe_allow_html=True)
        if st.button("\u27a1\ufe0f Aller aux Metres", type="primary"):
            st.switch_page("pages/1_Metres.py")

    elif any(kw in query_lower for kw in ["devis", "chiffrage", "chiffrer"]):
        st.markdown("""
        <div class="ai-response">
            <div class="ai-response-header">\U0001f4b0 Creation de devis</div>
            Je vais vous aider a creer un devis. Vous allez etre redirige vers la page <strong>Devis</strong>
            ou vous pouvez generer un devis professionnel PDF automatiquement.
        </div>
        """, unsafe_allow_html=True)
        if st.button("\u27a1\ufe0f Aller aux Devis", type="primary"):
            st.session_state["auto_query"] = ai_query
            st.switch_page("pages/8_Devis.py")

    elif any(kw in query_lower for kw in ["plan", "facade", "coupe", "implantation"]):
        st.markdown("""
        <div class="ai-response">
            <div class="ai-response-header">\U0001f50d Analyse de plan</div>
            Pour analyser un plan, vous pouvez utiliser le module <strong>Metres</strong> (extraction automatique des ouvrages)
            ou <strong>Etudes</strong> (analyse technique detaillee).
        </div>
        """, unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if c1.button("\U0001f4d0 Metres (extraction)", type="primary", width="stretch"):
            st.switch_page("pages/1_Metres.py")
        if c2.button("\U0001f4d6 Etudes (analyse)", width="stretch"):
            st.session_state["auto_query"] = ai_query
            st.switch_page("pages/3_Etudes.py")

    elif any(kw in query_lower for kw in ["etude", "thermique", "acoustique", "structure", "geotechnique"]):
        st.markdown("""
        <div class="ai-response">
            <div class="ai-response-header">\U0001f4d6 Analyse d'etude</div>
            Je vais vous aider a analyser votre etude. Rendez-vous sur la page <strong>Etudes</strong>
            pour charger votre document et obtenir une analyse IA detaillee.
        </div>
        """, unsafe_allow_html=True)
        if st.button("\u27a1\ufe0f Aller aux Etudes", type="primary"):
            st.session_state["auto_query"] = ai_query
            st.switch_page("pages/3_Etudes.py")

    elif any(kw in query_lower for kw in ["plu", "urbanisme", "regle", "zone"]):
        st.markdown("""
        <div class="ai-response">
            <div class="ai-response-header">\U0001f3d8\ufe0f Analyse PLU</div>
            Pour analyser un PLU, rendez-vous sur la page <strong>PLU</strong>
            ou l'IA peut extraire les regles d'urbanisme applicables a votre projet.
        </div>
        """, unsafe_allow_html=True)
        if st.button("\u27a1\ufe0f Aller au PLU", type="primary"):
            st.session_state["auto_query"] = ai_query
            st.switch_page("pages/5_PLU.py")

    elif any(kw in query_lower for kw in ["facture", "facturation", "paiement"]):
        st.markdown("""
        <div class="ai-response">
            <div class="ai-response-header">\U0001f9fe Facturation</div>
            Je vous redirige vers la page <strong>Facturation</strong> pour creer ou gerer vos factures.
        </div>
        """, unsafe_allow_html=True)
        if st.button("\u27a1\ufe0f Aller a la Facturation", type="primary"):
            st.session_state["auto_query"] = ai_query
            st.switch_page("pages/10_Facturation.py")

    elif any(kw in query_lower for kw in ["dce", "cctp", "ccap", "dpgf", "cahier"]):
        st.markdown("""
        <div class="ai-response">
            <div class="ai-response-header">\U0001f4d1 Analyse DCE</div>
            Rendez-vous sur la page <strong>DCE</strong> pour analyser vos documents de consultation.
        </div>
        """, unsafe_allow_html=True)
        if st.button("\u27a1\ufe0f Aller au DCE", type="primary"):
            st.session_state["auto_query"] = ai_query
            st.switch_page("pages/2_DCE.py")

    elif any(kw in query_lower for kw in ["planning", "gantt", "calendrier"]):
        st.markdown("""
        <div class="ai-response">
            <div class="ai-response-header">\U0001f4c5 Planning</div>
            Rendez-vous sur la page <strong>Planning</strong> pour generer ou consulter votre planning Gantt.
        </div>
        """, unsafe_allow_html=True)
        if st.button("\u27a1\ufe0f Aller au Planning", type="primary"):
            st.session_state["auto_query"] = ai_query
            st.switch_page("pages/4_Planning.py")

    elif any(kw in query_lower for kw in ["reunion", "compte-rendu", "pv reunion", "cr "]):
        st.markdown("""
        <div class="ai-response">
            <div class="ai-response-header">\U0001f4dd Reunions</div>
            Rendez-vous sur la page <strong>Reunions</strong> pour generer un compte-rendu PowerPoint automatique.
        </div>
        """, unsafe_allow_html=True)
        if st.button("\u27a1\ufe0f Aller aux Reunions", type="primary"):
            st.session_state["auto_query"] = ai_query
            st.switch_page("pages/14_Reunions.py")

    elif any(kw in query_lower for kw in ["document", "fichier", "upload", "telecharger"]):
        st.markdown("""
        <div class="ai-response">
            <div class="ai-response-header">\U0001f4c2 Documents</div>
            Rendez-vous sur la page <strong>Documents</strong> pour gerer, uploader ou telecharger vos fichiers.
        </div>
        """, unsafe_allow_html=True)
        if st.button("\u27a1\ufe0f Aller aux Documents", type="primary"):
            st.session_state["auto_query"] = ai_query
            st.switch_page("pages/11_Documents.py")

    else:
        st.markdown(f"""
        <div class="ai-response">
            <div class="ai-response-header">\U0001f916 Assistant IA</div>
            Je comprends votre demande : <em>"{ai_query}"</em><br><br>
            Voici ce que je peux faire pour vous :<br>
            \u2022 <strong>Metre</strong> : "fait un metre du plan facade"<br>
            \u2022 <strong>Devis</strong> : "cree un devis lot plomberie"<br>
            \u2022 <strong>Analyse plan</strong> : "analyse ce plan de coupe"<br>
            \u2022 <strong>Etude</strong> : "analyse l'etude thermique"<br>
            \u2022 <strong>PLU</strong> : "verifie le PLU zone UA"<br>
            \u2022 <strong>DCE</strong> : "analyse le CCTP"<br>
            \u2022 <strong>Facture</strong> : "cree une facture"<br>
            \u2022 <strong>Reunion</strong> : "prepare le compte-rendu"<br><br>
            Essayez une de ces commandes !
        </div>
        """, unsafe_allow_html=True)

    # Clear input after processing
    if "ai_input" in st.session_state:
        del st.session_state["ai_input"]

st.markdown("---")

# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ
# KPIs
# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ

stats = db.get_dashboard_stats(user_id)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("\U0001f3d7\ufe0f Chantiers", stats["nb_chantiers"], f"{stats['nb_chantiers_actifs']} actifs")
with col2:
    st.metric("\U0001f4c4 Devis", stats["nb_devis"], f"{stats['total_devis_ht']:,.0f} \u20ac HT")
with col3:
    st.metric("\U0001f9fe Factures", stats["nb_factures"], f"{stats['total_factures_ttc']:,.0f} \u20ac TTC")
with col4:
    st.metric("\U0001f4b0 Recouvrement", f"{stats['taux_recouvrement']:.0f}%", f"{stats['total_paye']:,.0f} \u20ac payes")

st.markdown("---")

col_a, col_b, col_c = st.columns(3)
with col_a:
    reste = stats.get("total_factures_ttc", 0) - stats.get("total_paye", 0)
    st.metric("\U0001f4b3 Reste a encaisser", f"{reste:,.0f} \u20ac")
with col_b:
    st.metric("\U0001f4c8 CA Total", f"{stats.get('total_paye', 0):,.0f} \u20ac")
with col_c:
    marge = stats.get("total_devis_ht", 0) - stats.get("total_factures_ttc", 0)
    st.metric("\U0001f4ca Devis non factures", f"{marge:,.0f} \u20ac")

st.markdown("---")

st.markdown("---")

# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ
# PLANNING VISUEL GENERAL - Vue Gantt de tous les chantiers
# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ

st.markdown("### \U0001f4c5 Planning general des chantiers")

import plotly.express as px
import plotly.graph_objects as go_plan
from datetime import datetime, timedelta

all_phases = db.get_all_phases_user(user_id)
chantiers_list = stats.get("chantiers", [])

# Palette de couleurs pour les chantiers
CHANTIER_COLORS = [
    "#1B4F8A", "#E67E22", "#2ECC71", "#9B59B6", "#E74C3C",
    "#1ABC9C", "#F39C12", "#3498DB", "#D35400", "#27AE60",
    "#8E44AD", "#C0392B", "#16A085", "#2980B9", "#F1C40F",
]

gantt_data = []
chantier_ids_map = {}  # nom -> id
chantier_phases_map = {}  # nom -> list of phases

# 1) Ajouter les phases existantes
if all_phases:
    for p in all_phases:
        start = p.get("date_debut")
        end = p.get("date_fin")
        if start and end:
            ch_info = p.get("chantiers", {})
            ch_nom = ch_info.get("nom", "Chantier") if ch_info else p.get("chantier_nom", "Chantier")
            gantt_data.append({
                "Chantier": ch_nom,
                "Phase": p.get("nom", "Phase"),
                "Debut": str(start), "Fin": str(end),
                "Statut": p.get("statut", "a_faire"),
                "Avancement": p.get("avancement", 0),
            })
            if ch_nom not in chantier_phases_map:
                chantier_phases_map[ch_nom] = []
            chantier_phases_map[ch_nom].append(p)

# 2) Ajouter les chantiers avec dates mais sans phases
for ch in chantiers_list:
    ch_nom = ch.get("nom", "Sans nom")
    chantier_ids_map[ch_nom] = ch.get("id")
    if ch_nom not in chantier_phases_map and ch.get("date_debut") and ch.get("date_fin"):
        gantt_data.append({
            "Chantier": ch_nom, "Phase": "Chantier planifie",
            "Debut": str(ch["date_debut"]), "Fin": str(ch["date_fin"]),
            "Statut": "planifie", "Avancement": 0,
        })

planning_container = st.container()
with planning_container:
    if gantt_data:
        import pandas as pd
        df_gantt = pd.DataFrame(gantt_data)

        # Attribuer une couleur unique par chantier
        unique_chantiers = list(df_gantt["Chantier"].unique())
        chantier_color_map = {name: CHANTIER_COLORS[i % len(CHANTIER_COLORS)] for i, name in enumerate(unique_chantiers)}

        fig_plan = px.timeline(
            df_gantt, x_start="Debut", x_end="Fin", y="Chantier",
            color="Chantier",
            hover_data=["Phase", "Statut", "Avancement"],
            color_discrete_map=chantier_color_map,
            title=""
        )
        fig_plan.update_yaxes(autorange="reversed")
        fig_plan.update_layout(height=max(250, len(unique_chantiers) * 80), margin=dict(l=0, r=0, t=10, b=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.3))
        st.plotly_chart(fig_plan, key="planning_gantt_main", width="stretch")

        # Detail par chantier cliquable
        st.markdown("#### \U0001f50d Detail par chantier")
        for idx_ch, ch_nom in enumerate(unique_chantiers):
            color_dot = chantier_color_map.get(ch_nom, "#1B4F8A")
            phases_ch = chantier_phases_map.get(ch_nom, [])
            ch_id = chantier_ids_map.get(ch_nom)
            nb_phases = len(phases_ch)
            label = f"\U0001f3d7\ufe0f {ch_nom} ÃÂ¢ÃÂÃÂ {nb_phases} phase(s)" if nb_phases > 0 else f"\U0001f3d7\ufe0f {ch_nom} ÃÂ¢ÃÂÃÂ Aucune phase"

            with st.expander(label, expanded=False):
                if phases_ch:
                    for ph in phases_ch:
                        col_a, col_b, col_c = st.columns([3, 2, 1])
                        col_a.markdown(f"**{ph.get('nom', 'Phase')}**")
                        col_b.caption(f"{ph.get('date_debut', '?')} ÃÂ¢ÃÂÃÂ {ph.get('date_fin', '?')}")
                        statut = ph.get("statut", "a_faire")
                        if statut == "termine":
                            col_c.success("Termine")
                        elif statut == "en_cours":
                            col_c.info("En cours")
                        elif statut == "en_retard":
                            col_c.error("En retard")
                        else:
                            col_c.warning("A faire")
                else:
                    st.warning("Aucune phase detaillee pour ce chantier.")
                    if ch_id:
                        if st.button(f"\U0001f916 Generer le planning IA pour {ch_nom}", key=f"gen_plan_{idx_ch}"):
                            _date_debut = ch.get("date_debut")
                            if _date_debut and isinstance(_date_debut, str):
                                try:
                                    _start = datetime.strptime(_date_debut, "%Y-%m-%d").date()
                                except Exception:
                                    _start = date.today()
                            elif _date_debut and hasattr(_date_debut, "year"):
                                _start = _date_debut
                            else:
                                _start = date.today()

                            _phases_to_save = []
                            _current = _start
                            for _idx_p, _phase in enumerate(PHASES_BTP):
                                _d_debut = _current
                                _d_fin = _d_debut + timedelta(days=_phase["duree"])
                                _phases_to_save.append({
                                    "nom": _phase["nom"],
                                    "categorie": _phase.get("categorie", "personnalisee"),
                                    "date_debut": _d_debut.isoformat(),
                                    "date_fin": _d_fin.isoformat(),
                                    "duree_jours": _phase["duree"],
                                    "statut": "a_faire",
                                    "progression": 0,
                                    "ordre": _idx_p + 1,
                                    "couleur": _phase.get("couleur", "#1B4F8A"),
                                })
                                _current = _d_fin - timedelta(days=min(2, _phase["duree"] - 1))

                            _ok = db.save_phases_batch(user_id, ch_id, _phases_to_save)
                            if _ok:
                                db.update_chantier(ch_id, {
                                    "date_debut": _phases_to_save[0]["date_debut"],
                                    "date_fin": _phases_to_save[-1]["date_fin"],
                                })
                                st.success(f"Planning genere avec {len(_phases_to_save)} phases pour {ch_nom} !")
                                st.rerun()
                            else:
                                st.error("Erreur lors de la generation du planning.")
    else:
        today = datetime.now()
        start_month = today.replace(day=1)
        end_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        fig_plan = go_plan.Figure()
        fig_plan.add_shape(type="line", x0=str(today.date()), x1=str(today.date()), y0=-0.5, y1=0.5, line=dict(color="red", width=2, dash="dash"))
        fig_plan.add_annotation(x=str(today.date()), y=0.3, text="Aujourd'hui", showarrow=False, font=dict(color="red", size=10))
        fig_plan.update_layout(xaxis=dict(type="date", range=[str(start_month.date()), str(end_month.date())], title="", dtick="D1", tickformat="%d %b"), yaxis=dict(visible=False), height=200, margin=dict(l=0, r=0, t=10, b=40), plot_bgcolor="white")
        fig_plan.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#f0f0f0")
        st.plotly_chart(fig_plan, key="planning_gantt_main", width="stretch")
        st.info("\U0001f4c5 Aucun chantier planifie. Creez un chantier avec des dates ou generez un planning IA.")

    # Toujours afficher le bouton de generation IA
    if chantiers_list:
        col_plan1, col_plan2 = st.columns([3, 1])
        with col_plan1:
            chantier_noms = {c.get("nom", "Sans nom"): c for c in chantiers_list}
            selected_chantier = st.selectbox("Generer un planning IA pour :", list(chantier_noms.keys()), key="planning_gen_select")
        with col_plan2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("\U0001f916 Generer planning IA", type="primary", key="btn_gen_planning"):
                ch = chantier_noms[selected_chantier]
                ch_id_gen = ch.get("id")
                _date_debut = ch.get("date_debut")
                if _date_debut and isinstance(_date_debut, str):
                    try:
                        _start = datetime.strptime(_date_debut, "%Y-%m-%d").date()
                    except Exception:
                        _start = date.today()
                elif _date_debut and hasattr(_date_debut, "year"):
                    _start = _date_debut
                else:
                    _start = date.today()

                _phases_to_save = []
                _current = _start
                for _idx_p, _phase in enumerate(PHASES_BTP):
                    _d_debut = _current
                    _d_fin = _d_debut + timedelta(days=_phase["duree"])
                    _phases_to_save.append({
                        "nom": _phase["nom"],
                        "categorie": _phase.get("categorie", "personnalisee"),
                        "date_debut": _d_debut.isoformat(),
                        "date_fin": _d_fin.isoformat(),
                        "duree_jours": _phase["duree"],
                        "statut": "a_faire",
                        "progression": 0,
                        "ordre": _idx_p + 1,
                        "couleur": _phase.get("couleur", "#1B4F8A"),
                    })
                    _current = _d_fin - timedelta(days=min(2, _phase["duree"] - 1))

                _ok = db.save_phases_batch(user_id, ch_id_gen, _phases_to_save)
                if _ok:
                    db.update_chantier(ch_id_gen, {
                        "date_debut": _phases_to_save[0]["date_debut"],
                        "date_fin": _phases_to_save[-1]["date_fin"],
                    })
                    st.success(f"Planning genere avec {len(_phases_to_save)} phases pour {selected_chantier} !")
                    st.rerun()
                else:
                    st.error("Erreur lors de la generation du planning.")

# Details par onglet
# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ

tab1, tab2, tab3 = st.tabs(["\U0001f3d7\ufe0f Chantiers", "\U0001f4c4 Devis", "\U0001f9fe Factures"])

with tab1:
    chantiers = stats.get("chantiers", [])
    if chantiers:
        statuts = list(set(c.get("statut", "") for c in chantiers))
        statuts_display = ["Tous"] + [_fmt_statut(s) for s in statuts]
        filtre = st.selectbox("Filtrer par statut", statuts_display, key="filtre_chantier")

        df = pd.DataFrame(chantiers)
        if filtre != "Tous":
            for s in statuts:
                if _fmt_statut(s) == filtre:
                    df = df[df["statut"] == s]
                    break

        cols_display = [c for c in ["nom", "client_nom", "statut", "adresse", "budget_ht", "avancement_pct", "created_at"] if c in df.columns]
        df_display = df[cols_display].copy() if cols_display else df.copy()

        if "statut" in df_display.columns:
            df_display["statut"] = df_display["statut"].apply(_fmt_statut)
        if "created_at" in df_display.columns:
            df_display["created_at"] = df_display["created_at"].apply(_fmt_date)
        if "budget_ht" in df_display.columns:
            df_display["budget_ht"] = df_display["budget_ht"].apply(lambda x: f"{float(x or 0):,.0f} \u20ac" if x else "\u2014")
        if "avancement_pct" in df_display.columns:
            df_display["avancement_pct"] = df_display["avancement_pct"].apply(lambda x: f"{float(x or 0):.0f}%" if x else "\u2014")

        rename = {"nom": "Nom", "client_nom": "Client", "statut": "Statut", "adresse": "Adresse", "budget_ht": "Budget HT", "avancement_pct": "Avancement", "created_at": "Cree le"}
        df_display.columns = [rename.get(c, c) for c in df_display.columns]
        st.dataframe(df_display, width="stretch", hide_index=True)

        if "statut" in df.columns:
            df["Statut"] = df["statut"].apply(_fmt_statut)
            fig = px.pie(df, names="Statut", title="Repartition par statut", color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig, width="stretch")
    else:
        st.info("Aucun chantier. Creez votre premier chantier ci-dessous.")

    with st.expander("\u2795 Nouveau chantier"):
        with st.form("new_chantier"):
            c1, c2 = st.columns(2)
            with c1:
                nom = st.text_input("Nom du chantier *")
                client = st.text_input("Client")
                adresse = st.text_input("Adresse")
            with c2:
                budget = st.number_input("Budget HT (\u20ac)", min_value=0.0, step=1000.0, value=0.0)
                metier = st.selectbox("Metier", ["Gros oeuvre", "Second oeuvre", "Genie civil", "Renovation", "Extension", "Neuf", "Autre"])
                responsable = st.text_input("Responsable")
            notes = st.text_area("Notes", height=80)
            c3, c4 = st.columns(2)
            with c3:
                date_debut = st.date_input("Date de debut du chantier", value=None, key="new_ch_date_debut")
            with c4:
                date_fin = st.date_input("Date de fin prevue", value=None, key="new_ch_date_fin")
            submitted = st.form_submit_button("Creer le chantier", type="primary")
            if submitted and nom:
                data = {"nom": nom, "client_nom": client, "adresse": adresse, "statut": "en_cours", "budget_ht": budget, "metier": metier, "responsable": responsable, "notes": notes}
                if date_debut:
                    data["date_debut"] = str(date_debut)
                if date_fin:
                    data["date_fin"] = str(date_fin)
                result = db.create_chantier(user_id, data)
                if result:
                    st.success(f"Chantier '{nom}' cree !")
                    st.rerun()
                else:
                    st.error("Erreur lors de la creation.")

with tab2:
    devis = stats.get("devis", [])
    if devis:
        df = pd.DataFrame(devis)
        cols_display = [c for c in ["numero", "objet", "client_nom", "montant_ht", "statut", "created_at"] if c in df.columns]
        df_display = df[cols_display].copy() if cols_display else df.copy()
        if "statut" in df_display.columns:
            df_display["statut"] = df_display["statut"].apply(_fmt_statut)
        if "created_at" in df_display.columns:
            df_display["created_at"] = df_display["created_at"].apply(_fmt_date)
        if "montant_ht" in df_display.columns:
            df_display["montant_ht"] = df_display["montant_ht"].apply(lambda x: f"{float(x or 0):,.2f} \u20ac")
        rename = {"numero": "N\u00b0", "objet": "Objet", "client_nom": "Client", "montant_ht": "Montant HT", "statut": "Statut", "created_at": "Cree le"}
        df_display.columns = [rename.get(c, c) for c in df_display.columns]
        st.dataframe(df_display, width="stretch", hide_index=True)
    else:
        st.info("Aucun devis. Creez-en un depuis la page Devis.")

with tab3:
    factures = stats.get("factures", [])
    if factures:
        total_ttc = sum(float(f.get("montant_ttc", 0) or 0) for f in factures)
        payees = sum(float(f.get("montant_ttc", 0) or 0) for f in factures if f.get("statut") in ("payee", "payee"))
        fc1, fc2, fc3 = st.columns(3)
        fc1.metric("Total facture", f"{total_ttc:,.0f} \u20ac")
        fc2.metric("Paye", f"{payees:,.0f} \u20ac")
        fc3.metric("Impaye", f"{total_ttc - payees:,.0f} \u20ac")

        df = pd.DataFrame(factures)
        cols_display = [c for c in ["numero", "client_nom", "objet", "montant_ttc", "statut", "date_facture", "date_echeance"] if c in df.columns]
        df_display = df[cols_display].copy() if cols_display else df.copy()
        if "statut" in df_display.columns:
            df_display["statut"] = df_display["statut"].apply(_fmt_statut)
        for dc in ["date_facture", "date_echeance"]:
            if dc in df_display.columns:
                df_display[dc] = df_display[dc].apply(_fmt_date)
        if "montant_ttc" in df_display.columns:
            df_display["montant_ttc"] = df_display["montant_ttc"].apply(lambda x: f"{float(x or 0):,.2f} \u20ac")
        rename = {"numero": "N\u00b0", "client_nom": "Client", "objet": "Objet", "montant_ttc": "Montant TTC", "statut": "Statut", "date_facture": "Date", "date_echeance": "Echeance"}
        df_display.columns = [rename.get(c, c) for c in df_display.columns]
        st.dataframe(df_display, width="stretch", hide_index=True)
    else:
        st.info("Aucune facture. Creez-en une depuis la page Facturation.")
