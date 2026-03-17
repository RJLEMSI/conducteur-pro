import streamlit as st

# --- Configuration de la page (AVANT st.navigation) ---
st.set_page_config(
    page_title="ConducteurPro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Initialisation Supabase ---
from lib.supabase_client import init_supabase_session, is_authenticated, save_persistent_session

init_supabase_session()

# Sauvegarder la session persistante si authentifie
# (assure que le fichier est toujours a jour apres chaque rerun)
if is_authenticated():
    _uid = st.session_state.get("user_id", "")
    _at = st.session_state.get("supabase_access_token", "")
    _rt = st.session_state.get("supabase_refresh_token", "")
    if _uid and _rt:
        save_persistent_session(
            user_id=_uid,
            email=st.session_state.get("user_email", ""),
            access_token=_at,
            refresh_token=_rt,
            plan=st.session_state.get("user_plan", "free"),
        )

# --- CSS Global + Responsive ---
from utils import GLOBAL_CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

try:
    from lib.responsive import inject_responsive_css, inject_professional_theme
    inject_responsive_css()
    inject_professional_theme()
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
        "General": [
            st.Page("pages/0_Tableau_de_bord.py", title="Tableau de bord", icon="\U0001f4ca", default=True),
        ],
        "Analyses IA": [
            st.Page("pages/1_Metres.py", title="Metres", icon="\U0001f4d0"),
            st.Page("pages/2_DCE.py", title="DCE", icon="\U0001f4d1"),
            st.Page("pages/3_Etudes.py", title="Etudes", icon="\U0001f4d6"),
            st.Page("pages/4_Planning.py", title="Planning", icon="\U0001f4c5"),
            st.Page("pages/5_PLU.py", title="PLU", icon="\U0001f3d8\ufe0f"),
            st.Page("pages/6_Synthese.py", title="Synthese", icon="\U0001f4cb"),
        ],
        "Documents & Finance": [
            st.Page("pages/8_Devis.py", title="Devis", icon="\U0001f4b0"),
            st.Page("pages/10_Facturation.py", title="Facturation", icon="\U0001f9fe"),
            st.Page("pages/11_Documents.py", title="Documents", icon="\U0001f4c2"),
            st.Page("pages/14_Reunions.py", title="Reunions", icon="\U0001f4dd"),
        ],
        "ERP": [
            st.Page("pages/15_Achats.py", title="Achats", icon="U0001f6d2"),
            st.Page("pages/16_Sous_Traitants.py", title="Sous-Traitants", icon="U0001f477"),
            st.Page("pages/17_Pointage.py", title="Pointage", icon="⏰"),
            st.Page("pages/18_Stocks.py", title="Stocks", icon="U0001f4e6"),
            st.Page("pages/19_CRM.py", title="CRM", icon="U0001f4bc"),
            st.Page("pages/20_Suivi_Financier.py", title="Suivi Financier", icon="U0001f4b9"),
        ],
        "Compte": [
            st.Page("pages/9_Abonnement.py", title="Abonnement", icon="\u2b50"),
            st.Page("pages/13_Mon_Compte.py", title="Mon Compte", icon="\U0001f464"),
        ],
    }
else:
    pages = {
        "Bienvenue": [
            st.Page("pages/00_Connexion.py", title="Connexion", default=True),
        ],
    }

pg = st.navigation(pages)
pg.run()
