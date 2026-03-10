"""
auth.py ÃÂ¢ÃÂÃÂ Authentification utilisateur via Supabase Auth.
Login, register, logout, vÃÂÃÂ©rification email, reset password, feature gating.
"""
import streamlit as st
from datetime import datetime
from lib.supabase_client import get_supabase_client, init_supabase_session


# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Inscription ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ
def register_user(email: str, password: str, display_name: str = "", company_name: str = "") -> dict:
    """
    Inscrit un nouvel utilisateur via Supabase Auth + crÃÂÃÂ©e le profil.
    Retourne {"success": bool, "message": str, "user_id": str|None}
    """
    client = get_supabase_client()
    if not client:
        return {"success": False, "message": "Supabase non configurÃÂÃÂ©. VÃÂÃÂ©rifiez vos secrets.", "user_id": None}

    try:
        # CrÃÂÃÂ©er l'utilisateur dans Supabase Auth
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
            return {"success": False, "message": "Erreur lors de l'inscription. VÃÂÃÂ©rifiez vos informations.", "user_id": None}

        user_id = result.user.id

        # CrÃÂÃÂ©er le profil utilisateur dans la table user_profiles
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
            # Le profil sera crÃÂÃÂ©ÃÂÃÂ© au premier login si ÃÂÃÂ©chec ici
            pass

        return {
            "success": True,
            "message": "Compte crÃÂÃÂ©ÃÂÃÂ© ! VÃÂÃÂ©rifiez votre email pour confirmer votre inscription.",
            "user_id": user_id,
        }

    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
            return {"success": False, "message": "Un compte existe dÃÂÃÂ©jÃÂÃÂ  avec cet email.", "user_id": None}
        return {"success": False, "message": f"Erreur : {error_msg}", "user_id": None}


# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Connexion ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ
def login_user(email: str, password: str) -> dict:
    """
    Connecte un utilisateur existant.
    Retourne {"success": bool, "message": str, "user_id": str|None}
    """
    client = get_supabase_client()
    if not client:
        return {"success": False, "message": "Supabase non configurÃÂÃÂ©.", "user_id": None}

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

        return {"success": True, "message": "Connexion rÃÂÃÂ©ussie !", "user_id": user_id}

    except Exception as e:
        error_msg = str(e)
        if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
            return {"success": False, "message": "Email ou mot de passe incorrect.", "user_id": None}
        return {"success": False, "message": f"Erreur de connexion : {error_msg}", "user_id": None}


def _load_user_profile(client, user_id: str, email: str):
    """Charge ou crÃÂÃÂ©e le profil utilisateur depuis Supabase."""
    try:
        result = client.table("user_profiles").select("*").eq("user_id", user_id).execute()

        if result.data and len(result.data) > 0:
            profile = result.data[0]
            st.session_state.user_profile = profile
            st.session_state.user_name = profile.get("display_name", "")
            st.session_state.user_plan = profile.get("subscription_plan", "free")
        else:
            # CrÃÂÃÂ©er le profil s'il n'existe pas
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


# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ DÃÂÃÂ©connexion ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ
def logout_user():
    """DÃÂÃÂ©connecte l'utilisateur et nettoie la session."""
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


# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Reset password ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ
def reset_password(email: str) -> dict:
    """Envoie un email de rÃÂÃÂ©initialisation du mot de passe."""
    client = get_supabase_client()
    if not client:
        return {"success": False, "message": "Supabase non configurÃÂÃÂ©."}

    try:
        client.auth.reset_password_email(email)
        return {"success": True, "message": "Email de rÃÂÃÂ©initialisation envoyÃÂÃÂ©. VÃÂÃÂ©rifiez votre boÃÂÃÂ®te mail."}
    except Exception as e:
        return {"success": False, "message": f"Erreur : {e}"}


# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Refresh session ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ
def refresh_session():
    """Tente de rafraÃÂÃÂ®chir la session si un refresh token existe."""
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


# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Feature gating ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ
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
        "max_analyses_month": -1,  # illimitÃÂÃÂ©
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
    """VÃÂÃÂ©rifie si l'utilisateur a accÃÂÃÂ¨s ÃÂÃÂ  une fonctionnalitÃÂÃÂ©."""
    plan = st.session_state.get("user_plan", "free")
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

    val = limits.get(feature)
    if isinstance(val, bool):
        return val
    if isinstance(val, int):
        return val != 0
    return False


