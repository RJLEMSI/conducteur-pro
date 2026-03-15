"""
ConducteurPro - Client Supabase (singleton).
Initialise la connexion Supabase, gere la session utilisateur,
fournit les helpers d'authentification.
Inclut un store persistant fichier pour survivre aux rechargements de page.
"""
import streamlit as st
import json
import os
import traceback
from datetime import datetime
from supabase import create_client, Client


# ---- Fichier de log pour debug session ----
SESSION_LOG = "/tmp/conducteurpro_session_debug.log"

def _log_session(msg):
    """Log debug info pour diagnostiquer les problemes de session."""
    try:
        with open(SESSION_LOG, "a") as f:
            f.write(f"[{datetime.utcnow().isoformat()}] {msg}\n")
    except Exception:
        pass


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
        _log_session(f"save_persistent_session SKIP: user_id={bool(user_id)} rt={bool(refresh_token)}")
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
    _log_session(f"save_persistent_session OK: user={user_id[:8]}... rt_len={len(refresh_token)}")


def restore_persistent_session():
    """Tente de restaurer une session depuis le fichier.
    Essaie chaque session sauvegardee jusqu'a en trouver une valide.
    Utilise set_session() (plus fiable) avec fallback sur refresh_session().
    """
    sessions = _load_sessions()
    if not sessions:
        _log_session("restore_persistent_session: no sessions in file")
        return False

    client = get_supabase_client()

    for uid, data in list(sessions.items()):
        rt = data.get("refresh_token", "")
        at = data.get("access_token", "")
        if not rt:
            _log_session(f"restore: uid={uid[:8]}... no refresh_token, skip")
            continue

        # Methode 1: set_session (la plus fiable, concue pour restaurer des tokens stockes)
        try:
            _log_session(f"restore: trying set_session for uid={uid[:8]}... at_len={len(at)} rt_len={len(rt)}")
            result = client.auth.set_session(at, rt)
            if result and result.user:
                _apply_restored_session(result, data, sessions, uid)
                _log_session(f"restore: set_session SUCCESS for uid={uid[:8]}...")
                return True
            else:
                _log_session(f"restore: set_session returned no user")
        except Exception as e:
            _log_session(f"restore: set_session FAILED: {type(e).__name__}: {e}")

        # Methode 2: refresh_session avec le token
        try:
            _log_session(f"restore: trying refresh_session for uid={uid[:8]}...")
            result = client.auth.refresh_session(rt)
            if result and result.user:
                _apply_restored_session(result, data, sessions, uid)
                _log_session(f"restore: refresh_session SUCCESS for uid={uid[:8]}...")
                return True
            else:
                _log_session(f"restore: refresh_session returned no user")
        except Exception as e:
            _log_session(f"restore: refresh_session FAILED: {type(e).__name__}: {e}")

        # Les deux methodes ont echoue, supprimer cette session
        _log_session(f"restore: REMOVING invalid session for uid={uid[:8]}...")
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
        _log_session(f"clear_persistent_session: removed uid={uid[:8]}...")


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

    _log_session("init_supabase_session: not authenticated, trying restore...")

    # Tenter la restauration depuis le fichier persistant
    if restore_persistent_session():
        _log_session("init_supabase_session: restored from file OK")
        return

    # Tenter depuis le client Supabase (session en memoire du process)
    try:
        client = get_supabase_client()
        sess = client.auth.get_session()
        if sess and sess.user:
            st.session_state.user_id = sess.user.id
            st.session_state.user_email = sess.user.email
            st.session_state.authenticated = True
            # IMPORTANT: sauvegarder aussi les tokens pour la persistance
            if hasattr(sess, 'access_token') and hasattr(sess, 'refresh_token'):
                st.session_state.supabase_access_token = sess.access_token
                st.session_state.supabase_refresh_token = sess.refresh_token
            _log_session(f"init_supabase_session: restored from get_session OK, user={sess.user.id[:8]}...")
            return
    except Exception as e:
        _log_session(f"init_supabase_session: get_session failed: {type(e).__name__}: {e}")

    _log_session("init_supabase_session: no session found, user not authenticated")


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
