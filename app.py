import streamlit as st

# âââ Configuration de la page ââââââââââââââââââââââââââââââââââââââââââââââââââ
st.set_page_config(
    page_title="ConducteurPro Â· IA Chantier",
    page_icon="ðï¸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# âââ Initialisation Supabase ââââââââââââââââââââââââââââââââââââââââââââââââââ
from lib.supabase_client import init_supabase_session, is_authenticated, get_user_id
init_supabase_session()

# âââ CSS Global ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
from utils import GLOBAL_CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# âââ Routing : redirige selon l'Ã©tat d'authentification ââââââââââââââââââââââ
if is_authenticated():
    user_id = get_user_id()

    # Sidebar SaaS
    from lib.helpers import render_saas_sidebar
    render_saas_sidebar(user_id)

    # âââ Page d'accueil authentifiÃ©e ââââââââââââââââââââââââââââââââââââââââ
    st.markdown("## ðï¸ Bienvenue sur ConducteurPro")
    st.markdown("**L'outil d'excellence pour les conducteurs de travaux, propulsÃ© par l'IA Claude.**")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### ð Tableau de bord")
        st.markdown("Vue d'ensemble de tous vos chantiers, KPIs et alertes.")
        st.page_link("pages/0_Tableau_de_bord.py", label="Ouvrir â", icon="ð")

    with col2:
        st.markdown("### ð Analyse de plans")
        st.markdown("MÃ©trÃ©s automatiques par IA Ã  partir de vos plans PDF.")
        st.page_link("pages/1_Metres.py", label="Ouvrir â", icon="ð")

    with col3:
        st.markdown("### ð SynthÃ¨se DCE")
        st.markdown("Analyse complÃ¨te de vos DCE en quelques secondes.")
        st.page_link("pages/2_DCE.py", label="Ouvrir â", icon="ð")

    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown("### ð Planning")
        st.markdown("GÃ©nÃ©ration intelligente de planning avec Gantt interactif.")
        st.page_link("pages/4_Planning.py", label="Ouvrir â", icon="ð")

    with col5:
        st.markdown("### ð° Devis")
        st.markdown("Devis professionnels PDF gÃ©nÃ©rÃ©s par l'IA.")
        st.page_link("pages/8_Devis.py", label="Ouvrir â", icon="ð°")

    with col6:
        st.markdown("### ð Documents")
        st.markdown("Tous vos documents chantier classÃ©s et sÃ©curisÃ©s.")
        st.page_link("pages/11_Documents.py", label="Ouvrir â", icon="ð")

    st.markdown("---")

    # VÃ©rifier la clÃ© API Anthropic
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""

    # Essayer de charger la clÃ© depuis st.secrets
    try:
        if st.secrets.get("ANTHROPIC_API_KEY"):
            st.session_state.api_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass

    if not st.session_state.api_key:
        with st.expander("âï¸ Configuration de la clÃ© API Anthropic", expanded=False):
            st.info("Pour utiliser les fonctionnalitÃ©s IA (mÃ©trÃ©s, DCE, planning, devis), "
                    "une clÃ© API Anthropic est nÃ©cessaire.")
            key_input = st.text_input("ClÃ© API Anthropic", type="password",
                                       placeholder="sk-ant-...")
            if key_input:
                st.session_state.api_key = key_input
                st.success("â ClÃ© API enregistrÃ©e pour cette session.")
                st.rerun()

else:
    # âââ Page d'accueil non authentifiÃ©e ââââââââââââââââââââââââââââââââââââ
    st.markdown("""
    <div style="text-align: center; padding: 3rem 0;">
        <h1>ðï¸ ConducteurPro</h1>
        <h3 style="color: #6B7280;">L'outil d'excellence pour les conducteurs de travaux</h3>
        <p style="font-size: 1.1rem; color: #9CA3AF; max-width: 600px; margin: 1rem auto;">
            MÃ©trÃ©s automatiques, planning intelligent, devis & factures,
            gestion documentaire. PropulsÃ© par Claude AI.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.page_link("pages/00_Connexion.py", label="ð Se connecter",
                      icon="ð", use_container_width=True)
        st.markdown("")
        st.page_link("pages/00_Connexion.py", label="ð CrÃ©er un compte gratuit",
                      icon="â¨", use_container_width=True)

    st.markdown("---")

    # Section fonctionnalitÃ©s
    st.markdown("### â¨ FonctionnalitÃ©s principales")
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("**ð MÃ©trÃ©s automatiques**")
        st.caption("Uploadez un plan, l'IA extrait tous les ouvrages mesurables.")
    with f2:
        st.markdown("**ð Planning intelligent**")
        st.caption("Gantt interactif, phasage recommandÃ©, ressources estimÃ©es.")
    with f3:
        st.markdown("**ð° Devis & Factures**")
        st.caption("Devis PDF professionnels et suivi de facturation complet.")

    # Section tarifs
    st.markdown("### ð Tarifs")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown("#### ð DÃ©couverte")
        st.markdown("**Gratuit**")
        st.caption("3 analyses/mois Â· 3 chantiers max")
    with p2:
        st.markdown("#### ð Pro")
        st.markdown("**69,90 â¬/mois**")
        st.caption("IllimitÃ© Â· 50 chantiers Â· 100 GB stockage")
    with p3:
        st.markdown("#### ð¢ Ãquipe")
        st.markdown("**118,90 â¬/mois**")
        st.caption("4 utilisateurs Â· 500 chantiers Â· 500 GB")
