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

# --- CSS Global ---
from utils import GLOBAL_CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# --- Navigation dynamique selon authentification ---
if is_authenticated():
    pages = {
        "General": [
            st.Page("pages/0_Tableau_de_bord.py", title="Tableau de bord", icon="📊", default=True),
            st.Page("pages/01_Import_Donnees.py", title="Import Donnees", icon="📥"),
        ],
        "Analyses": [
            st.Page("pages/1_Metres.py", title="Metres", icon="📐"),
            st.Page("pages/2_DCE.py", title="DCE", icon="📋"),
            st.Page("pages/3_Etudes.py", title="Etudes", icon="🔬"),
            st.Page("pages/4_Planning.py", title="Planning", icon="📅"),
            st.Page("pages/5_PLU.py", title="PLU", icon="🏛️"),
            st.Page("pages/6_Synthese.py", title="Synthese", icon="📝"),
        ],
        "Business": [
            st.Page("pages/8_Devis.py", title="Devis", icon="💰"),
            st.Page("pages/10_Facturation.py", title="Facturation", icon="🧾"),
            st.Page("pages/11_Documents.py", title="Documents", icon="📁"),
        ],
        "Compte": [
            st.Page("pages/9_Abonnement.py", title="Abonnement", icon="⭐"),
            st.Page("pages/12_Legal.py", title="Mentions legales", icon="⚖️"),
            st.Page("pages/00_Connexion.py", title="Mon compte", icon="👤"),
        ],
    }
else:
    pages = {
        "": [
            st.Page("pages/00_Connexion.py", title="Connexion", icon="🔐", default=True),
            st.Page("pages/12_Legal.py", title="Mentions legales", icon="⚖️"),
        ],
    }

pg = st.navigation(pages)
pg.run()
