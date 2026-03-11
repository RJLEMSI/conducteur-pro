import streamlit as st

# --- Configuration de la page (AVANT st.navigation) ---
st.set_page_config(
    page_title="ConducteurPro",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Initialisation Supabase ---
from lib.supabase_client import init_supabase_session, is_authenticated
init_supabase_session()

# --- CSS Global + Responsive ---
from utils import GLOBAL_CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

try:
    from lib.responsive import inject_responsive_css, inject_professional_theme
    inject_responsive_css()
    inject_professional_theme()
except Exception:
    pass

# --- Bandeau cookies RGPD ---
try:
    from lib.rgpd import render_cookie_banner
    render_cookie_banner()
except Exception:
    pass

# --- Onboarding nouveaux utilisateurs ---
try:
    from lib.onboarding import should_show_onboarding, render_onboarding
    if is_authenticated() and should_show_onboarding():
        render_onboarding()
except Exception:
    pass

# --- Navigation dynamique selon authentification ---
if is_authenticated():
    pages = {
        "Général": [
            st.Page("pages/0_Tableau_de_bord.py", title="Tableau de bord", icon="📊", default=True),
            st.Page("pages/01_Import_Donnees.py", title="Import Données", icon="📥"),
        ],
        "Analyses": [
            st.Page("pages/1_Metres.py", title="Métrés", icon="📐"),
            st.Page("pages/2_DCE.py", title="DCE", icon="📑"),
            st.Page("pages/3_Etudes.py", title="Études", icon="🔬"),
            st.Page("pages/4_Planning.py", title="Planning", icon="📅"),
            st.Page("pages/5_PLU.py", title="PLU", icon="🏗️"),
            st.Page("pages/6_Synthese.py", title="Synthèse", icon="📊"),
        ],
        "Documents": [
            st.Page("pages/8_Devis.py", title="Devis", icon="📋"),
            st.Page("pages/10_Facturation.py", title="Facturation", icon="💰"),
            st.Page("pages/11_Documents.py", title="Documents", icon="📂"),
        ],
        "Compte": [
            st.Page("pages/9_Abonnement.py", title="Abonnement", icon="💳"),
            st.Page("pages/13_Mon_Compte.py", title="Mon Compte", icon="👤"),
            st.Page("pages/12_Legal.py", title="Mentions légales", icon="⚖️"),
        ],
    }
else:
    pages = {
        "Bienvenue": [
            st.Page("pages/00_Connexion.py", title="Connexion", icon="🔐", default=True),
            st.Page("pages/12_Legal.py", title="Mentions légales", icon="⚖️"),
        ],
    }

pg = st.navigation(pages)
pg.run()
