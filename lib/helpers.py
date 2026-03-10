"""
ConducteurPro â Helpers communs pour toutes les pages Streamlit.
Fournit l'authentification, la configuration de page et la sidebar SaaS.
"""
import streamlit as st
from lib.supabase_client import init_supabase_session, get_user_id, is_authenticated, check_auth
from lib.auth import get_plan_limit, PLAN_LIMITS, get_plan_display


# âââ Configuration de page avec authentification âââââââââââââââââââââââââââââââ

def page_setup(title: str = "ConducteurPro", icon: str = "ðï¸", layout: str = "wide"):
    """Configure la page Streamlit et vÃ©rifie l'authentification.
    Retourne le user_id si authentifiÃ©, sinon redirige vers la page de connexion.
    """
    st.set_page_config(page_title=f"ConducteurPro Â· {title}", page_icon=icon, layout=layout)
    init_supabase_session()
    
    if not is_authenticated():
        st.warning("Veuillez vous connecter pour accÃ©der Ã  cette page.")
        st.switch_page("pages/00_Connexion.py")
        st.stop()
    
    user_id = get_user_id()
    if not user_id:
        st.error("Session expirÃ©e. Veuillez vous reconnecter.")
        st.switch_page("pages/00_Connexion.py")
        st.stop()
    
    return user_id


# âââ Sidebar SaaS âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def render_saas_sidebar(user_id: str):
    """Affiche la sidebar SaaS avec infos utilisateur, plan, navigation et logout."""
    from lib import db
    from lib.auth import logout_user
    
    with st.sidebar:
        st.markdown("### ðï¸ ConducteurPro")
        st.markdown("---")
        
        # Infos utilisateur
        profile = db.get_profile(user_id)
        if profile:
            plan = profile.get("plan", "free")
            plan_labels = {"free": "ð Gratuit", "pro": "â­ Pro", "team": "ð¥ Ãquipe"}
            st.markdown(f"**Utilisateur:** {profile.get('full_name', 'N/A')}")
            st.markdown(f"**Plan:** {plan_labels.get(plan, plan)}")
            st.markdown(f"**Email:** {profile.get('email', 'N/A')}")
            
            # Compteur de chantiers
            chantiers = db.get_chantiers(user_id)
            nb = len(chantiers) if chantiers else 0
            limit = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"]).get("max_chantiers", float("inf"))
            if limit != float("inf"):
                st.progress(min(nb / limit, 1.0), text=f"Chantiers: {nb}/{int(limit)}")
            else:
                st.markdown(f"**Chantiers:** {nb} (illimitÃ©)")
        
        st.markdown("---")
        
        # Navigation
        st.markdown("#### ð Navigation")
        nav_items = [
            ("ð  Accueil", "app.py"),
            ("ð Tableau de bord", "pages/0_Tableau_de_bord.py"),
            ("ð MÃ©trÃ©s", "pages/1_Metres.py"),
            ("ð DCE", "pages/2_DCE.py"),
            ("ð Ãtudes", "pages/3_Etudes.py"),
            ("ð Planning", "pages/4_Planning.py"),
            ("ðï¸ PLU", "pages/5_PLU.py"),
            ("ð SynthÃ¨se", "pages/6_Synthese.py"),
            ("ð° Devis", "pages/8_Devis.py"),
            ("ð³ Abonnement", "pages/9_Abonnement.py"),
            ("ð§¾ Facturation", "pages/10_Facturation.py"),
            ("ð Documents", "pages/11_Documents.py"),
        ]
        for label, page in nav_items:
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                st.switch_page(page)
        
        st.markdown("---")
        
        # Logout
        if st.button("ðª Se dÃ©connecter", use_container_width=True):
            logout_user()
            st.switch_page("pages/00_Connexion.py")


# âââ SÃ©lecteur de chantier ââââââââââââââââââââââââââââââââââââââââââââââââââââ

def chantier_selector(key: str = "chantier_select"):
    """Affiche un sÃ©lecteur de chantier et retourne le chantier sÃ©lectionnÃ© (dict) ou None."""
    from lib import db
    
    user_id = get_user_id()
    chantiers = db.get_chantiers(user_id) or []
    
    if not chantiers:
        st.info("Aucun chantier trouvÃ©. CrÃ©ez-en un depuis le Tableau de bord.")
        return None
    
    # Format options
    options = {f"{c['nom']} â {c.get('client', 'N/A')}": c for c in chantiers}
    selected_label = st.selectbox(
        "ð Chantier",
        list(options.keys()),
        key=key
    )
    
    return options.get(selected_label)


# âââ VÃ©rification de fonctionnalitÃ©s (feature gating) âââââââââââââââââââââââââ

def require_feature(user_id: str, feature: str):
    """VÃ©rifie que l'utilisateur a accÃ¨s Ã  une fonctionnalitÃ© selon son plan.
    Affiche un message d'upgrade et stoppe la page si pas d'accÃ¨s.
    
    Features: 'ai_analysis', 'import_data', 'export_pdf', 'advanced_planning',
              'multi_user', 'priority_support'
    """
    from lib import db
    from lib.auth import show_upgrade_message
    
    profile = db.get_profile(user_id)
    plan = profile.get("plan", "free") if profile else "free"
    
    # DÃ©finir quelles features sont disponibles par plan
    feature_access = {
        "free": ["ai_analysis"],  # 3 analyses gratuites par mois
        "pro": ["ai_analysis", "import_data", "export_pdf", "advanced_planning", "priority_support"],
        "team": ["ai_analysis", "import_data", "export_pdf", "advanced_planning", "multi_user", "priority_support"],
    }
    
    allowed = feature_access.get(plan, [])
    
    if feature not in allowed:
        show_upgrade_message(feature)
        st.stop()
    
    # Pour le plan free, vÃ©rifier les quotas
    if plan == "free" and feature == "ai_analysis":
        from datetime import datetime, timedelta
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        etudes = db.get_etudes(user_id) or []
        recent = [e for e in etudes if e.get("created_at", "") >= month_start.isoformat()]
        limit = PLAN_LIMITS.get("free", {}).get("ai_analyses_month", 3)
        if len(recent) >= limit:
            st.warning(f"ð« Limite atteinte : {int(limit)} analyses gratuites par mois.")
            show_upgrade_message("ai_analysis")
            st.stop()
