"""
supabase_client.py — Initialisation et gestion du client Supabase.
Fournit un singleton pour la connexion DB + Storage + Auth.
"""
import streamlit as st
from supabase import create_client, Client

# ─── Singleton Supabase ───────────────────────────────────────────────────────
@st.cache_resource
def get_supabase_client() -> Client:
    """
    Retourne un client Supabase initialisé à partir des secrets Streamlit.
    Utilise @st.cache_resource pour ne créer qu'une seule instance.
    """
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_ANON_KEY", "")
    if not url or not key:
        return None
    return create_client(url, key)


def get_supabase_admin() -> Client:
    """
    Client Supabase avec clé service (pour les opérations admin).
    À utiliser uniquement côté serveur pour les opérations sans RLS.
    """
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        return None
    return create_client(url, key)


def init_supabase_session():
    """
    Initialise les variables de session Supabase.
    Appelé au démarrage de chaque page.
    """
    defaults = {
        "authenticated": False,
        "user_id": None,
        "user_email": "",
        "user_name": "",
        "user_plan": "free",
        "user_profile": None,
        "supabase_access_token": None,
        "supabase_refresh_token": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def check_auth():
    """
    Vérifie si l'utilisateur est authentifié.
    Retourne True si connecté, False sinon.
    """
    return st.session_state.get("authenticated", False) and st.session_state.get("user_id") is not None
