import streamlit as st
import os

st.set_page_config(page_title="ConducteurPro Mon Compte", page_icon="\U0001f464", layout="wide")

from lib.auth import require_auth, get_plan_display, PLAN_LIMITS
from lib.db import get_profile
from lib.supabase_client import get_supabase_client

auth = require_auth()
if not auth:
    st.stop()

user_id = st.session_state.get("user_id")
user_email = st.session_state.get("user_email", "")
profile = get_profile(user_id) or {}
current_plan = profile.get("subscription_plan", "free")

# --- CSS ---
st.markdown("""<style>
.account-card { background:white; border-radius:12px; padding:24px; box-shadow:0 2px 12px rgba(0,0,0,0.06); border:1px solid #e8ecf1; margin-bottom:20px; }
.account-header { display:flex; align-items:center; gap:16px; margin-bottom:24px; padding-bottom:16px; border-bottom:2px solid #f0f4f8; }
.avatar-circle { width:64px; height:64px; border-radius:50%; background:linear-gradient(135deg,#1B4F72,#2E86C1); display:flex; align-items:center; justify-content:center; color:white; font-size:28px; font-weight:700; }
.account-name { font-size:24px; font-weight:700; color:#1B4F72; }
.account-email { font-size:14px; color:#7f8c8d; }
.plan-badge { display:inline-block; padding:4px 12px; border-radius:16px; font-size:12px; font-weight:600; }
.section-label { font-size:18px; font-weight:600; color:#1B4F72; margin-bottom:12px; }
.stat-row { display:flex; gap:16px; flex-wrap:wrap; }
.stat-box { flex:1; min-width:150px; background:#f8fafc; border-radius:10px; padding:16px; text-align:center; border:1px solid #e8ecf1; }
.stat-value { font-size:24px; font-weight:700; color:#1B4F72; }
.stat-label { font-size:12px; color:#7f8c8d; margin-top:4px; }
</style>""", unsafe_allow_html=True)

# --- Header ---
display_name = profile.get("display_name", "") or user_email.split("@")[0]
company = profile.get("company_name", "") or ""
initials = "".join([w[0].upper() for w in display_name.split()[:2]]) if display_name else "?"
plan_info = get_plan_display(current_plan)
plan_colors = {"free": "#95a5a6", "pro": "#1B4F72", "team": "#8E44AD"}
plan_names = {"free": "Découverte", "pro": "Pro", "team": "Équipe"}
pc = plan_colors.get(current_plan, "#95a5a6")
pn = plan_names.get(current_plan, "Découverte")

st.markdown(f'<div class="account-header"><div class="avatar-circle">{initials}</div><div><div class="account-name">{display_name}</div><div class="account-email">{user_email}</div><span class="plan-badge" style="background:{pc}20;color:{pc};">Plan {pn}</span></div></div>', unsafe_allow_html=True)

# --- Stats ---
from lib import storage, db as db_module
try:
    usage = storage.get_storage_usage(user_id=user_id)
    nb_docs = usage.get("nb_documents", 0)
    total_mb = usage.get("total_bytes", 0) / 1024 / 1024
except Exception:
    nb_docs = 0
    total_mb = 0

try:
    chantiers = db_module.get_chantiers(user_id) or []
    nb_chantiers = len(chantiers)
except Exception:
    nb_chantiers = 0

st.markdown(f'<div class="stat-row"><div class="stat-box"><div class="stat-value">{nb_chantiers}</div><div class="stat-label">Chantiers</div></div><div class="stat-box"><div class="stat-value">{nb_docs}</div><div class="stat-label">Documents</div></div><div class="stat-box"><div class="stat-value">{total_mb:.1f} Mo</div><div class="stat-label">Stockage utilisé</div></div><div class="stat-box"><div class="stat-value">{pn}</div><div class="stat-label">Abonnement</div></div></div>', unsafe_allow_html=True)

st.markdown("")

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["Profil & Entreprise", "Sécurité", "Abonnement"])

with tab1:
    st.markdown('<p class="section-label">Informations personnelles</p>', unsafe_allow_html=True)
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            display_name_input = st.text_input("Nom complet", value=profile.get("display_name", "") or "")
            phone = st.text_input("Téléphone", value=profile.get("phone", "") or "")
        with col2:
            company_name = st.text_input("Nom de l entreprise", value=profile.get("company_name", "") or "")
            siret = st.text_input("SIRET", value=profile.get("siret", "") or "")
        address = st.text_input("Adresse complète", value=profile.get("address", "") or "")
        
        submitted = st.form_submit_button("Enregistrer les modifications", type="primary", use_container_width=True)
        if submitted:
            updates = {
                "display_name": display_name_input,
                "company_name": company_name,
                "siret": siret,
                "phone": phone,
                "address": address,
            }
            try:
                client = get_supabase_client()
                client.table("user_profiles").update(updates).eq("user_id", user_id).execute()
                st.success("Profil mis a jour avec succes !")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la mise a jour : {e}")

with tab2:
    st.markdown('<p class="section-label">Modifier le mot de passe</p>', unsafe_allow_html=True)
    st.info("Pour modifier votre mot de passe, utiliséz la fonction \"Mot de passe oublie\" sur la page de connexion.")
    if st.button("Aller a la page de connexion", use_container_width=True):
        st.switch_page("pages/00_Connexion.py")
    
    st.markdown("---")
    st.markdown('<p class="section-label">Informations du compte</p>', unsafe_allow_html=True)
    st.markdown(f"**Email :** {user_email}")
    st.markdown(f"**Identifiant :** `{user_id[:8]}...`")
    
    st.markdown("---")
    st.markdown('<p class="section-label" style="color:#e74c3c;">Zone dangereuse</p>', unsafe_allow_html=True)
    st.warning("La suppression du compte est irreversible et entrainera la perte de toutes vos données.")
    if st.button("Supprimer mon compte", type="secondary"):
        st.error("Pour supprimér votre compte, contactez le support a contact@conducteurpro.fr")

with tab3:
    st.markdown('<p class="section-label">Votre abonnement</p>', unsafe_allow_html=True)
    limits = PLAN_LIMITS.get(current_plan, {})
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Plan actuel", pn)
        st.metric("Chantiers max", limits.get("max_chantiers", 3))
    with col2:
        price = {"free": "Gratuit", "pro": "65,90\u20ac/mois", "team": "119,60\u20ac/mois"}
        st.metric("Prix", price.get(current_plan, "Gratuit"))
        st.metric("Stockage max", limits.get("storage_label", "500 Mo"))
    
    st.markdown("")
    if current_plan == "free":
        if st.button("Passer au Pro", type="primary", use_container_width=True):
            st.switch_page("pages/9_Abonnement.py")
    elif current_plan == "pro":
        if st.button("Passer a Équipe", type="primary", use_container_width=True):
            st.switch_page("pages/9_Abonnement.py")
    else:
        st.success("Vous avez le plan le plus complet !")
    
    st.markdown("")
    st.caption("Gerez votre abonnement et vos paiements sur la page Abonnement.")