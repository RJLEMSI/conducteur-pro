"""
ConducteurPro  Helpers communs pour toutes les pages Streamlit.
Fournit l'authentification, la configuration de page et la sidebar SaaS.
"""
import streamlit as st
from lib.supabase_client import init_supabase_session, get_user_id, is_authenticated, check_auth
from lib.auth import get_plan_limit, PLAN_LIMITS, get_plan_display


#  Configuration de page avec authentification 

def page_setup(title: str = "ConducteurPro", icon: str = "", layout: str = "wide"):
    """Configure la page Streamlit et vrifie l'authentification.
    Retourne le user_id si authentifi, sinon redirige vers la page de connexion.
    """
    st.set_page_config(page_title=f"ConducteurPro  {title}", page_icon=icon, layout=layout)
    init_supabase_session()
    
    if not is_authenticated():
        st.warning("Veuillez vous connecter pour accder  cette page.")
        st.switch_page("pages/00_Connexion.py")
        st.stop()
    
    user_id = get_user_id()
    if not user_id:
        st.error("Session expire. Veuillez vous reconnecter.")
        st.switch_page("pages/00_Connexion.py")
        st.stop()
    
    return user_id


#  Sidebar SaaS 

def render_saas_sidebar(user_id: str):
    """Affiche la sidebar SaaS avec infos utilisateur, plan, navigation et logout."""
    from lib import db
    from lib.auth import logout_user
    
    with st.sidebar:
        st.markdown("""<div style="text-align:center;padding:0.5rem 0 0.8rem;"><span style="font-size:1.5rem;font-weight:800;color:#0D3B6E;">🏗️ ConducteurPro</span><br><span style="font-size:0.7rem;color:#7a8a9a;letter-spacing:0.5px;">LOGICIEL BTP PROFESSIONNEL</span></div>""", unsafe_allow_html=True)
        st.markdown("---")
        
        # Infos utilisateur
        profile = db.get_profile(user_id)
        if profile:
            plan = profile.get("subscription_plan", "free")
            plan_labels = {"free": " Gratuit", "pro": " Pro", "team": " quipe"}
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
                st.markdown(f"**Chantiers:** {nb} (illimité)")
        
        st.markdown("---")
        
        # Navigation
        st.markdown("####  Navigation")
        nav_items = [
            (" Accueil", "app.py"),
            (" Tableau de bord", "pages/0_Tableau_de_bord.py"),
            (" Mtrs", "pages/1_Metres.py"),
            (" DCE", "pages/2_DCE.py"),
            (" tudes", "pages/3_Etudes.py"),
            (" Planning", "pages/4_Planning.py"),
            (" PLU", "pages/5_PLU.py"),
            (" Synthse", "pages/6_Synthese.py"),
            (" Devis", "pages/8_Devis.py"),
            (" Abonnement", "pages/9_Abonnement.py"),
            (" Facturation", "pages/10_Facturation.py"),
            (" Documents", "pages/11_Documents.py"),
        ]
        for label, page in nav_items:
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                st.switch_page(page)
        
        st.markdown("---")
        
        # Logout
        if st.button(" Se déconnecter", use_container_width=True):
            logout_user()
            st.switch_page("pages/00_Connexion.py")


#  Slecteur de chantier 

def chantier_selector(key: str = "chantier_select"):
    """Affiche un slecteur de chantier et retourne le chantier slectionn (dict) ou None."""
    from lib import db
    
    user_id = get_user_id()
    chantiers = db.get_chantiers(user_id) or []
    
    if not chantiers:
        st.info("Aucun chantier trouvé. Créez-en un depuis le Tableau de bord.")
        return None
    
    # Format options
    options = {f"{c['nom']}  {c.get('client', 'N/A')}": c for c in chantiers}
    selected_label = st.selectbox(
        " Chantier",
        list(options.keys()),
        key=key
    )
    
    return options.get(selected_label)


#  Vrification de fonctionnalits (feature gating) 

def require_feature(user_id: str, feature: str):
    """Vrifie que l'utilisateur a accs  une fonctionnalit selon son plan.
    Affiche un message d'upgrade et stoppe la page si pas d'accs.
    
    Features: 'ai_analysis', 'import_data', 'export_pdf', 'advanced_planning',
              'multi_user', 'priority_support'
    """
    from lib import db
    from lib.auth import show_upgrade_message
    
    profile = db.get_profile(user_id)
    plan = profile.get("subscription_plan", "free") if profile else "free"
    
    # Dfinir quelles features sont disponibles par plan
    feature_access = {
        "free": ["ai_analysis"],  # 3 analyses gratuites par mois
        "pro": ["ai_analysis", "import_data", "export_pdf", "advanced_planning", "priority_support"],
        "team": ["ai_analysis", "import_data", "export_pdf", "advanced_planning", "multi_user", "priority_support"],
    }
    
    allowed = feature_access.get(plan, [])
    
    if feature not in allowed:
        show_upgrade_message(feature)
        st.stop()
    
    # Pour le plan free, vrifier les quotas
    if plan == "free" and feature == "ai_analysis":
        from datetime import datetime, timedelta
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        etudes = db.get_etudes(user_id) or []
        recent = [e for e in etudes if e.get("created_at", "") >= month_start.isoformat()]
        limit = PLAN_LIMITS.get("free", {}).get("ai_analyses_month", 3)
        if len(recent) >= limit:
            st.warning(f" Limite atteinte : {int(limit)} analyses gratuites par mois.")
            show_upgrade_message("ai_analysis")
            st.stop()
