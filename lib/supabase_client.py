"""
ConducteurPro — Client Supabase (singleton).
Initialise la connexion Supabase, gère la session utilisateur,
fournit les helpers d'authentification.
"""
import streamlit as st
from supabase import create_client, Client


def get_supabase_client() -> Client:
    """Retourne le client Supabase (singleton via session_state)."""
    if "supabase_client" not in st.session_state:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if not url or not key:
            st.error("Configuration Supabase manquante. Vérifiez SUPABASE_URL et SUPABASE_KEY dans les secrets.")
            st.stop()
        st.session_state.supabase_client = create_client(url, key)
    return st.session_state.supabase_client


def get_supabase_admin() -> Client:
    """Retourne un client Supabase avec la clé service_role (admin, bypass RLS).
    À utiliser uniquement pour les opérations côté serveur.
    """
    if "supabase_admin" not in st.session_state:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            return get_supabase_client()  # fallback to anon client
        st.session_state.supabase_admin = create_client(url, key)
    return st.session_state.supabase_admin


def init_supabase_session():
    """Initialise la session Supabase et vérifie si un utilisateur est connecté.
    Restaure la session depuis les query params (callback OAuth) ou depuis le cache.
    """
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.session_state.user_plan = "free"
        st.session_state.authenticated = False
    
    # Tenter de restaurer la session depuis le token en cache
    if not st.session_state.authenticated and "access_token" in st.session_state:
        try:
            client = get_supabase_client()
            session = client.auth.get_session()
            if session and session.user:
                st.session_state.user_id = session.user.id
                st.session_state.user_email = session.user.email
                st.session_state.authenticated = True
        except Exception:
            pass


def is_authenticated() -> bool:
    """Vérifie si l'utilisateur est actuellement authentifié."""
    return st.session_state.get("authenticated", False)


def get_user_id() -> str | None:
    """Retourne l'ID de l'utilisateur connecté ou None."""
    return st.session_state.get("user_id", None)


def get_user_email() -> str | None:
    """Retourne l'email de l'utilisateur connecté ou None."""
    return st.session_state.get("user_email", None)


def check_auth():
    """Vérifie l'authentification et redirige vers la page de connexion si non connecté.
    Usage: check_auth() au début de chaque page protégée.
    """
    init_supabase_session()
    if not is_authenticated():
        st.warning("Vous devez être connecté pour accéder à cette page.")
        st.switch_page("pages/00_Connexion.py")
        st.stop()
