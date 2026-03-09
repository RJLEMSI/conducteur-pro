"""
Page 00 — Connexion / Inscription
Première page affichée. Authentification via Supabase Auth.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils import GLOBAL_CSS
from lib.supabase_client import init_supabase_session, is_authenticated
from lib.auth import register_user, login_user, logout_user, reset_password

st.set_page_config(
    page_title="Connexion · ConducteurPro",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# Cacher la sidebar pour la page de connexion
st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none; }
    .login-container {
        max-width: 480px;
        margin: 0 auto;
        padding: 2rem;
    }
    .auth-card {
        background: white;
        border: 1px solid #E2EBF5;
        border-radius: 20px;
        padding: 2.5rem;
        box-shadow: 0 4px 24px rgba(13,59,110,0.08);
    }
    .brand-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .brand-header h1 {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0D3B6E;
        margin: 0;
    }
    .brand-header p {
        color: #6B7280;
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }
    .features-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.2rem;
        margin: 2rem 0;
    }
    .feature-item {
        text-align: center;
        padding: 1rem;
        background: #F8FAFF;
        border-radius: 12px;
    }
    .feature-item .icon { font-size: 1.8rem; }
    .feature-item .label {
        font-size: 0.82rem;
        color: #374151;
        font-weight: 600;
        margin-top: 0.4rem;
    }
</style>
""", unsafe_allow_html=True)

init_supabase_session()

# Si déjà connecté, rediriger vers le tableau de bord
if is_authenticated():
    st.switch_page("pages/0_Tableau_de_bord.py")

# ─── Header de marque ─────────────────────────────────────────────────────────
st.markdown("""
<div class="brand-header">
    <h1>🏗️ ConducteurPro</h1>
    <p>L'outil d'excellence pour les conducteurs de travaux</p>
</div>
""", unsafe_allow_html=True)

# ─── Features rapides ────────────────────────────────────────────────────────
st.markdown("""
<div class="features-grid">
    <div class="feature-item">
        <div class="icon">📐</div>
        <div class="label">Métrés automatiques</div>
    </div>
    <div class="feature-item">
        <div class="icon">📅</div>
        <div class="label">Planning intelligent</div>
    </div>
    <div class="feature-item">
        <div class="icon">💰</div>
        <div class="label">Devis & Factures</div>
    </div>
    <div class="feature-item">
        <div class="icon">📋</div>
        <div class="label">Synthèse DCE</div>
    </div>
    <div class="feature-item">
        <div class="icon">📁</div>
        <div class="label">Gestion documents</div>
    </div>
    <div class="feature-item">
        <div class="icon">🤖</div>
        <div class="label">Propulsé par l'IA</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Formulaire connexion / inscription ──────────────────────────────────────
tab_login, tab_register, tab_reset = st.tabs([
    "🔐 Se connecter",
    "📝 Créer un compte",
    "🔑 Mot de passe oublié"
])

# ─── Connexion ────────────────────────────────────────────────────────────────
with tab_login:
    with st.form("login_form", clear_on_submit=False):
        st.markdown("#### Connectez-vous à votre compte")
        email = st.text_input("Email", placeholder="votre@email.fr", key="login_email")
        password = st.text_input("Mot de passe", type="password", placeholder="••••••••", key="login_pwd")

        submitted = st.form_submit_button("Se connecter", type="primary", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Veuillez remplir tous les champs.")
            else:
                with st.spinner("Connexion en cours..."):
                    result = login_user(email, password)
                    if result["success"]:
                        st.success(result["message"])
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(result["message"])

    st.markdown("""
    <div style="text-align:center;margin-top:1rem;font-size:0.85rem;color:#6B7280;">
        Pas encore de compte ? Cliquez sur l'onglet <strong>"Créer un compte"</strong> ci-dessus.
    </div>
    """, unsafe_allow_html=True)

# ─── Inscription ──────────────────────────────────────────────────────────────
with tab_register:
    with st.form("register_form", clear_on_submit=True):
        st.markdown("#### Créez votre compte ConducteurPro")
        st.markdown("Commencez gratuitement avec 3 analyses par mois.")

        col1, col2 = st.columns(2)
        with col1:
            reg_name = st.text_input("Votre nom", placeholder="Jean Dupont", key="reg_name")
        with col2:
            reg_company = st.text_input("Entreprise (optionnel)", placeholder="BTP Dupont", key="reg_company")

        reg_email = st.text_input("Email professionnel", placeholder="jean@btpdupont.fr", key="reg_email")
        reg_pwd = st.text_input("Mot de passe", type="password", placeholder="Minimum 8 caractères", key="reg_pwd")
        reg_pwd2 = st.text_input("Confirmer le mot de passe", type="password", placeholder="Retapez votre mot de passe", key="reg_pwd2")

        st.markdown("""
        <div style="font-size:0.8rem;color:#6B7280;margin:0.5rem 0;">
            En créant un compte, vous acceptez nos <a href="#" target="_blank">Conditions d'utilisation</a>
            et notre <a href="#" target="_blank">Politique de confidentialité</a>.
        </div>
        """, unsafe_allow_html=True)

        submitted = st.form_submit_button("Créer mon compte", type="primary", use_container_width=True)

        if submitted:
            if not reg_email or not reg_pwd:
                st.error("Email et mot de passe sont obligatoires.")
            elif len(reg_pwd) < 8:
                st.error("Le mot de passe doit contenir au moins 8 caractères.")
            elif reg_pwd != reg_pwd2:
                st.error("Les mots de passe ne correspondent pas.")
            else:
                with st.spinner("Création du compte..."):
                    result = register_user(
                        email=reg_email,
                        password=reg_pwd,
                        display_name=reg_name,
                        company_name=reg_company,
                    )
                    if result["success"]:
                        st.success(result["message"])
                        st.info("📧 Vérifiez votre boîte mail pour confirmer votre inscription, puis connectez-vous.")
                    else:
                        st.error(result["message"])

# ─── Reset password ───────────────────────────────────────────────────────────
with tab_reset:
    with st.form("reset_form", clear_on_submit=True):
        st.markdown("#### Réinitialiser votre mot de passe")
        st.markdown("Entrez votre email et nous vous enverrons un lien de réinitialisation.")

        reset_email = st.text_input("Email", placeholder="votre@email.fr", key="reset_email")
        submitted = st.form_submit_button("Envoyer le lien", type="primary", use_container_width=True)

        if submitted:
            if not reset_email:
                st.error("Veuillez entrer votre adresse email.")
            else:
                with st.spinner("Envoi en cours..."):
                    result = reset_password(reset_email)
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#9CA3AF;font-size:0.8rem;">
    ConducteurPro v3.0 · Propulsé par Claude AI · © 2025 ConducteurPro
</div>
""", unsafe_allow_html=True)
