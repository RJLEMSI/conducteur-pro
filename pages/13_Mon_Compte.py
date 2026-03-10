import streamlit as st
from lib.helpers import page_setup
from lib.auth import get_user_profile, update_user_profile

page_setup()
user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Veuillez vous connecter.")
    st.stop()

st.markdown("## 👤 Mon Compte")

profile = get_user_profile(user_id) or {}

st.markdown("### Informations personnelles")

with st.form("profile_form"):
    display_name = st.text_input("Nom complet", value=profile.get("display_name", ""))
    company_name = st.text_input("Entreprise", value=profile.get("company_name", ""))
    siret = st.text_input("SIRET", value=profile.get("siret", ""))
    phone = st.text_input("Téléphone", value=profile.get("phone", ""))
    address = st.text_input("Adresse", value=profile.get("address", ""))
    
    submitted = st.form_submit_button("Mettre à jour")
    if submitted:
        updates = {
            "display_name": display_name,
            "company_name": company_name,
            "siret": siret,
            "phone": phone,
            "address": address,
        }
        if update_user_profile(user_id, updates):
            st.success("Profil mis à jour !")
            st.rerun()
        else:
            st.error("Erreur lors de la mise à jour.")

st.markdown("---")
st.markdown("### Informations du compte")
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**Email :** {profile.get('email', 'N/A')}")
    st.markdown(f"**Plan :** {profile.get('subscription_plan', 'free').capitalize()}")
with col2:
    st.markdown(f"**Membre depuis :** {str(profile.get('created_at', 'N/A'))[:10]}")
    st.markdown(f"**Stockage :** {profile.get('storage_limit_gb', 0)} Go")

st.markdown("---")
st.markdown("### Déconnexion")
if st.button("Se déconnecter", type="secondary"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
