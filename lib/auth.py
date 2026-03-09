"""
auth.py — Authentification utilisateur via Supabase Auth.
Login, register, logout, vérification email, reset password, feature gating.
"""
import streamlit as st
from datetime import datetime
from lib.supabase_client import get_supabase_client, init_supabase_session


# ─── Inscription ──────────────────────────────────────────────────────────────
def register_user(email: str, password: str, display_name: str = "", company_name: str = "") -> dict:
    """
    Inscrit un nouvel utilisateur via Supabase Auth + crée le profil.
    Retourne {"success": bool, "message": str, "user_id": str|None}
    """
    client = get_supabase_client()
    if not client:
        return {"success": False, "message": "Supabase non configuré. Vérifiez vos secrets.", "user_id": None}

    try:
        # Créer l'utilisateur dans Supabase Auth
        result = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "display_name": display_name,
                    "company_name": company_name,
                }
            }
        })

        if result.user is None:
            return {"success": False, "message": "Erreur lors de l'inscription. Vérifiez vos informations.", "user_id": None}

        user_id = result.user.id

        # Créer le profil utilisateur dans la table user_profiles
        try:
            client.table("user_profiles").insert({
                "user_id": user_id,
                "email": email,
                "display_name": display_name or email.split("@")[0],
                "company_name": company_name,
                "subscription_plan": "free",
                "max_concurrent_users": 1,
                "storage_limit_gb": 1,
                "subscription_active": False,
                "onboarding_complete": False,
            }).execute()
        except Exception:
            # Le profil sera créé au premier login si échec ici
            pass

        return {
            "success": True,
            "message": "Compte créé ! Vérifiez votre email pour confirmer votre inscription.",
            "user_id": user_id,
        }

    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
            return {"success": False, "message": "Un compte existe déjà avec cet email.", "user_id": None}
        return {"success": False, "message": f"Erreur : {error_msg}", "user_id": None}


# ─── Connexion ────────────────────────────────────────────────────────────────
def login_user(email: str, password: str) -> dict:
    """
    Connecte un utilisateur existant.
    Retourne {"success": bool, "message": str, "user_id": str|None}
    """
    client = get_supabase_client()
    if not client:
        return {"success": False, "message": "Supabase non configuré.", "user_id": None}

    try:
        result = client.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })

        if result.user is None:
            return {"success": False, "message": "Email ou mot de passe incorrect.", "user_id": None}

        user_id = result.user.id

        # Stocker les tokens dans la session
        st.session_state.authenticated = True
        st.session_state.user_id = user_id
        st.session_state.user_email = email
        st.session_state.supabase_access_token = result.session.access_token
        st.session_state.supabase_refresh_token = result.session.refresh_token

        # Charger le profil utilisateur
        _load_user_profile(client, user_id, email)

        return {"success": True, "message": "Connexion réussie !", "user_id": user_id}

    except Exception as e:
        error_msg = str(e)
        if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
            return {"success": False, "message": "Email ou mot de passe incorrect.", "user_id": None}
        return {"success": False, "message": f"Erreur de connexion : {error_msg}", "user_id": None}


def _load_user_profile(client, user_id: str, email: str):
    """Charge ou crée le profil utilisateur depuis Supabase."""
    try:
        result = client.table("user_profiles").select("*").eq("user_id", user_id).execute()

        if result.data and len(result.data) > 0:
            profile = result.data[0]
            st.session_state.user_profile = profile
            st.session_state.user_name = profile.get("display_name", "")
            st.session_state.user_plan = profile.get("subscription_plan", "free")
        else:
            # Créer le profil s'il n'existe pas
            new_profile = {
                "user_id": user_id,
                "email": email,
                "display_name": email.split("@")[0],
                "subscription_plan": "free",
                "max_concurrent_users": 1,
                "storage_limit_gb": 1,
            }
            client.table("user_profiles").insert(new_profile).execute()
            st.session_state.user_profile = new_profile
            st.session_state.user_plan = "free"
    except Exception:
        st.session_state.user_plan = "free"


