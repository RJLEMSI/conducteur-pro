"""
ConducteurPro — Client Supabase (singleton).
Initialise la connexion Supabase, gère la session utilisateur,
fournit les helpers d'authentification.
Inclut un store persistant pour survivre aux rechargements de page.
"""
import streamlit as st
import uuid
from supabase import create_client, Client


# ---- Store persistant côté serveur (survit aux refresh de page) ----
@st.cache_resource
def _get_persistent_store():
    """Dict partagé entre toutes les sessions Streamlit. Clé = sid, Valeur = dict de session."""
    return {}


def save_persistent_session(user_id, email, access_token, refresh_token, plan="free"):
    """Sauvegarde la session dans le store persistant et stocke le sid en query_params."""
    store = _get_persistent_store()
    sid = str(uuid.uuid4())
    store[sid] = {
        "user_id": user_id,
        "email": email,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "plan": plan,
    }
    st.query_params["sid"] = sid


def restore_persistent_session():
    """Tente de restaurer la session depuis le store persistant via query_params['sid'].
    Retourne True si la session a été restaurée avec succès."""
    sid = st.query_params.get("sid")
    if not sid:
        return False

    store = _get_persistent_store()
    data = store.get(sid)
    if not data:
        return False

    try:
        client = get_supabase_client()
        # Tenter de rafraîchir la session Supabase avec le refresh token
        result = client.auth.refresh_session(data["refresh_token"])
        if result and result.user:
            st.session_state.authenticated = True
            st.session_state.user_id = result.user.id
            st.session_state.user_email = result.user.email or data["email"]
            st.session_state.supabase_access_token = result.session.access_token
            st.session_state.supabase_refresh_token = result.session.refresh_token
            st.session_state.user_plan = data.get("plan", "free")
            # Mettre à jour le store avec les nouveaux tokens
            store[sid]["access_token"] = result.session.access_token
            store[sid]["refresh_token"] = result.session.refresh_token
            return True
    except Exception:
        # Token expiré ou invalide — nettoyer
        store.pop(sid, None)
        if "sid" in st.query_params:
            del st.query_params["sid"]

    return False


def clear_persistent_session():
    """Supprime la session persistante (appelé lors de la déconnexion)."""
    sid = st.query_params.get("sid")
    if sid:
        store = _get_persistent_store()
        store.pop(sid, None)
        del st.query_params["sid"]


# ---- Client Supabase ----

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
    """Retourne le client Supabase avec le service role key (admin)."""
    if "supabase_admin" not in st.session_state:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not key:
            return get_supabase_client()  # fallback to anon client
        st.session_state.supabase_admin = create_client(url, key)
    return st.session_state.supabase_admin


def init_supabase_session():
    """Initialise la session Supabase.
    Tente de restaurer depuis le store persistant si session_state est vide.
    """
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.session_state.user_plan = "free"
        st.session_state.authenticated = False

    # Si déjà authentifié, rien à faire
    if st.session_state.authenticated:
        return

    # Tenter la restauration depuis le store persistant
    if restore_persistent_session():
        return

    # Tenter de restaurer depuis le token en cache (session_state)
    if st.session_state.get("supabase_access_token"):
        try:
            client = get_supabase_client()
            sess = client.auth.get_session()
            if sess and sess.user:
                st.session_state.user_id = sess.user.id
                st.session_state.user_email = sess.user.email
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
    """Vérifie l'authentification et redirige vers la page de connexion si non connecté."""
    init_supabase_session()
    if not is_authenticated():
        st.warning("Vous devez être connecté pour accéder à cette page.")
        st.switch_page("pages/00_Connexion.py")
        st.stop()
