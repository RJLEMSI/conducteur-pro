import streamlit as st

# --- Configuration de la page (AVANT st.navigation) ---
st.set_page_config(
    page_title="ConducteurPro",
    page_icon="ðï¸",
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

# --- Bandeau cookies RGPD supprimé (inutile) ---

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
        "GÃ©nÃ©ral": [
            st.Page("pages/0_Tableau_de_bord.py", title="Tableau de bord", icon="ð", default=True),
            st.Page("pages/01_Import_Donnees.py", title="Import DonnÃ©es", icon="ð¥"),
        ],
        "Analyses": [
            st.Page("pages/1_Metres.py", title="MÃ©trÃ©s", icon="ð"),
            st.Page("pages/2_DCE.py", title="DCE", icon="ð"),
            st.Page("pages/3_Etudes.py", title="Ãtudes", icon="ð¬"),
            st.Page("pages/4_Planning.py", title="Planning", icon="ð"),
            st.Page("pages/5_PLU.py", title="PLU", icon="ðï¸"),
            st.Page("pages/6_Synthese.py", title="SynthÃ¨se", icon="ð"),
        ],
        "Documents": [
            st.Page("pages/8_Devis.py", title="Devis", icon="ð"),
            st.Page("pages/10_Facturation.py", title="Facturation", icon="ð°"),
            st.Page("pages/11_Documents.py", title="Documents", icon="ð"),
        ],
        "Compte": [
            st.Page("pages/9_Abonnement.py", title="Abonnement", icon="ð³"),
            st.Page("pages/13_Mon_Compte.py", title="Mon Compte", icon="ð¤"),
            st.Page("pages/12_Legal.py", title="Mentions lÃ©gales", icon="âï¸"),
        ],
    }
else:
    pages = {
        "Bienvenue": [
            st.Page("pages/00_Connexion.py", title="Connexion", icon="ð", default=True),
            st.Page("pages/12_Legal.py", title="Mentions lÃ©gales", icon="âï¸"),
        ],
    }

pg = st.navigation(pages)
pg.run()