def get_plan_limit(feature: str):
    """Retourne la limite d'un plan pour une fonctionnalitÃÂÃÂ©."""
    plan = st.session_state.get("user_plan", "free")
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    return limits.get(feature, 0)


def show_upgrade_message(feature_name: str = "cette fonctionnalitÃÂÃÂ©"):
    """Affiche un message incitant ÃÂÃÂ  passer ÃÂÃÂ  un plan supÃÂÃÂ©rieur."""
    st.warning(f"ÃÂ¢ÃÂÃÂ ÃÂ¯ÃÂ¸ÃÂ **{feature_name}** n'est pas disponible avec votre plan actuel.")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0D3B6E,#1B6CA8);color:white;
                    border-radius:12px;padding:1rem;text-align:center;">
            <div style="font-size:1.1rem;font-weight:700;">ÃÂ°ÃÂÃÂÃÂ Pro ÃÂ¢ÃÂÃÂ 65,90 ÃÂ¢ÃÂÃÂ¬/mois</div>
            <div style="font-size:.85rem;opacity:.85;margin-top:.3rem;">1 utilisateur ÃÂÃÂ· 50 chantiers ÃÂÃÂ· 100 GB</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#1B6CA8,#3B82F6);color:white;
                    border-radius:12px;padding:1rem;text-align:center;">
            <div style="font-size:1.1rem;font-weight:700;">ÃÂ°ÃÂÃÂÃÂ¢ ÃÂÃÂquipe ÃÂ¢ÃÂÃÂ 119,60 ÃÂ¢ÃÂÃÂ¬/mois</div>
            <div style="font-size:.85rem;opacity:.85;margin-top:.3rem;">4 utilisateurs ÃÂÃÂ· 500 chantiers ÃÂÃÂ· 500 GB</div>
        </div>
        """, unsafe_allow_html=True)
    if st.button("ÃÂ¢ÃÂ­ÃÂ Voir les offres d'abonnement", use_container_width=True):
        st.switch_page("pages/9_Abonnement.py")


# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Garde de page (ÃÂÃÂ  appeler en haut de chaque page protÃÂÃÂ©gÃÂÃÂ©e) ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ
def require_auth():
    """
    VÃÂÃÂ©rifie que l'utilisateur est connectÃÂÃÂ©.
    Redirige vers la page de connexion sinon.
    Retourne True si authentifiÃÂÃÂ©.
    """
    init_supabase_session()

    if st.session_state.get("authenticated") and st.session_state.get("user_id"):
        return True

    # Tenter un refresh
    if refresh_session():
        return True

    # Non connectÃÂÃÂ© ÃÂ¢ÃÂÃÂ rediriger
    st.warning("ÃÂ°ÃÂÃÂÃÂ Veuillez vous connecter pour accÃÂÃÂ©der ÃÂÃÂ  cette page.")
    if st.button("Se connecter", type="primary", use_container_width=True):
        st.switch_page("pages/00_Connexion.py")
    st.stop()
    return False


# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Affichage du plan ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ

def get_plan_display(plan: str = None) -> dict:
    """Retourne les informations d'affichage pour un plan donnÃÂÃÂ©.
    Returns: dict avec 'name', 'icon', 'color', 'price', 'features'
    """
    import streamlit as st
    if plan is None:
        plan = st.session_state.get("user_plan", "free")
    
    plans = {
        "free": {
            "name": "Gratuit",
            "icon": "\u2696\ufe0f",
            "color": "#6c757d",
            "price": "0\u20ac/mois",
            "features": [
                "3 chantiers maximum",
                "3 analyses IA par mois",
                "Stockage 50 Mo",
            ]
        },
        "pro": {
            "name": "Pro",
            "icon": "\u2b50",
            "color": "#0066cc",
            "price": "69,90\u20ac/mois",
            "features": [
                "Chantiers illimit\u00e9s",
                "Analyses IA illimit\u00e9es",
                "Import de donn\u00e9es",
                "Export PDF",
                "Planning avanc\u00e9",
                "Support prioritaire",
                "Stockage 5 Go",
            ]
        },
        "team": {
            "name": "Equipe",
            "icon": "\u2605",
            "color": "#28a745",
            "price": "118,90\u20ac/mois",
            "features": [
                "Tout Pro +",
                "Jusqu\'a 4 utilisateurs",
                "Partage de chantiers",
                "Formation dediee (1h)",
                "Stockage 20 Go",
            ]
        }
    }
    return plans.get(plan, plans["free"])
