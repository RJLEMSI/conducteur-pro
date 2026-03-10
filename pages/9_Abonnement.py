import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from datetime import datetime
from lib.helpers import page_setup, render_saas_sidebar
from lib import db
from lib.auth import get_plan_display, PLAN_LIMITS
from utils import GLOBAL_CSS

user_id = page_setup(title="Abonnement", icon="*")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.title("Mon Abonnement")

profile = db.get_profile(user_id)
current_plan = profile.get("subscription_plan", "free") if profile else "free"
plan_info = get_plan_display(current_plan)

# --- Plan actuel ---
st.subheader("Plan actuel: " + plan_info["name"])
st.markdown("**Prix:** " + plan_info["price"])
st.markdown("**Fonctionnalites incluses:**")
for f in plan_info["features"]:
    st.markdown(f"- {f}")

st.divider()

# --- Plans disponibles ---
st.subheader("Plans disponibles")

col1, col2 = st.columns(2)
plans = ["free", "pro"]

for i, (col, plan_key) in enumerate(zip([col1, col2], plans)):
    info = get_plan_display(plan_key)
    with col:
        is_current = plan_key == current_plan
        st.markdown("### " + info["name"])
        st.markdown("**" + info["price"] + "**")
        for feat in info["features"]:
            st.markdown(f"- {feat}")
        
        if is_current:
            st.success("Plan actuel")
        elif plan_key == "free":
            if st.button("Retrograder", key=f"plan_{plan_key}"):
                st.warning("Contactez le support pour retrograder.")
        else:
            if st.button("Passer au plan " + info["name"], key=f"plan_{plan_key}", type="primary"):
                try:
                    import stripe
                    stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
                    
                    price_id = st.secrets.get(f"STRIPE_PRICE_{plan_key.upper()}", "")
                    if not price_id:
                        st.error("Configuration Stripe manquante.")
                        st.stop()
                    
                    session = stripe.checkout.Session.create(
                        payment_method_types=["card"],
                        line_items=[{"price": price_id, "quantity": 1}],
                        mode="subscription",
                        success_url=st.secrets.get("APP_URL", "https://deva8r5poktveiufcmdppb.streamlit.app") + "?payment=success",
                        cancel_url=st.secrets.get("APP_URL", "https://deva8r5poktveiufcmdppb.streamlit.app") + "?payment=cancel",
                        client_reference_id=user_id,
                        metadata={"user_id": user_id, "plan": plan_key}
                    )
                    
                    st.markdown(f'<a href="{session.url}" target="_blank"><button style="background:#0066cc;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer;">Finaliser le paiement</button></a>', unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Erreur Stripe: {str(e)}")

st.divider()
st.caption("Les paiements sont securises par Stripe. Vous pouvez annuler a tout moment.")
