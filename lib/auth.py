"""
auth.py â Authentification utilisateur via Supabase Auth.
Login, register, logout, vÃ©rification email, reset password, feature gating.
"""
import streamlit as st
from datetime import datetime
from lib.supabase_client import get_supabase_client, init_supabase_session


# âââ Inscription ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def register_user(email: str, password: str, display_name: str = "", company_name: str = "") -> dict:
    """
    Inscrit un nouvel utilisateur via Supabase Auth + crÃ©e le profil.
    Retourne {"success": bool, "message": str, "user_id": str|None}
    """
    client = get_supabase_client()
    if not client:
        return {"success": False, "message": "Supabase non configurÃ©. VÃ©rifiez vos secrets.", "user_id": None}

    try:
        # CrÃ©er l'utilisateur dans Supabase Auth
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
            return {"success": False, "message": "Erreur lors de l'inscription. VÃ©rifiez vos informations.", "user_id": None}

        user_id = result.user.id

        # CrÃ©er le profil utilisateur dans la table user_profiles
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
            # Le profil sera crÃ©Ã© au premier login si Ã©chec ici
            pass

        return {
            "success": True,
            "message": "Compte crÃ©Ã© ! VÃ©rifiez votre email pour confirmer votre inscription.",
            "user_id": user_id,
        }

    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
            return {"success": False, "message": "Un compte existe dÃ©jÃ  avec cet email.", "user_id": None}
        return {"success": False, "message": f"Erreur : {error_msg}", "user_id": None}


# âââ Connexion ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def login_user(email: str, password: str) -> dict:
    """
    Connecte un utilisateur existant.
    Retourne {"success": bool, "message": str, "user_id": str|None}
    """
    client = get_supabase_client()
    if not client:
        return {"success": False, "message": "Supabase non configurÃ©.", "user_id": None}

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

        return {"success": True, "message": "Connexion rÃ©ussie !", "user_id": user_id}

    except Exception as e:
        error_msg = str(e)
        if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
            return {"success": False, "message": "Email ou mot de passe incorrect.", "user_id": None}
        return {"success": False, "message": f"Erreur de connexion : {error_msg}", "user_id": None}


def _load_user_profile(client, user_id: str, email: str):
    """Charge ou crÃ©e le profil utilisateur depuis Supabase."""
    try:
        result = client.table("user_profiles").select("*").eq("user_id", user_id).execute()

        if result.data and len(result.data) > 0:
            profile = result.data[0]
            st.session_state.user_profile = profile
            st.session_state.user_name = profile.get("display_name", "")
            st.session_state.user_plan = profile.get("subscription_plan", "free")
        else:
            # CrÃ©er le profil s'il n'existe pas
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


# âââ DÃ©connexion ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def logout_user():
    """DÃ©connecte l'utilisateur et nettoie la session."""
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


# âââ Reset password âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def reset_password(email: str) -> dict:
    """Envoie un email de rÃ©initialisation du mot de passe."""
    client = get_supabase_client()
    if not client:
        return {"success": False, "message": "Supabase non configurÃ©."}

    try:
        client.auth.reset_password_email(email)
        return {"success": True, "message": "Email de rÃ©initialisation envoyÃ©. VÃ©rifiez votre boÃ®te mail."}
    except Exception as e:
        return {"success": False, "message": f"Erreur : {e}"}


# âââ Refresh session âââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def refresh_session():
    """Tente de rafraÃ®chir la session si un refresh token existe."""
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


# âââ Feature gating ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
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
        "max_analyses_month": -1,  # illimitÃ©
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
    """VÃ©rifie si l'utilisateur a accÃ¨s Ã  une fonctionnalitÃ©."""
    plan = st.session_state.get("user_plan", "free")
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

    val = limits.get(feature)
    if isinstance(val, bool):
        return val
    if isinstance(val, int):
        return val != 0
    return False


def get_plan_limit(feature: str):
    """Retourne la limite d'un plan pour une fonctionnalitÃ©."""
    plan = st.session_state.get("user_plan", "free")
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    return limits.get(feature, 0)


def show_upgrade_message(feature_name: str = "cette fonctionnalitÃ©"):
    """Affiche un message incitant Ã  passer Ã  un plan supÃ©rieur."""
    st.warning(f"â ï¸ **{feature_name}** n'est pas disponible avec votre plan actuel.")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0D3B6E,#1B6CA8);color:white;
                    border-radius:12px;padding:1rem;text-align:center;">
            <div style="font-size:1.1rem;font-weight:700;">ð Pro â 65,90 â¬/mois</div>
            <div style="font-size:.85rem;opacity:.85;margin-top:.3rem;">1 utilisateur Â· 50 chantiers Â· 100 GB</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#1B6CA8,#3B82F6);color:white;
                    border-radius:12px;padding:1rem;text-align:center;">
            <div style="font-size:1.1rem;font-weight:700;">ð¢ Ãquipe â 119,60 â¬/mois</div>
            <div style="font-size:.85rem;opacity:.85;margin-top:.3rem;">4 utilisateurs Â· 500 chantiers Â· 500 GB</div>
        </div>
        """, unsafe_allow_html=True)
    if st.button("â­ Voir les offres d'abonnement", use_container_width=True):
        st.switch_page("pages/9_Abonnement.py")


# âââ Garde de page (Ã  appeler en haut de chaque page protÃ©gÃ©e) âââââââââââââââ
def require_auth():
    """
    VÃ©rifie que l'utilisateur est connectÃ©.
    Redirige vers la page de connexion sinon.
    Retourne True si authentifiÃ©.
    """
    init_supabase_session()

    if st.session_state.get("authenticated") and st.session_state.get("user_id"):
        return True

    # Tenter un refresh
    if refresh_session():
        return True

    # Non connectÃ© â rediriger
    st.warning("ð Veuillez vous connecter pour accÃ©der Ã  cette page.")
    if st.button("Se connecter", type="primary", use_container_width=True):
        st.switch_page("pages/00_Connexion.py")
    st.stop()
    return False


# âââ Affichage du plan ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def get_plan_display(plan: str = None) -> dict:
    """Retourne les informations d'affichage pour un plan donnÃ©.
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
            "name": "\u00c9quipe",
            "icon": "\ud83d\udc65",
            "color": "#28a745",
            "price": "118,90\u20ac/mois",
            "features": [
                "Tout Pro +",
                "Jusqu\u2019\u00e0 4 utilisateurs",
                "Partage de chantiers",
                "Formation dédiée (1h)",
                "Stockage 20 Go",
            ]
        }
    }
    return plans.get(plan, plans["free"])
