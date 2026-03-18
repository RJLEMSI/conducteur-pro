import streamlit as st
import os

try:
    from lib.stripe_config import init_stripe, get_stripe_mode, create_customer_portal
    init_stripe()
except Exception:
    pass

from lib.auth import require_auth, get_plan_display, PLAN_LIMITS
from lib.db import get_profile

auth = require_auth()
if not auth:
    st.stop()

user_id  = st.session_state.get("user_id")
user_email = st.session_state.get("user_email", "")
profile  = get_profile(user_id)
current_plan = (profile or {}).get("subscription_plan", "free")

st.markdown("""<style>
.pricing-container { display:flex; gap:20px; justify-content:center; flex-wrap:wrap; margin:30px 0; }
.pricing-card {
    background:white; border-radius:16px; padding:28px 24px; width:270px;
    box-shadow:0 4px 20px rgba(0,0,0,0.08); border:2px solid #e8ecf1;
    position:relative; transition:transform 0.3s,box-shadow 0.3s;
}
.pricing-card:hover { transform:translateY(-8px); box-shadow:0 12px 40px rgba(0,0,0,0.15); }
.pricing-card.popular { border-color:#1B4F72; background:linear-gradient(180deg,#f0f7ff 0%,white 30%); }
.pricing-card.enterprise { border-color:#7B2FBE; background:linear-gradient(180deg,#faf5ff 0%,white 30%); }
.popular-badge {
    position:absolute; top:-14px; left:50%; transform:translateX(-50%);
    background:linear-gradient(135deg,#1B4F72,#2E86C1); color:white;
    padding:5px 18px; border-radius:20px; font-size:12px; font-weight:600; white-space:nowrap;
}
.enterprise-badge {
    position:absolute; top:-14px; left:50%; transform:translateX(-50%);
    background:linear-gradient(135deg,#7B2FBE,#A855F7); color:white;
    padding:5px 18px; border-radius:20px; font-size:12px; font-weight:600; white-space:nowrap;
}
.current-badge {
    position:absolute; top:-14px; right:16px;
    background:#27AE60; color:white; padding:4px 12px; border-radius:12px; font-size:11px; font-weight:600;
}
.plan-icon { font-size:36px; margin-bottom:6px; }
.plan-name { font-size:20px; font-weight:700; color:#1B4F72; margin:4px 0; }
.plan-price { font-size:34px; font-weight:800; color:#2C3E50; margin:10px 0 4px; }
.plan-price .period { font-size:14px; font-weight:400; color:#7f8c8d; }
.feature-list { list-style:none; padding:0; margin:16px 0; }
.feature-list li { padding:6px 0; font-size:13px; color:#34495e; border-bottom:1px solid #f0f0f0; display:flex; align-items:center; gap:6px; }
.feature-list li:last-child { border-bottom:none; }
.feat-yes { color:#27AE60; font-weight:bold; }
.feat-no  { color:#e74c3c; }
.section-title { text-align:center; font-size:30px; font-weight:700; color:#1B4F72; margin-bottom:6px; }
.section-subtitle { text-align:center; font-size:15px; color:#7f8c8d; margin-bottom:28px; }
.guarantee-box {
    background:linear-gradient(135deg,#f8f9fa,#e8f4f8); border-radius:12px;
    padding:20px; text-align:center; margin:36px auto; max-width:700px; border:1px solid #d5e8f0;
}
</style>""", unsafe_allow_html=True)

st.markdown('<p class="section-title">Choisissez votre formule</p>', unsafe_allow_html=True)
st.markdown('<p class="section-subtitle">Des outils professionnels pour piloter vos chantiers efficacement</p>', unsafe_allow_html=True)

plan_names  = {"free": "D\u00e9couverte", "pro": "Pro", "team": "\u00c9quipe Pro", "enterprise": "\u00c9quipe Premium"}
plan_icons  = {"free": "\U0001f331", "pro": "\u2b50", "team": "\U0001f680", "enterprise": "\U0001f451"}
plan_colors = {"free": "#95a5a6", "pro": "#1B4F72", "team": "#8E44AD", "enterprise": "#7B2FBE"}

banner_name  = plan_names.get(current_plan, "D\u00e9couverte")
banner_icon  = plan_icons.get(current_plan, "\U0001f331")
banner_color = plan_colors.get(current_plan, "#95a5a6")
st.markdown(f'<div style="background:linear-gradient(135deg,{banner_color}15,{banner_color}08);border-left:4px solid {banner_color};border-radius:8px;padding:14px 20px;margin-bottom:28px;"><span style="font-size:17px;">{banner_icon} Votre abonnement actuel : <strong style="color:{banner_color};">{banner_name}</strong></span></div>', unsafe_allow_html=True)

