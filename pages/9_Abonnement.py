import streamlit as st
import os

st.set_page_config(page_title="ConducteurPro Abonnement", page_icon="\u2b50", layout="wide")

from lib.auth import require_auth, get_plan_display, PLAN_LIMITS
from lib.db import get_profile

auth = require_auth()
if not auth:
    st.stop()

user_id = st.session_state.get("user_id")
user_email = st.session_state.get("user_email", "")
profile = get_profile(user_id)
current_plan = (profile or {}).get("subscription_plan", "free")

# --- CSS ---
st.markdown("""<style>
.pricing-container { display:flex; gap:24px; justify-content:center; flex-wrap:wrap; margin:30px 0; }
.pricing-card { background:white; border-radius:16px; padding:32px 28px; width:300px; box-shadow:0 4px 20px rgba(0,0,0,0.08); border:2px solid #e8ecf1; position:relative; transition:transform 0.3s,box-shadow 0.3s; }
.pricing-card:hover { transform:translateY(-8px); box-shadow:0 12px 40px rgba(0,0,0,0.15); }
.pricing-card.popular { border-color:#1B4F72; background:linear-gradient(180deg,#f0f7ff 0%,white 30%); }
.popular-badge { position:absolute; top:-14px; left:50%; transform:translateX(-50%); background:linear-gradient(135deg,#1B4F72,#2E86C1); color:white; padding:6px 20px; border-radius:20px; font-size:13px; font-weight:600; white-space:nowrap; }
.current-badge { position:absolute; top:-14px; right:20px; background:#27AE60; color:white; padding:4px 14px; border-radius:12px; font-size:12px; font-weight:600; }
.plan-icon { font-size:40px; margin-bottom:8px; }
.plan-name { font-size:22px; font-weight:700; color:#1B4F72; margin:4px 0; }
.plan-price { font-size:36px; font-weight:800; color:#2C3E50; margin:12px 0 4px; }
.plan-price .period { font-size:16px; font-weight:400; color:#7f8c8d; }
.feature-list { list-style:none; padding:0; margin:20px 0; }
.feature-list li { padding:8px 0; font-size:14px; color:#34495e; border-bottom:1px solid #f0f0f0; display:flex; align-items:center; gap:8px; }
.feature-list li:last-child { border-bottom:none; }
.feat-yes { color:#27AE60; font-weight:bold; }
.feat-no { color:#e74c3c; }
.section-title { text-align:center; font-size:32px; font-weight:700; color:#1B4F72; margin-bottom:8px; }
.section-subtitle { text-align:center; font-size:16px; color:#7f8c8d; margin-bottom:30px; }
.guarantee-box { background:linear-gradient(135deg,#f8f9fa,#e8f4f8); border-radius:12px; padding:24px; text-align:center; margin:40px auto; max-width:700px; border:1px solid #d5e8f0; }
</style>""", unsafe_allow_html=True)

st.markdown('<p class="section-title">Choisissez votre formule</p>', unsafe_allow_html=True)
st.markdown('<p class="section-subtitle">Des outils professionnels pour piloter vos chantiers efficacement</p>', unsafe_allow_html=True)

plan_names = {"free": "Découverte", "pro": "Pro", "team": "Équipe"}
plan_icons = {"free": "\U0001f331", "pro": "\u2b50", "team": "\U0001f680"}
plan_colors = {"free": "#95a5a6", "pro": "#1B4F72", "team": "#8E44AD"}
banner_name = plan_names.get(current_plan, "Découverte")
banner_icon = plan_icons.get(current_plan, "\U0001f331")
banner_color = plan_colors.get(current_plan, "#95a5a6")

st.markdown(f'<div style="background:linear-gradient(135deg,{banner_color}15,{banner_color}08);border-left:4px solid {banner_color};border-radius:8px;padding:16px 24px;margin-bottom:30px;"><span style="font-size:18px;">{banner_icon} Votre abonnement actuel : <strong style="color:{banner_color};">{banner_name}</strong></span></div>', unsafe_allow_html=True)

plans = [
    {"key": "free", "name": "Découverte", "icon": "\U0001f331", "price": "0", "period": "", "popular": False, "subtitle": "Pour tester la plateforme", "features": [("\u2713", True, "3 chantiers maximum"), ("\u2713", True, "500 Mo de stockage"), ("\u2713", True, "Génération de devis PDF"), ("\u2713", True, "Planning basique"), ("\u2717", False, "Import de données"), ("\u2717", False, "Facturation avancée"), ("\u2717", False, "Analyse IA"), ("\u2717", False, "Support prioritaire")]},
    {"key": "pro", "name": "Pro", "icon": "\u2b50", "price": "65,90", "period": "/mois", "popular": True, "subtitle": "Pour les indépendants", "features": [("\u2713", True, "50 chantiers"), ("\u2713", True, "100 Go de stockage"), ("\u2713", True, "Toutes les fonctionnalités"), ("\u2713", True, "Facturation professionnelle"), ("\u2713", True, "Import CSV / Excel"), ("\u2713", True, "Analyse IA illimitee"), ("\u2713", True, "Export PDF complet"), ("\u2717", False, "Multi-utilisateurs")]},
    {"key": "team", "name": "Équipe", "icon": "\U0001f680", "price": "119,60", "period": "/mois", "popular": False, "subtitle": "Pour les équipes", "features": [("\u2713", True, "500 chantiers"), ("\u2713", True, "500 Go de stockage"), ("\u2713", True, "Toutes les fonctionnalités"), ("\u2713", True, "4 utilisateurs simultanés"), ("\u2713", True, "Facturation avancée"), ("\u2713", True, "Analyse IA illimitee"), ("\u2713", True, "Support prioritaire"), ("\u2713", True, "Tableau de bord équipe")]},
]

