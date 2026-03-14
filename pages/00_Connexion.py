"""
Page 00  Connexion / Inscription
Premire page affiche. Authentification via Supabase Auth.
"""
import sys, os
import random
import time as _time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils import GLOBAL_CSS
from lib.supabase_client import init_supabase_session, is_authenticated
from lib.auth import register_user, login_user, logout_user, reset_password

# st.set_page_config géré par app.py
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# Cacher la sidebar pour la page de connexion
st.markdown("""
<style>
    /* Hide sidebar on login page */
    [data-testid="stSidebar"] { display: none; }
    [data-testid="stSidebarNav"] { display: none; }
    
    /* Professional login page styling */
    .brand-header {
        text-align: center;
        padding: 2rem 1rem 1rem;
        margin-bottom: 0.5rem;
    }
    .brand-header h1 {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1B4F8A 0%, #2E86DE 50%, #1B4F8A 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
        letter-spacing: -0.5px;
    }
    .brand-header .tagline {
        font-size: 1.15rem;
        color: #5a6a7a;
        font-weight: 400;
        margin-bottom: 0;
    }
    .brand-header .badge {
        display: inline-block;
        background: linear-gradient(135deg, #1B4F8A, #2E86DE);
        color: white;
        padding: 0.25rem 0.9rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 0.8rem;
        letter-spacing: 0.5px;
    }
    
    /* Feature cards */
    .features-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.8rem;
        margin: 1rem 0 1.5rem;
        padding: 0 0.5rem;
    }
    .feature-card {
        background: white;
        border: 1px solid #e8ecf1;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .feature-card:hover {
        border-color: #2E86DE;
        box-shadow: 0 4px 12px rgba(46,134,222,0.12);
        transform: translateY(-2px);
    }
    .feature-card .icon {
        font-size: 1.6rem;
        margin-bottom: 0.4rem;
    }
    .feature-card .title {
        font-weight: 600;
        font-size: 0.85rem;
        color: #1A2B3C;
        margin-bottom: 0.2rem;
    }
    .feature-card .desc {
        font-size: 0.72rem;
        color: #7a8a9a;
        line-height: 1.3;
    }
    
    /* Form styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        justify-content: center;
        border-bottom: 2px solid #e8ecf1;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.6rem 1.5rem;
        font-weight: 500;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        border-bottom-color: #1B4F8A !important;
        color: #1B4F8A !important;
    }
    
    /* Login container */
    .login-container {
        max-width: 480px;
        margin: 0 auto;
    }
    
    /* Footer */
    .login-footer {
        text-align: center;
        padding: 1.5rem 0 0.5rem;
        color: #9aa5b4;
        font-size: 0.75rem;
        border-top: 1px solid #eef1f5;
        margin-top: 2rem;
    }
    .login-footer a { color: #2E86DE; text-decoration: none; }
    .login-footer a:hover { text-decoration: underline; }
    
    /* Trust badges */
    .trust-badges {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        margin: 1rem 0;
        flex-wrap: wrap;
    }
    .trust-badge {
        display: flex;
        align-items: center;
        gap: 0.3rem;
        font-size: 0.75rem;
        color: #6a7a8a;
    }
</style>
""", unsafe_allow_html=True)


def _generate_otp():
    return str(random.randint(100000, 999999))

