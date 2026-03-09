import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from datetime import datetime
from lib.helpers import page_setup, render_saas_sidebar
from lib import db
from lib.auth import get_plan_display, PLAN_LIMITS
from utils import GLOBAL_CSS

user_id = page_setup(title="Abonnement", icon="💳")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.title("💳 Mon Abonnement")

profile = db.get_profile(user_id)
current_plan = profile.get("plan", "free") if profile else "free"
plan_info = get_plan_display(current_plan)

# ─── Plan actuel ──────────────────────────────────────────────────────────────
st.subheader(f"{plan_info['icon']} Plan actuel: {plan_info['name']}")
st.markdown(f"**Prix:** {plan_info['price']}")
st.markdown("**Fonctionnalités incluses:**")
for f in plan_info["features"]:
    st.markdown(f"- ✅ {f}")

st.markdown("---")

# ─── Changer de plan ──────────────────────────────────────────────────────────
st.subheader("🔄 Changer de plan")

col1, col2, col3 = st.columns(3)

plans = ["free", "pro", "team"]
for i, (col, plan_key) in enumerate(zip([col1, col2, col3], plans)):
    info = get_plan_display(plan_key)
    with col:
        is_current = plan_key == current_plan
        st.markdown(f"### {info['icon']} {info['name']}")
        st.markdown(f"**{info['price']}**")
        for feat in info["features"]:
            st.markdown(f"- {feat}")
        
        if is_current:
            st.success("✅ Plan actuel")
        elif plan_key == "free":
            if st.button("Rétrograder", key=f"plan_{plan_key}"):
                st.warning("Contactez le support pour rétrograder.")
        else:
            if st.button(f"Passer au plan {info['name']}", key=f"plan_{plan_key}", type="primary"):
                try:
                    import stripe
                    stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
                    
                    price_id = st.secrets.get(f"STRIPE_PRICE_{plan_key.upper()}", "")
                    if not price_id:
                        st.error("Configuration Stripe manquante.")
                        st.stop()
                    
                    session = stripe.checkout.Session.create(
                        mode="subscription",
                        payment_method_types=["card"],
                        line_items=[{"price": price_id, "quantity": 1}],
                        success_url=st.secrets.get("APP_URL", "") + "?payment=success",
                        cancel_url=st.secrets.get("APP_URL", "") + "?payment=cancel",
                        metadata={"user_id": user_id, "plan": plan_key},
                        customer_email=profile.get("email", "") if profile else "",
                    )
                    st.markdown(f"[🔗 Procéder au paiement]({session.url})")
                except Exception as e:
                    st.error(f"Erreur Stripe: {e}")

# ─── Historique ───────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📜 Historique")
sub = db.get_subscription(user_id)
if sub:
    st.json(sub)
else:
    st.info("Aucun abonnement payant actif.")
