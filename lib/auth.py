"""
auth.py - Authentification utilisateur via Supabase Auth.
Login, register, logout, verification email, reset password, feature gating.
"""
import streamlit as st
from datetime import datetime
from lib.supabase_client import get_supabase_client, init_supabase_session


# --- Inscription ---
def register_user(email: str, password: str, display_name: str = "", company_name: str = "") -> dict:
    """Inscrit un nouvel utilisateur via Supabase Auth."""
    client = get_supabase_client()
    if not client:
        return {"success": False, "message": "Service indisponible.", "user_id": None}

    try:
        result = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "display_name": display_name or email.split("@")[0],
                    "company_name": company_name,
                }
            }
        })

        if not result.user:
            return {"success": False, "message": "Echec de l'inscription. Vérifiéz vos informations.", "user_id": None}

        user_id = result.user.id

        # Creer le profil utilisateur dans la table user_profiles
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
            # Le profil sera cree au premier login si echec ici
            pass

        return {
            "success": True,
            "message": "Compte cree ! Vérifiéz votre email pour confirmer votre inscription.",
            "user_id": user_id,
        }

    except Exception as e:
        error_msg = str(e)
        if "already" in error_msg.lower():
            return {"success": False, "message": "Cet email est deja utilise.", "user_id": None}
        return {"success": False, "message": f"Erreur : {error_msg}", "user_id": None}


# --- Connexion ---
def login_user(email: str, password: str) -> dict:
    """Connecté un utilisateur via Supabase Auth."""
    client = get_supabase_client()
    if not client:
        return {"success": False, "message": "Service indisponible.", "user_id": None}

    try:
        result = client.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })

        if not result.user:
            return {"success": False, "message": "Echec de connexion.", "user_id": None}

        user_id = result.user.id
        email = result.user.email

        # Stocker la session
        st.session_state.authenticated = True
        st.session_state.user_id = user_id
        st.session_state.user_email = email
        st.session_state.supabase_access_token = result.session.access_token
        st.session_state.supabase_refresh_token = result.session.refresh_token

        # Charger le profil utilisateur
        _load_user_profile(client, user_id, email)

        return {"success": True, "message": "Connexion reussie !", "user_id": user_id}

    except Exception as e:
        error_msg = str(e)
        if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
            return {"success": False, "message": "Email ou mot de passe incorrect.", "user_id": None}
        return {"success": False, "message": f"Erreur de connexion : {error_msg}", "user_id": None}


def _load_user_profile(client, user_id: str, email: str):
    """Charge ou cree le profil utilisateur depuis Supabase."""
    try:
        result = client.table("user_profiles").select("*").eq("user_id", user_id).execute()

        if result.data and len(result.data) > 0:
            profile = result.data[0]
            st.session_state.user_plan = profile.get("subscription_plan", "free")
            st.session_state.user_display_name = profile.get("display_name", "")
            st.session_state.user_company = profile.get("company_name", "")
            st.session_state.subscription_active = profile.get("subscription_active", False)
        else:
            # Creer un profil par defaut
            try:
                client.table("user_profiles").insert({
                    "user_id": user_id,
                    "email": email,
                    "display_name": email.split("@")[0],
                    "subscription_plan": "free",
                    "max_concurrent_users": 1,
                    "storage_limit_gb": 1,
                    "subscription_active": False,
                    "onboarding_complete": False,
                }).execute()
            except Exception:
                pass
            st.session_state.user_plan = "free"
            st.session_state.user_display_name = email.split("@")[0]
            st.session_state.user_company = ""
            st.session_state.subscription_active = False

    except Exception:
        st.session_state.user_plan = "free"
        st.session_state.user_display_name = email.split("@")[0]
        st.session_state.user_company = ""
        st.session_state.subscription_active = False