cards_html = '<div class="pricing-container">'
for p in plans:
    pop_cls = " popular" if p["popular"] else ""
    pop_badge = '<div class="popular-badge">Le plus populaire</div>' if p["popular"] else ""
    cur_badge = '<div class="current-badge">Actuel</div>' if p["key"] == current_plan else ""
    feats = ""
    for icon, ok, txt in p["features"]:
        cls = "feat-yes" if ok else "feat-no"
        feats += f'<li><span class="{cls}">{icon}</span> {txt}</li>'
    if p["price"] == "0":
        pr = "0"
        per = '<span class="period">Gratuit</span>'
    else:
        pr = f'{p["price"]}\u20ac'
        per = f'<span class="period">{p["period"]}</span>'
    cards_html += f'<div class="pricing-card{pop_cls}">{pop_badge}{cur_badge}<div class="plan-icon">{p["icon"]}</div><div class="plan-name">{p["name"]}</div><div style="color:#7f8c8d;font-size:14px;">{p["subtitle"]}</div><div class="plan-price">{pr} {per}</div><ul class="feature-list">{feats}</ul></div>'
cards_html += "</div>"
st.markdown(cards_html, unsafe_allow_html=True)

st.markdown("---")
col1, col2, col3 = st.columns(3)
stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
price_pro = os.environ.get("STRIPE_PRICE_PRO", "")
price_team = os.environ.get("STRIPE_PRICE_TEAM", "")

with col1:
    if current_plan != "free":
        if st.button("Revenir au gratuit", use_container_width=True):
            st.warning("Contactez le support pour reclasser votre abonnement.")

with col2:
    if current_plan != "pro":
        if st.button("Passer au Pro - 65,90\u20ac/mois", use_container_width=True, type="primary"):
            if stripe_key and price_pro:
                try:
                    import stripe
                    stripe.api_key = stripe_key
                    session = stripe.checkout.Session.create(
                        payment_method_types=["card"],
                        line_items=[{"price": price_pro, "quantity": 1}],
                        mode="subscription",
                        success_url="https://deva8r5poktveiufcmdppb.streamlit.app/Abonnement?success=true",
                        cancel_url="https://deva8r5poktveiufcmdppb.streamlit.app/Abonnement?cancel=true",
                        client_reference_id=str(user_id),
                        customer_email=user_email,
                    )
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={session.url}">', unsafe_allow_html=True)
                except Exception as e:
                    st.error("Une erreur est survenue lors du paiement. Veuillez réessayer ou contacter le support.")
            else:
                st.info("Paiement Stripe en cours de configuration.")
    else:
        st.success("Vous etes sur le plan Pro")

with col3:
    if current_plan != "team":
        if st.button("Passer a Équipe - 119,60\u20ac/mois", use_container_width=True):
            if stripe_key and price_team:
                try:
                    import stripe
                    stripe.api_key = stripe_key
                    session = stripe.checkout.Session.create(
                        payment_method_types=["card"],
                        line_items=[{"price": price_team, "quantity": 1}],
                        mode="subscription",
                        success_url="https://deva8r5poktveiufcmdppb.streamlit.app/Abonnement?success=true",
                        cancel_url="https://deva8r5poktveiufcmdppb.streamlit.app/Abonnement?cancel=true",
                        client_reference_id=str(user_id),
                        customer_email=user_email,
                    )
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={session.url}">', unsafe_allow_html=True)
                except Exception as e:
                    st.error("Une erreur est survenue lors du paiement. Veuillez réessayer ou contacter le support.")
            else:
                st.info("Paiement Stripe en cours de configuration.")
    else:
        st.success("Vous etes sur le plan Équipe")

params = st.query_params
if params.get("success"):
    st.balloons()
    st.success("Paiement réussi ! Votre abonnement est maintenant actif.")
elif params.get("cancel"):
    st.warning("Paiement annule. Vous pouvez reessayer a tout moment.")

st.markdown("---")
st.markdown('<p class="section-title" style="font-size:24px;">Questions frequentes</p>', unsafe_allow_html=True)

with st.expander("Puis-je changer de formule a tout moment ?"):
    st.write("Oui, vous pouvez upgrader ou downgrader votre abonnement quand vous le souhaitez. Le changement prend effet immediatement.")

with st.expander("Mes données sont-elles en sécurité ?"):
    st.write("Absolument. Tous vos fichiers sont chiffres (AES-256) et stockes sur des serveurs sécurisés en Europe.")

with st.expander("Comment fonctionne la periode d essai ?"):
    st.write("La formule Découverte est gratuite et sans limite de temps. Vous pouvez tester avec 3 chantiers.")

with st.expander("Quels moyens de paiement acceptez-vous ?"):
    st.write("Nous acceptons les cartes bancaires (Visa, Mastercard, Amex) via Stripe.")

with st.expander("Puis-je obtenir une facture pour mon entreprise ?"):
    st.write("Oui, une facture est automatiquement générée pour chaque paiement.")

st.markdown('<div class="guarantee-box"><div style="font-size:32px;margin-bottom:8px;">\U0001f6e1\ufe0f</div><div style="font-size:18px;font-weight:600;color:#1B4F72;margin-bottom:8px;">Satisfaction garantie</div><div style="color:#5a6c7d;font-size:14px;">Chiffrement SSL | Stripe certifie PCI-DSS | Donnees hébergées en Europe</div></div>', unsafe_allow_html=True)