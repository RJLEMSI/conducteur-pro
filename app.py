import streamlit as st
import os
import json

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

# --- DEBUG temporaire ---
_log_file = "/tmp/conducteurpro_session_debug.log"
_sess_file = "/tmp/conducteurpro_sessions.json"
_dbg = "auth=" + str(is_authenticated())
_dbg += " uid=" + str(bool(st.session_state.get("user_id")))
_dbg += " at=" + str(bool(st.session_state.get("supabase_access_token")))
_dbg += " rt=" + str(bool(st.session_state.get("supabase_refresh_token")))
_dbg += " log=" + str(os.path.exists(_log_file))
_dbg += " sess=" + str(os.path.exists(_sess_file))
if os.path.exists(_sess_file):
    _dbg += " sz=" + str(os.path.getsize(_sess_file))
st.caption(_dbg)
if os.path.exists(_log_file):
    try:
        with open(_log_file, "r") as _f:
            _log_lines = _f.readlines()[-15:]
            st.code("".join(_log_lines), language="text")
    except Exception:
        pass
# --- END DEBUG ---

from utils import GLOBAL_CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

try:
    from lib.responsive import inject_responsive_css, inject_professional_theme
    inject_responsive_css()
    inject_professional_theme()
except Exception:
    pass

try:
    from lib.onboarding import should_show_onboarding, render_onboarding
    if is_authenticated() and should_show_onboarding():
        render_onboarding()
except Exception:
    pass

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