plans = [
    {
        "key": "free", "name": "D\u00e9couverte", "icon": "\U0001f331", "price": "0", "period": "",
        "popular": False, "enterprise": False, "subtitle": "Pour d\u00e9couvrir la plateforme",
        "features": [
            ("\u2713", True,  "3 chantiers maximum"),
            ("\u2713", True,  "500 Mo de stockage"),
            ("\u2713", True,  "G\u00e9n\u00e9ration de devis PDF"),
            ("\u2713", True,  "Planning basique"),
            ("\u2717", False, "Modules ERP"),
            ("\u2717", False, "Analyse IA"),
            ("\u2717", False, "Import / Export"),
            ("\u2717", False, "Support prioritaire"),
        ]
    },
    {
        "key": "pro", "name": "Pro", "icon": "\u2b50", "price": "89", "period": "/mois",
        "popular": True, "enterprise": False, "subtitle": "Pour les ind\u00e9pendants BTP",
        "features": [
            ("\u2713", True, "50 chantiers"),
            ("\u2713", True, "100 Go de stockage"),
            ("\u2713", True, "Toutes les fonctionnalit\u00e9s"),
            ("\u2713", True, "Facturation professionnelle"),
            ("\u2713", True, "Modules ERP complets"),
            ("\u2713", True, "Analyse IA illimit\u00e9e"),
            ("\u2713", True, "Agent ERP IA"),
            ("\u2717", False, "Multi-utilisateurs"),
        ]
    },
    {
        "key": "team", "name": "\u00c9quipe Pro", "icon": "\U0001f680", "price": "179", "period": "/mois",
        "popular": False, "enterprise": False, "subtitle": "Pour les PME du BTP",
        "features": [
            ("\u2713", True, "500 chantiers"),
            ("\u2713", True, "500 Go de stockage"),
            ("\u2713", True, "Toutes les fonctionnalit\u00e9s"),
            ("\u2713", True, "4 utilisateurs simultan\u00e9s"),
            ("\u2713", True, "Modules ERP complets"),
            ("\u2713", True, "Analyse IA illimit\u00e9e"),
            ("\u2713", True, "Agent ERP IA"),
            ("\u2713", True, "Support prioritaire"),
        ]
    },
    {
        "key": "enterprise", "name": "\u00c9quipe Premium", "icon": "\U0001f451", "price": "279", "period": "/mois",
        "popular": False, "enterprise": True, "subtitle": "Pour les grandes entreprises BTP",
        "features": [
            ("\u2713", True, "Chantiers illimit\u00e9s"),
            ("\u2713", True, "Stockage illimit\u00e9"),
            ("\u2713", True, "Toutes les fonctionnalit\u00e9s"),
            ("\u2713", True, "10 utilisateurs simultan\u00e9s"),
            ("\u2713", True, "ERP + Agent IA prioritaire"),
            ("\u2713", True, "Analyse IA illimit\u00e9e"),
            ("\u2713", True, "Support d\u00e9di\u00e9 24/7"),
            ("\u2713", True, "Onboarding personnalis\u00e9"),
        ]
    },
]

cards_html = '<div class="pricing-container">'
for p in plans:
    extra_cls = ""
    badge = ""
    if p["enterprise"]:
        extra_cls = " enterprise"
        badge = '<div class="enterprise-badge">\U0001f451 Premium</div>'
    elif p["popular"]:
        extra_cls = " popular"
        badge = '<div class="popular-badge">Le plus populaire</div>'
    cur_badge = '<div class="current-badge">Actuel</div>' if p["key"] == current_plan else ""
    feats = ""
    for icon, ok, txt in p["features"]:
        cls = "feat-yes" if ok else "feat-no"
        feats += f'<li><span class="{cls}">{icon}</span> {txt}</li>'
    if p["price"] == "0":
        pr  = "0"
        per = '<span class="period">Gratuit</span>'
    else:
        pr  = f'{p["price"]}\u20ac'
        per = f'<span class="period">{p["period"]}</span>'
    cards_html += f'<div class="pricing-card{extra_cls}">{badge}{cur_badge}<div class="plan-icon">{p["icon"]}</div><div class="plan-name">{p["name"]}</div><div style="color:#7f8c8d;font-size:13px;">{p["subtitle"]}</div><div class="plan-price">{pr} {per}</div><ul class="feature-list">{feats}</ul></div>'
cards_html += "</div>"
st.markdown(cards_html, unsafe_allow_html=True)

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
stripe_key  = os.environ.get("STRIPE_SECRET_KEY", "")
price_pro   = st.secrets.get("STRIPE_PRICE_PRO", "")
price_team  = st.secrets.get("STRIPE_PRICE_TEAM", "")
price_ent   = st.secrets.get("STRIPE_PRICE_ENTERPRISE", "")