# ─── Déconnexion ──────────────────────────────────────────────────────────────
def logout_user():
    """Déconnecte l'utilisateur et nettoie la session."""
    client = get_supabase_client()
    if client:
        try:
            client.auth.sign_out()
        except Exception:
            pass

    keys_to_clear = [
        "authenticated", "user_id", "user_email", "user_name",
        "user_plan", "user_profile", "supabase_access_token",
        "supabase_refresh_token",
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    init_supabase_session()


# ─── Reset password ───────────────────────────────────────────────────────────
def reset_password(email: str) -> dict:
    """Envoie un email de réinitialisation du mot de passe."""
    client = get_supabase_client()
    if not client:
        return {"success": False, "message": "Supabase non configuré."}

    try:
        client.auth.reset_password_email(email)
        return {"success": True, "message": "Email de réinitialisation envoyé. Vérifiez votre boîte mail."}
    except Exception as e:
        return {"success": False, "message": f"Erreur : {e}"}


# ─── Refresh session ─────────────────────────────────────────────────────────
def refresh_session():
    """Tente de rafraîchir la session si un refresh token existe."""
    if not st.session_state.get("supabase_refresh_token"):
        return False

    client = get_supabase_client()
    if not client:
        return False

    try:
        result = client.auth.refresh_session(st.session_state.supabase_refresh_token)
        if result.user:
            st.session_state.authenticated = True
            st.session_state.user_id = result.user.id
            st.session_state.supabase_access_token = result.session.access_token
            st.session_state.supabase_refresh_token = result.session.refresh_token
            _load_user_profile(client, result.user.id, result.user.email)
            return True
    except Exception:
        pass

    return False


# ─── Feature gating ──────────────────────────────────────────────────────────
PLAN_LIMITS = {
    "free": {
        "max_chantiers": 3,
        "max_documents_mb": 500,
        "max_analyses_month": 3,
        "devis_pdf": False,
        "historique": False,
        "import_data": False,
        "support_priority": False,
    },
    "pro": {
        "max_chantiers": 50,
        "max_documents_mb": 100_000,  # 100 GB
        "max_analyses_month": -1,  # illimité
        "devis_pdf": True,
        "historique": True,
        "import_data": True,
        "support_priority": False,
    },
    "team": {
        "max_chantiers": 500,
        "max_documents_mb": 500_000,  # 500 GB
        "max_analyses_month": -1,
        "devis_pdf": True,
        "historique": True,
        "import_data": True,
        "support_priority": True,
    },
}


def check_feature(feature: str) -> bool:
    """Vérifie si l'utilisateur a accès à une fonctionnalité."""
    plan = st.session_state.get("user_plan", "free")
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

    val = limits.get(feature)
    if isinstance(val, bool):
        return val
    if isinstance(val, int):
        return val != 0
    return False


def get_plan_limit(feature: str):
    """Retourne la limite d'un plan pour une fonctionnalité."""
    plan = st.session_state.get("user_plan", "free")
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    return limits.get(feature, 0)


def show_upgrade_message(feature_name: str = "cette fonctionnalité"):
    """Affiche un message incitant à passer à un plan supérieur."""
    st.warning(f"⚠️ **{feature_name}** n'est pas disponible avec votre plan actuel.")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0D3B6E,#1B6CA8);color:white;
                    border-radius:12px;padding:1rem;text-align:center;">
            <div style="font-size:1.1rem;font-weight:700;">🚀 Pro — 65,90 €/mois</div>
            <div style="font-size:.85rem;opacity:.85;margin-top:.3rem;">1 utilisateur · 50 chantiers · 100 GB</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#1B6CA8,#3B82F6);color:white;
                    border-radius:12px;padding:1rem;text-align:center;">
            <div style="font-size:1.1rem;font-weight:700;">🏢 Équipe — 119,60 €/mois</div>
            <div style="font-size:.85rem;opacity:.85;margin-top:.3rem;">4 utilisateurs · 500 chantiers · 500 GB</div>
        </div>
        """, unsafe_allow_html=True)
    if st.button("⭐ Voir les offres d'abonnement", use_container_width=True):
        st.switch_page("pages/9_Abonnement.py")


# ─── Garde de page (à appeler en haut de chaque page protégée) ───────────────
def require_auth():
    """
    Vérifie que l'utilisateur est connecté.
    Redirige vers la page de connexion sinon.
    Retourne True si authentifié.
    """
    init_supabase_session()

    if st.session_state.get("authenticated") and st.session_state.get("user_id"):
        return True

    # Tenter un refresh
    if refresh_session():
        return True

    # Non connecté → rediriger
    st.warning("🔒 Veuillez vous connecter pour accéder à cette page.")
    if st.button("Se connecter", type="primary", use_container_width=True):
        st.switch_page("pages/00_Connexion.py")
    st.stop()
    return False
