import streamlit as st

# ─── Configuration de la page ──────────────────────────────────────────────────
st.set_page_config(
    page_title="ConducteurPro · IA Chantier",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Initialisation Supabase ──────────────────────────────────────────────────
from lib.supabase_client import init_supabase_session, is_authenticated, get_user_id
init_supabase_session()

# ─── CSS Global ──────────────────────────────────────────────────────────────
from utils import GLOBAL_CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ─── Routing : redirige selon l'état d'authentification ──────────────────────
if is_authenticated():
    user_id = get_user_id()

    # Sidebar SaaS
    from lib.helpers import render_saas_sidebar
    render_saas_sidebar(user_id)

    # ─── Page d'accueil authentifiée ────────────────────────────────────────
    st.markdown("## 🏗️ Bienvenue sur ConducteurPro")
    st.markdown("**L'outil d'excellence pour les conducteurs de travaux, propulsé par l'IA Claude.**")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 📊 Tableau de bord")
        st.markdown("Vue d'ensemble de tous vos chantiers, KPIs et alertes.")
        st.page_link("pages/0_Tableau_de_bord.py", label="Ouvrir →", icon="📊")

    with col2:
        st.markdown("### 📐 Analyse de plans")
        st.markdown("Métrés automatiques par IA à partir de vos plans PDF.")
        st.page_link("pages/1_Metres.py", label="Ouvrir →", icon="📐")

    with col3:
        st.markdown("### 📋 Synthèse DCE")
        st.markdown("Analyse complète de vos DCE en quelques secondes.")
        st.page_link("pages/2_DCE.py", label="Ouvrir →", icon="📋")

    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown("### 📅 Planning")
        st.markdown("Génération intelligente de planning avec Gantt interactif.")
        st.page_link("pages/4_Planning.py", label="Ouvrir →", icon="📅")

    with col5:
        st.markdown("### 💰 Devis")
        st.markdown("Devis professionnels PDF générés par l'IA.")
        st.page_link("pages/8_Devis.py", label="Ouvrir →", icon="💰")

    with col6:
        st.markdown("### 📁 Documents")
        st.markdown("Tous vos documents chantier classés et sécurisés.")
        st.page_link("pages/11_Documents.py", label="Ouvrir →", icon="📁")

    st.markdown("---")

    # Vérifier la clé API Anthropic
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""

    # Essayer de charger la clé depuis st.secrets
    try:
        if st.secrets.get("ANTHROPIC_API_KEY"):
            st.session_state.api_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass

    if not st.session_state.api_key:
        with st.expander("⚙️ Configuration de la clé API Anthropic", expanded=False):
            st.info("Pour utiliser les fonctionnalités IA (métrés, DCE, planning, devis), "
                    "une clé API Anthropic est nécessaire.")
            key_input = st.text_input("Clé API Anthropic", type="password",
                                       placeholder="sk-ant-...")
            if key_input:
                st.session_state.api_key = key_input
                st.success("✅ Clé API enregistrée pour cette session.")
                st.rerun()

else:
    # ─── Page d'accueil non authentifiée ────────────────────────────────────
    st.markdown("""
    <div style="text-align: center; padding: 3rem 0;">
        <h1>🏗️ ConducteurPro</h1>
        <h3 style="color: #6B7280;">L'outil d'excellence pour les conducteurs de travaux</h3>
        <p style="font-size: 1.1rem; color: #9CA3AF; max-width: 600px; margin: 1rem auto;">
            Métrés automatiques, planning intelligent, devis & factures,
            gestion documentaire. Propulsé par Claude AI.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.page_link("pages/00_Connexion.py", label="🔐 Se connecter",
                      icon="🔑", use_container_width=True)
        st.markdown("")
        st.page_link("pages/00_Connexion.py", label="🚀 Créer un compte gratuit",
                      icon="✨", use_container_width=True)

    st.markdown("---")

    # Section fonctionnalités
    st.markdown("### ✨ Fonctionnalités principales")
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("**📐 Métrés automatiques**")
        st.caption("Uploadez un plan, l'IA extrait tous les ouvrages mesurables.")
    with f2:
        st.markdown("**📅 Planning intelligent**")
        st.caption("Gantt interactif, phasage recommandé, ressources estimées.")
    with f3:
        st.markdown("**💰 Devis & Factures**")
        st.caption("Devis PDF professionnels et suivi de facturation complet.")

    # Section tarifs
    st.markdown("### 💎 Tarifs")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown("#### 🆓 Découverte")
        st.markdown("**Gratuit**")
        st.caption("3 analyses/mois · 3 chantiers max")
    with p2:
        st.markdown("#### 🚀 Pro")
        st.markdown("**69,90 €/mois**")
        st.caption("Illimité · 50 chantiers · 100 GB stockage")
    with p3:
        st.markdown("#### 🏢 Équipe")
        st.markdown("**118,90 €/mois**")
        st.caption("4 utilisateurs · 500 chantiers · 500 GB")
