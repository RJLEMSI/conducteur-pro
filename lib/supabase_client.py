"""
ConducteurPro - Client Supabase (singleton).
Initialise la connexion Supabase, gere la session utilisateur,
fournit les helpers d'authentification.
Inclut un store persistant fichier pour survivre aux rechargements de page.
"""
import streamlit as st
import json
import os
from datetime import datetime
from supabase import create_client, Client


# ---- Store persistant fichier (survit aux refresh ET restart service) ----
SESSION_FILE = "/tmp/conducteurpro_sessions.json"


def _load_sessions():
    """Charge les sessions depuis le fichier."""
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_sessions(data):
    """Sauvegarde les sessions dans le fichier."""
    try:
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        with open(SESSION_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def save_persistent_session(user_id, email, access_token, refresh_token, plan="free"):
    """Sauvegarde la session dans le fichier persistant."""
    if not user_id or not refresh_token:
        return
    sessions = _load_sessions()
    sessions[user_id] = {
        "email": email,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "plan": plan,
        "saved_at": datetime.utcnow().isoformat(),
    }
    _save_sessions(sessions)


def restore_persistent_session():
    """Tente de restaurer une session depuis le fichier.
    Essaie chaque session sauvegardee jusqu'a en trouver une valide.
    Utilise set_session() (plus fiable) avec fallback sur refresh_session().
    """
    sessions = _load_sessions()
    if not sessions:
        return False

    client = get_supabase_client()

    for uid, data in list(sessions.items()):
        rt = data.get("refresh_token", "")
        at = data.get("access_token", "")
        if not rt:
            continue

        # Methode 1: set_session (la plus fiable, concue pour restaurer des tokens stockes)
        try:
            result = client.auth.set_session(at, rt)
            if result and result.user:
                _apply_restored_session(result, data, sessions, uid)
                return True
        except Exception:
            pass

        # Methode 2: refresh_session avec le token
        try:
            result = client.auth.refresh_session(rt)
            if result and result.user:
                _apply_restored_session(result, data, sessions, uid)
                return True
        except Exception:
            pass

        # Les deux methodes ont echoue, supprimer cette session
        sessions.pop(uid, None)
        _save_sessions(sessions)

    return False


def _apply_restored_session(result, data, sessions, uid):
    """Applique une session restauree a session_state et met a jour le fichier."""
    st.session_state.authenticated = True
    st.session_state.user_id = result.user.id
    st.session_state.user_email = result.user.email or data.get("email", "")
    st.session_state.supabase_access_token = result.session.access_token
    st.session_state.supabase_refresh_token = result.session.refresh_token
    st.session_state.user_plan = data.get("plan", "free")

    # Mettre a jour les tokens dans le fichier
    sessions[uid]["access_token"] = result.session.access_token
    sessions[uid]["refresh_token"] = result.session.refresh_token
    sessions[uid]["saved_at"] = datetime.utcnow().isoformat()
    _save_sessions(sessions)


def clear_persistent_session():
    """Supprime la session persistante de l'utilisateur courant."""
    uid = st.session_state.get("user_id")
    if uid:
        sessions = _load_sessions()
        sessions.pop(uid, None)
        _save_sessions(sessions)


# ---- Client Supabase ----

def get_supabase_client() -> Client:
    """Retourne le client Supabase (singleton via session_state)."""
    if "supabase_client" not in st.session_state:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if not url or not key:
            st.error("Configuration Supabase manquante.")
            st.stop()
        st.session_state.supabase_client = create_client(url, key)
    return st.session_state.supabase_client


def get_supabase_admin() -> Client:
    """Retourne le client Supabase avec le service role key (admin)."""
    if "supabase_admin" not in st.session_state:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not key:
            return get_supabase_client()
        st.session_state.supabase_admin = create_client(url, key)
    return st.session_state.supabase_admin


def init_supabase_session():
    """Initialise la session Supabase.
    Tente de restaurer depuis le fichier persistant si session_state est vide.
    """
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.session_state.user_plan = "free"
        st.session_state.authenticated = False

    # Deja authentifie, rien a faire
    if st.session_state.authenticated:
        return

    # Tenter la restauration depuis le fichier persistant
    if restore_persistent_session():
        return

    # Tenter depuis le client Supabase (session en memoire du process)
    try:
        client = get_supabase_client()
        sess = client.auth.get_session()
        if sess and sess.user:
            st.session_state.user_id = sess.user.id
            st.session_state.user_email = sess.user.email
            st.session_state.authenticated = True
            # Sauvegarder aussi les tokens pour la persistance
            if hasattr(sess, 'access_token') and hasattr(sess, 'refresh_token'):
                st.session_state.supabase_access_token = sess.access_token
                st.session_state.supabase_refresh_token = sess.refresh_token
            return
    except Exception:
        pass


def is_authenticated() -> bool:
    """Verifie si l'utilisateur est actuellement authentifie."""
    return st.session_state.get("authenticated", False)


def get_user_id() -> str | None:
    """Retourne l'ID de l'utilisateur connecte ou None."""
    return st.session_state.get("user_id", None)


def get_user_email() -> str | None:
    """Retourne l'email de l'utilisateur connecte ou None."""
    return st.session_state.get("user_email", None)


def check_auth():
    """Verifie l'authentification et redirige vers la page de connexion si non connecte."""
    init_supabase_session()
    if not is_authenticated():
        st.warning("Vous devez etre connecte pour acceder a cette page.")
        st.switch_page("pages/00_Connexion.py")
        st.stop()