with col1:
    if current_plan != "free":
        if st.button("Revenir au gratuit", use_container_width=True):
            st.warning("Contactez le support pour modifier votre abonnement.")

with col2:
    if current_plan != "pro":
        if st.button("Pro — 89\u20ac/mois", use_container_width=True, type="primary"):
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
                except Exception:
                    st.error("Erreur paiement. Veuillez contacter le support.")
            else:
                st.info("Paiement Stripe en cours de configuration.")
    else:
        st.success("\u2705 Plan Pro actif")

with col3:
    if current_plan != "team":
        if st.button("\u00c9quipe Pro — 179\u20ac/mois", use_container_width=True):
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
                except Exception:
                    st.error("Erreur paiement. Veuillez contacter le support.")
            else:
                st.info("Paiement Stripe en cours de configuration.")
    else:
        st.success("\u2705 Plan \u00c9quipe Pro actif")

with col4:
    if current_plan != "enterprise":
        if st.button("\U0001f451 Premium — 279\u20ac/mois", use_container_width=True):
            if stripe_key and price_ent:
                try:
                    import stripe
                    stripe.api_key = stripe_key
                    session = stripe.checkout.Session.create(
                        payment_method_types=["card"],
                        line_items=[{"price": price_ent, "quantity": 1}],
                        mode="subscription",
                        success_url="https://deva8r5poktveiufcmdppb.streamlit.app/Abonnement?success=true",
                        cancel_url="https://deva8r5poktveiufcmdppb.streamlit.app/Abonnement?cancel=true",
                        client_reference_id=str(user_id),
                        customer_email=user_email,
                    )
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={session.url}">', unsafe_allow_html=True)
                except Exception:
                    st.error("Erreur paiement. Veuillez contacter le support.")
            else:
                st.info("Contactez-nous pour activer l'offre Premium : contact@conducteurpro.fr")
    else:
        st.success("\u2705 Plan \u00c9quipe Premium actif")

params = st.query_params
if params.get("success"):
    st.balloons()
    st.success("Paiement r\u00e9ussi ! Votre abonnement est maintenant actif.")
elif params.get("cancel"):
    st.warning("Paiement annul\u00e9. Vous pouvez r\u00e9essayer \u00e0 tout moment.")

st.markdown("---")
st.markdown('<p class="section-title" style="font-size:22px;">Questions fr\u00e9quentes</p>', unsafe_allow_html=True)
with st.expander("Puis-je changer de formule \u00e0 tout moment ?"):
    st.write("Oui, vous pouvez upgrader ou downgrader votre abonnement quand vous le souhaitez. Le changement prend effet imm\u00e9diatement.")
with st.expander("Mes donn\u00e9es sont-elles en s\u00e9curit\u00e9 ?"):
    st.write("Absolument. Tous vos fichiers sont chiffr\u00e9s (AES-256) et stock\u00e9s sur des serveurs s\u00e9curis\u00e9s en Europe.")
with st.expander("Quelle diff\u00e9rence entre \u00c9quipe Pro et \u00c9quipe Premium ?"):
    st.write("L'\u00c9quipe Premium inclut 10 utilisateurs simultan\u00e9s (contre 4), un support d\u00e9di\u00e9 24/7, un onboarding personnalis\u00e9 et un acc\u00e8s prioritaire \u00e0 l'Agent ERP IA.")
with st.expander("Quels moyens de paiement acceptez-vous ?"):
    st.write("Nous acceptons les cartes bancaires (Visa, Mastercard, Amex) via Stripe, s\u00e9curis\u00e9 PCI-DSS.")
with st.expander("Puis-je obtenir une facture pour mon entreprise ?"):
    st.write("Oui, une facture est automatiquement g\u00e9n\u00e9r\u00e9e pour chaque paiement.")

st.markdown('<div class="guarantee-box"><div style="font-size:28px;margin-bottom:6px;">\U0001f6e1\ufe0f</div><div style="font-size:17px;font-weight:600;color:#1B4F72;margin-bottom:6px;">Satisfaction garantie</div><div style="color:#5a6c7d;font-size:13px;">Chiffrement SSL \u2022 Stripe certifi\u00e9 PCI-DSS \u2022 Donn\u00e9es h\u00e9berg\u00e9es en Europe</div></div>', unsafe_allow_html=True)

try:
    from lib.stripe_config import get_stripe_mode
    with st.sidebar:
        mode = get_stripe_mode()
        if mode == "test":
            st.sidebar.warning("\u26a0\ufe0f Mode TEST Stripe")
        else:
            st.sidebar.success("\u2705 Mode PRODUCTION Stripe")
except Exception:
    pass
