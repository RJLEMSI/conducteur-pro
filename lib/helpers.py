"""
ConducteurPro Helpers communs pour toutes les pages Streamlit.
Fournit l'authentification, la configuration de page et la sidebar SaaS.
"""

import streamlit as st
from lib.supabase_client import init_supabase_session, get_user_id, is_authenticated, check_auth
from lib.auth import get_plan_limit, PLAN_LIMITS, get_plan_display


# Configuration de page avec authentification
def page_setup(title: str = "ConducteurPro", icon: str = "", layout: str = "wide"):
    """Configure la page et verifie l'authentification."""
    init_supabase_session()

    if not is_authenticated():
        st.switch_page("pages/00_Connexion.py")
        st.stop()

    user_id = get_user_id()
    if not user_id:
        st.switch_page("pages/00_Connexion.py")
        st.stop()

    return user_id


# Sidebar SaaS - SANS navigation (geree par st.navigation dans app.py)
def render_saas_sidebar(user_id: str):
    """Affiche la sidebar SaaS avec infos utilisateur, plan et logout."""
    from lib import db
    from lib.auth import logout_user

    with st.sidebar:
        # Logo
        st.markdown("""<div style="text-align:center;padding:0.5rem 0 0.8rem;">
            <span style="font-size:1.5rem;font-weight:800;color:#0D3B6E;">\U0001f3d7\ufe0f ConducteurPro</span><br>
            <span style="font-size:0.7rem;color:#7a8a9a;letter-spacing:0.5px;">LOGICIEL BTP PROFESSIONNEL</span>
        </div>""", unsafe_allow_html=True)
        st.markdown("---")

        # Infos utilisateur
        profile = db.get_profile(user_id)
        if profile:
            plan = profile.get("subscription_plan", "free")
            plan_labels = {"free": "\U0001f7e2 Gratuit", "pro": "\U0001f535 Pro", "team": "\U0001f7e3 Equipe", "enterprise": "\U0001f451 Premium"}
            st.markdown(f"**Utilisateur:** {profile.get('display_name', 'N/A')}")
            st.markdown(f"**Plan:** {plan_labels.get(plan, plan)}")
            st.markdown(f"**Email:** {profile.get('email', 'N/A')}")

            # Compteur de chantiers
            chantiers = db.get_chantiers(user_id)
            nb = len(chantiers) if chantiers else 0
            limit = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"]).get("max_chantiers", float("inf"))
            if limit != float("inf"):
                st.progress(min(nb / limit, 1.0), text=f"Chantiers: {nb}/{int(limit)}")
            else:
                st.markdown(f"**Chantiers:** {nb} (illimite)")

        st.markdown("---")

        # Logout uniquement - la navigation est geree par st.navigation() dans app.py
        if st.button("\U0001f6aa Se deconnecter", width="stretch"):
            logout_user()
            st.rerun()


# Selecteur de chantier
def chantier_selector(key: str = "chantier_select"):
    """Affiche un selecteur de chantier et retourne le chantier selectionne (dict) ou None."""
    from lib import db
    user_id = get_user_id()
    chantiers = db.get_chantiers(user_id) or []
    if not chantiers:
        st.info("Aucun chantier trouve. Creez-en un depuis le Tableau de bord.")
        return None

    # Format options
    options = {}
    for c in chantiers:
        client_nom = c.get("client_nom", "") or c.get("client", "")
        ville = c.get("ville", "")
        label = c["nom"]
        if client_nom:
            label += f" â {client_nom}"
        elif ville:
            label += f" â {ville}"
        options[label] = c

    selected_label = st.selectbox(
        "Chantier",
        list(options.keys()),
        key=key
    )
    return options.get(selected_label)


# Verification de fonctionnalites (feature gating)
def require_feature(user_id: str, feature: str):
    """Verifie que l'utilisateur a acces a une fonctionnalite selon son plan."""
    from lib import db
    from lib.auth import show_upgrade_message

    profile = db.get_profile(user_id)
    plan = profile.get("subscription_plan", "free") if profile else "free"

    feature_access = {
        "free": ["ai_analysis"],
        "enterprise": ["ai_analysis", "import_data", "export_pdf", "advanced_planning", "multi_user", "priority_support", "achats", "sous_traitants", "pointage", "stocks", "crm", "suivi_financier", "agent_erp"],
        "pro": ["ai_analysis", "import_data", "export_pdf", "advanced_planning", "priority_support", "achats", "sous_traitants", "pointage", "stocks", "crm", "suivi_financier", "agent_erp"],
        "team": ["ai_analysis", "import_data", "export_pdf", "advanced_planning", "multi_user", "priority_support", "achats", "sous_traitants", "pointage", "stocks", "crm", "suivi_financier", "agent_erp"],
    }

    allowed = feature_access.get(plan, [])
    if feature not in allowed:
        show_upgrade_message(feature)
        st.stop()

    if plan == "free" and feature == "ai_analysis":
        from datetime import datetime
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        etudes = db.get_etudes(user_id) or []
        recent = [e for e in etudes if e.get("created_at", "") >= month_start.isoformat()]
        limit = PLAN_LIMITS.get("free", {}).get("ai_analyses_month", 3)
        if len(recent) >= limit:
            st.warning(f"Limite atteinte : {int(limit)} analyses gratuites par mois.")
            show_upgrade_message("ai_analysis")
            st.stop()