def _send_otp(to_email, code):
    smtp_email = os.environ.get("SMTP_EMAIL", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    if not smtp_email or not smtp_password:
        return False
    msg = MIMEMultipart()
    msg["From"] = f"ConducteurPro <{smtp_email}>"
    msg["To"] = to_email
    msg["Subject"] = f"ConducteurPro - Code : {code}"
    body = f"""<html><body style="font-family:Arial,sans-serif;padding:20px;">
    <div style="max-width:400px;margin:0 auto;background:linear-gradient(135deg,#1B4F8A,#2D6BB4);padding:30px;border-radius:12px;color:white;text-align:center;">
    <h2>ConducteurPro</h2><p>Votre code de verification :</p>
    <div style="background:white;color:#1B4F8A;font-size:32px;font-weight:700;letter-spacing:8px;padding:15px;border-radius:8px;margin:20px 0;">{code}</div>
    <p style="font-size:14px;opacity:0.8;">Ce code expire dans 5 minutes.</p></div></body></html>"""
    msg.attach(MIMEText(body, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, to_email, msg.as_string())
        return True
    except Exception:
        return False

init_supabase_session()

# Si déjà connect, rediriger vers le tableau de bord
if is_authenticated():
    st.switch_page("pages/0_Tableau_de_bord.py")



# ✨ Header de marque
st.markdown("""
<div class="brand-header">
    <h1>🏗️ ConducteurPro</h1>
    <p class="tagline">La plateforme tout-en-un pour les conducteurs de travaux</p>
    <span class="badge">LOGICIEL PROFESSIONNEL BTP</span>
</div>
""", unsafe_allow_html=True)

# 📊 Features rapides
st.markdown("""
<div class="features-grid">
    <div class="feature-card">
        <div class="icon">📅</div>
        <div class="title">Planning intelligent</div>
        <div class="desc">Gantt interactif et suivi en temps réel</div>
    </div>
    <div class="feature-card">
        <div class="icon">📄</div>
        <div class="title">Devis & Factures</div>
        <div class="desc">Génération automatique de PDF professionnels</div>
    </div>
    <div class="feature-card">
        <div class="icon">🤖</div>
        <div class="title">IA Intégrée</div>
        <div class="desc">Analyse de plans, métrés et études techniques</div>
    </div>
    <div class="feature-card">
        <div class="icon">📁</div>
        <div class="title">GED Complète</div>
        <div class="desc">Gestion documentaire centralisée et sécurisée</div>
    </div>
    <div class="feature-card">
        <div class="icon">📊</div>
        <div class="title">Tableaux de bord</div>
        <div class="desc">KPIs en temps réel et suivi financier</div>
    </div>
    <div class="feature-card">
        <div class="icon">🔒</div>
        <div class="title">Sécurité Renforcée</div>
        <div class="desc">Chiffrement AES-256 et isolation des données</div>
    </div>
</div>

<div class="trust-badges">
    <span class="trust-badge">✅ Données hébergées en Europe</span>
    <span class="trust-badge">🔒 Chiffrement de bout en bout</span>
    <span class="trust-badge">⚡ Déploiement instantané</span>
</div>
""", unsafe_allow_html=True)


#  Formulaire connexion / inscription 
tab_login, tab_register, tab_reset = st.tabs([
    " Se connecter",
    " Créer un compte",
    " Mot de passe oublié"
])

#  Connexion 
with tab_login:
    # --- Mode verification OTP ---
    if st.session_state.get("pending_2fa"):
        st.markdown("### \U0001f510 Verification de securite")
        pending_email = st.session_state.get("pending_email", "")
        masked = pending_email[:3] + "***" + pending_email[pending_email.index("@"):] if "@" in pending_email else pending_email
        st.info(f"Un code de verification a 6 chiffres a ete envoye a **{masked}**")

        with st.form("otp_form", clear_on_submit=False):
            otp_input = st.text_input("Code de verification", max_chars=6, key="otp_input", placeholder="123456")
            verify_btn = st.form_submit_button("\u2705 Verifier le code", type="primary", width="stretch")

        if verify_btn and otp_input:
            if otp_input == st.session_state.get("otp_code"):
                if _time.time() < st.session_state.get("otp_expiry", 0):
                    st.session_state.authenticated = True
                    st.session_state.pending_2fa = False
                    for k in ["otp_code", "otp_expiry", "pending_email"]:
                        st.session_state.pop(k, None)
                    st.success("Verification reussie !")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Code expire. Veuillez vous reconnecter.")
                    st.session_state.pending_2fa = False
                    st.session_state.authenticated = False
            else:
                st.error("Code incorrect. Veuillez reessayer.")

        col_resend, col_back = st.columns(2)
        with col_resend:
            if st.button("\U0001f504 Renvoyer le code", width="stretch"):
                new_code = _generate_otp()
                st.session_state.otp_code = new_code
                st.session_state.otp_expiry = _time.time() + 300
                sent = _send_otp(st.session_state.get("pending_email", ""), new_code)
                if sent:
                    st.success("Nouveau code envoye !")
                else:
                    st.warning(f"Code : **{new_code}** (email non configure)")
        with col_back:
            if st.button("\u21a9\ufe0f Retour", width="stretch"):
                st.session_state.pending_2fa = False
                st.session_state.authenticated = False
                for k in ["otp_code", "otp_expiry", "pending_email"]:
                    st.session_state.pop(k, None)
                st.rerun()

    # --- Mode connexion normal ---
    else:
        with st.form("login_form", clear_on_submit=False):
            st.markdown("### Connectez-vous a votre compte")
            email = st.text_input("Email", placeholder="votre@email.fr", key="login_email")
            password = st.text_input("Mot de passe", type="password", placeholder="", key="login_pwd")

            submitted = st.form_submit_button("Se connecter", type="primary", width="stretch")

        if submitted:
            if not email or not password:
                st.error("Veuillez remplir tous les champs.")
            else:
                with st.spinner("Connexion en cours..."):
                    result = login_user(email, password)
                if result["success"]:
                    otp_code = _generate_otp()
                    st.session_state.authenticated = False
                    st.session_state.pending_2fa = True
                    st.session_state.pending_email = email
                    st.session_state.otp_code = otp_code
                    st.session_state.otp_expiry = _time.time() + 300
                    sent = _send_otp(email, otp_code)
                    if not sent:
                        st.session_state.otp_fallback = True
                    st.rerun()
                else:
                    st.error(result["message"])
    # Afficher le code si email non configure (fallback)
    if st.session_state.get("pending_2fa") and st.session_state.get("otp_fallback"):
        st.warning(f"\u26a0\ufe0f Email non configure. Votre code : **{st.session_state.get('otp_code', '')}**")
        st.caption("Configurez SMTP_EMAIL et SMTP_PASSWORD sur le serveur pour l'envoi automatique.")


    st.markdown("""
    <div style="text-align:center;margin-top:1rem;font-size:0.85rem;color:#6B7280;">
        Pas encore de compte ? Cliquez sur l'onglet <strong>"Créer un compte"</strong> ci-dessus.
    </div>
    """, unsafe_allow_html=True)

#  Inscription 
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
        reg_pwd2 = st.text_input("Confirmer le mot de passe", type="password", placeholder="Rétapez votre mot de passe", key="reg_pwd2")

        st.markdown("""
        <div style="font-size:0.8rem;color:#6B7280;margin:0.5rem 0;">
            En crant un compte, vous acceptez nos <a href="#" target="_blank">Conditions d'utilisation</a>
            et notre <a href="#" target="_blank">Politique de confidentialit</a>.
        </div>
        """, unsafe_allow_html=True)

        submitted = st.form_submit_button("Créer mon compte", type="primary", width="stretch")

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
                        st.info(" Vrifiez votre bote mail pour confirmer votre inscription, puis connectez-vous.")
                    else:
                        st.error(result["message"])

#  Reset password 
with tab_reset:
    with st.form("reset_form", clear_on_submit=True):
        st.markdown("#### Rinitialiser votre mot de passe")
        st.markdown("Entrez votre email et nous vous enverrons un lien de rinitialisation.")

        reset_email = st.text_input("Email", placeholder="votre@email.fr", key="reset_email")
        submitted = st.form_submit_button("Envoyer le lien", type="primary", width="stretch")

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

#  Footer 
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#9CA3AF;font-size:0.8rem;">
    ConducteurPro v3.0  Propulsé par Claude AI   2026 ConducteurPro
</div>
""", unsafe_allow_html=True)

# 🏷️ Footer
st.markdown("""
<div class="login-footer">
    <p><strong>ConducteurPro</strong> — Logiciel professionnel pour conducteurs de travaux</p>
    <p>© 2026 ConducteurPro. Tous droits réservés.</p>
</div>
""", unsafe_allow_html=True)