# --- Déconnexion ---
def logout_user():
    """Deconnecté l'utilisateur."""
    client = get_supabase_client()
    if client:
        try:
            client.auth.sign_out()
        except Exception:
            pass

    keys_to_clear = [
        "authenticated", "user_id", "user_email", "user_plan",
        "user_display_name", "user_company", "subscription_active",
        "supabase_access_token", "supabase_refresh_token",
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    init_supabase_session()


# --- Reset password ---
def reset_password(email: str) -> dict:
    """Envoie un email de réinitialisation du mot de passe."""
    client = get_supabase_client()
    if not client:
        return {"success": False, "message": "Service indisponible."}

    try:
        client.auth.reset_password_email(email)
        return {"success": True, "message": "Email de réinitialisation envoye."}
    except Exception as e:
        return {"success": False, "message": f"Erreur : {str(e)}"}


# --- Refresh session ---
def refresh_session():
    """Tente de rafraichir la session si un refresh token existe."""
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


# --- Feature gating ---
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
        "max_analyses_month": -1,
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
    """Vérifié si l'utilisateur a acces a une fonctionnalite."""
    plan = st.session_state.get("user_plan", "free")
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

    val = limits.get(feature)
    if isinstance(val, bool):
        return val
    if isinstance(val, int):
        return val != 0
    return False


def get_plan_limit(feature: str):
    """Retourne la limite d'un plan pour une fonctionnalite."""
    plan = st.session_state.get("user_plan", "free")
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    return limits.get(feature, 0)


def show_upgrade_message(feature_name: str = "cette fonctionnalite"):
    """Affiche un message incitant a passer a un plan superieur."""
    st.warning(f"**{feature_name}** n'est pas disponible avec votre plan actuel.")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background:#f8f9fa;padding:15px;border-radius:8px;text-align:center;">
            <h4>Plan Pro</h4>
            <p>65,90 EUR/mois</p>
            <p>Toutes les fonctionnalites</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background:#f8f9fa;padding:15px;border-radius:8px;text-align:center;">
            <h4>Plan Équipe</h4>
            <p>119,60 EUR/mois</p>
            <p>Jusqu'à 4 utilisateurs</p>
        </div>
        """, unsafe_allow_html=True)
    if st.button("Voir les plans", type="primary"):
        st.switch_page("pages/9_Abonnement.py")

# --- Garde de page (a appeler en haut de chaque page protegee) ---
def require_auth():
    """
    Vérifié que l'utilisateur est connecté.
    Redirige vers la page de connexion sinon.
    Retourne True si authentifié.
    """
    init_supabase_session()

    if st.session_state.get("authenticated") and st.session_state.get("user_id"):
        return True

    # Tenter un refresh
    if refresh_session():
        return True

    # Non connecté - rediriger
    st.warning("Veuillez vous connectér pour acceder a cette page.")
    if st.button("Se connectér", type="primary", use_container_width=True):
        st.switch_page("pages/00_Connexion.py")
    st.stop()
    return False


# --- Affichage des plans ---
def get_plan_display(plan: str = None) -> dict:
    """Retourne les informations d'affichage pour un plan donne.
    Returns: dict avec 'name', 'icon', 'color', 'price', 'features'
    """
    import streamlit as st
    if plan is None:
        plan = st.session_state.get("user_plan", "free")

    plans = {
        "free": {
            "name": "Gratuit",
            "icon": "*",
            "color": "#6c757d",
            "price": "0 EUR/mois",
            "features": [
                "3 chantiers maximum",
                "3 analyses IA par mois",
                "Stockage 50 Mo",
            ]
        },
        "pro": {
            "name": "Pro",
            "icon": "*",
            "color": "#0066cc",
            "price": "65,90 EUR/mois",
            "features": [
                "Chantiers illimités",
                "Analyses IA illimitées",
                "Import de données",
                "Export PDF",
                "Planning avancé",
                "Support prioritaire",
                "Stockage 5 Go",
            ]
        },
        "team": {
            "name": "Équipe",
            "icon": "*",
            "color": "#28a745",
            "price": "119,60 EUR/mois",
            "features": [
                "Tout Pro +",
                "Jusqu'à 4 utilisateurs",
                "Partage de chantiers",
                "Formation dédiée (1h)",
                "Stockage 20 Go",
            ]
        }
    }
    return plans.get(plan, plans["free"])
