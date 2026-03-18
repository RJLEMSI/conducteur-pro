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

# --- CSS Global ---
from utils import GLOBAL_CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
try:
    from lib.responsive import inject_responsive_css, inject_professional_theme
    inject_responsive_css()
    inject_professional_theme()
except Exception:
    pass

# --- Onboarding ---
try:
    from lib.onboarding import should_show_onboarding, render_onboarding
    if is_authenticated() and should_show_onboarding():
        render_onboarding()
except Exception:
    pass

# --- Navigation ---
if is_authenticated():
    pages = {
        "": [
            st.Page("pages/0_Tableau_de_bord.py", title="Tableau de bord", icon="🏠", default=True),
        ],
        "🏗️ Chantiers & IA": [
            st.Page("pages/1_Metres.py", title="Métrés", icon="📐"),
            st.Page("pages/2_DCE.py", title="DCE", icon="📑"),
            st.Page("pages/3_Etudes.py", title="Études", icon="📖"),
            st.Page("pages/4_Planning.py", title="Planning", icon="📅"),
            st.Page("pages/5_PLU.py", title="PLU", icon="🗺️"),
            st.Page("pages/6_Synthese.py", title="Synthèse", icon="📊"),
        ],
        "💼 Commercial": [
            st.Page("pages/8_Devis.py", title="Devis", icon="💰"),
            st.Page("pages/10_Facturation.py", title="Facturation", icon="🧾"),
            st.Page("pages/11_Documents.py", title="Documents", icon="📁"),
        ],
        "🤖 ERP": [
            st.Page("pages/15_Achats.py", title="Achats", icon="🛒"),
            st.Page("pages/16_Sous_Traitants.py", title="Sous-Traitants", icon="👷"),
            st.Page("pages/17_Pointage.py", title="Pointage", icon="⏰"),
            st.Page("pages/18_Stocks.py", title="Stocks", icon="📦"),
            st.Page("pages/19_CRM.py", title="CRM", icon="💼"),
            st.Page("pages/20_Suivi_Financier.py", title="Suivi Financier", icon="📈"),
            st.Page("pages/21_Agent_ERP.py", title="Agent ERP", icon="🎙️"),
        ],
        "⚙️ Paramètres": [
            st.Page("pages/14_Reunions.py", title="Réunions", icon="📋"),
            st.Page("pages/12_Legal.py", title="Légal", icon="⚖️"),
            st.Page("pages/9_Abonnement.py", title="Abonnement", icon="⭐"),
            st.Page("pages/13_Mon_Compte.py", title="Mon Compte", icon="👤"),
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
