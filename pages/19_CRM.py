import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import json
from datetime import datetime, date, timedelta
from collections import Counter
from lib.helpers import page_setup, render_saas_sidebar, require_feature
from lib.supabase_client import get_client
from utils import GLOBAL_CSS

user_id = page_setup("CRM", icon="💼")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)
require_feature(user_id, "crm")

sb = get_client()

# Status color mapping
STATUS_COLORS = {
    "nouveau": "#9e9e9e",
    "contacte": "#2196f3",
    "devis_envoye": "#ff9800",
    "relance": "#ffc107",
    "gagne": "#4caf50",
    "perdu": "#f44336"
}

STATUS_LABELS = {
    "nouveau": "Nouveau",
    "contacte": "Contacté",
    "devis_envoye": "Devis envoyé",
    "relance": "Relance",
    "gagne": "Gagné",
    "perdu": "Perdu"
}

# Fetch prospects for user
@st.cache_data(ttl=60)
def get_prospects():
    response = sb.table("prospects").select("*").eq("user_id", user_id).execute()
    return response.data if response.data else []

# Helper functions
def update_prospect_status(prospect_id, new_status):
    sb.table("prospects").update({"statut": new_status}).eq("id", prospect_id).execute()
    st.cache_data.clear()

def delete_prospect(prospect_id):
    sb.table("prospects").delete().eq("id", prospect_id).execute()
    st.cache_data.clear()

def add_prospect(data):
    sb.table("prospects").insert(data).execute()
    st.cache_data.clear()

def convert_to_chantier(prospect):
    chantier_data = {
        "user_id": user_id,
        "nom_chantier": prospect.get("nom", ""),
        "client_nom": prospect.get("contact_nom", ""),
        "adresse": prospect.get("adresse", ""),
        "type_travaux": prospect.get("type_projet", ""),
        "devis_montant": prospect.get("budget_estime", 0),
        "statut": "devis_signe",
        "date_debut": datetime.now().isoformat(),
        "notes": prospect.get("notes", "")
    }
    sb.table("chantiers").insert(chantier_data).execute()
    delete_prospect(prospect["id"])
    st.cache_data.clear()
    st.success(f"Prospect '{prospect['nom']}' converti en chantier ✓")

# TAB 1: Pipeline Commercial
with st.container():
    tab1, tab2, tab3 = st.tabs(["📊 Pipeline Commercial", "👥 Gestion Prospects", "📈 Statistiques"])

    with tab1:
        st.header("Pipeline Commercial")
        prospects = get_prospects()

        if not prospects:
            st.info("Aucun prospect actuellement. Créez en bor): prospect actuellement. Créez en dans l'onglet Gestion Prospects.")
        else:
            # Organize prospects by status
            pipeline = {status: [] for status in STATUS_COLORS.keys()}
            for p in prospects:
                status = p.get("statut", "nouveau")
                if status in pipeline:
                    pipeline[status].append(p)

            # Display columns
            cols = st.columns(len(STATUS_COLORS))
            for col_idx, (status, color) in enumerate(STATUS_COLORS.items()):
                with cols[col_idx]:
                    prospects_in_status = pipeline[status]
                    total_budget = sum(p.get("budget_estime", 0) for p in prospects_in_status)

                    st.markdown(
                        f"<div style='background-color:{color}; padding:10px; border-radius:5px; color:white; text-align:center; margin-bottom:10px;'>"
                        f"<b>{STATUS_LABELS[status]}</b><br/>"
                        f"{len(prospects_in_status)} prospect(s) | {total_budget:,.0f}€"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                    for prospect in prospects_in_status:
                        with st.expander(
                            f"🏢 {prospect.get('nom', 'Sans nom')} - {prospect.get('budget_estime', 0):,.0f}€"
                        ):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Contact:** {prospect.get('contact_nom', 'N/A')}")
                                st.write(f"**Email:** {prospect.get('email', 'N/A')}")
                                st.write(f"**Téléphone:** {prospect.get('telephone', 'N/A')}")
                            with col2:
                                st.write(f"**Type projet:** {prospect.get('type_projet', 'N/A')}")
                                st.write(f"**Date contact:** {prospect.get('date_premier_contact', 'N/A')}")
                                st.write(f"**Source:** {prospect.get('source', 'N/A')}")

                            st.write(f"**Notes:** {prospect.get('notes', '')}")

                            new_status = st.selectbox(
                                "Changer le statut",
                                options=list(STATUS_COLORS.keys()),
                                format_func=lambda x: STATUS_LABELS[x],
                                index=list(STATUS_COLORS.keys()).index(status),
                                key=f"status_{prospect['id']}"
                            )
                            if new_status != status:
                                update_prospect_status(prospect["id"], new_status)
                                st.success(f"Statut mis à jour ✓")
                                st.rerun()

    # TAB 2: Gestion Prospects
    with tab2:
        st.header("Gestion Prospects")

        sub_tab1, sub_tab2 = st.tabs(["Ajouter un prospect", "Liste des prospects"])

        with sub_tab1:
            with st.form("nouveau_prospect_form"):
                col1, col2 = st.columns(2)
                with col1:
                    nom = st.text_input("Nom de l'entreprise", placeholder="ex: ABC Bâ��timent")
                    contact_nom = st.text_input("Nom du contact", placeholder="ex: Jean Dupont")
                    email = st.text_input("Email", placeholder="contact@example.com")
                with col2:
                    telephone = st.text_input("Téléphone", placeholder="06 XX XX XX XX")
                    adresse = st.text_input("Adresse", placeholder="123 Rue de la Paix, 75000 Paris")

                col1, col2 = st.columns(2)
                with col1:
                    source = st.selectbox("Source du prospect", ["appel", "site_web", "recommandation", "salon", "autre"])
                    type_project = st.text_input("Type de projet", placeholder="ex: Rénovation toiture")
                with col2:
                    budget_estime = st.number_input("Budget estimé (€)", min_value=0, step=500, value=5000)

                notes = st.text_area("Notes", placeholder="Informations supplémentaires...")

                if st.form_submit_button("Ajouter le prospect"):
                    if nom and contact_nom and email:
                        prospect_data = {
                            "user_id": user_id,
                            "nom": nom,
                            "contact_nom": contact_nom,
                            "email": email,
                            "telephone": telephone,
                            "adresse": adresse,
                            "source": source,
                            "type_projet": type_projet,
                            "budget_estime": budget_estime,
                            "notes": notes,
                            "statut": "nouveau",
                            "date_premier_contact": datetime.now().isoformat(),
                            "date_relance": (datetime.now() + timedelta(days=7)).isoformat()
                        }
                        add_prospect(prospect_data)
                        st.success(f"Prospect '{nom}' ajouté avec succès ✓")
                    else:
                        st.error("Veuillez remplir au moins: Nom, Contact et Email")

        with sub_tab2:
            prospects = get_prospects()

            if not prospects:
                st.info("Aucun prospect. Créez-en un dans l'onglet précédent.")
            else:
                # Sort by date
                sorted_prospects = sorted(prospects, key=lambda x: x.get("date_premier_contact", ""), reverse=True)

                for prospect in sorted_prospects:
                    with st.expander(
                        f"{'🔴' if prospect.get('statut') == 'perdu' else '🟢' if prospect.get('statut') == 'gagne' else '⚪'} "
                        f"{prospect['nom']} | {STATUS_LABELS.get(prospect.get('statut', 'nouveau'), 'N/A')} | {prospect.get('budget_estime', 0):,.0f}€"
                    ):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Contact:** {prospect.get('contact_nom', '')}")
                            st.write(f"**Email:** {prospect.get('email', '')}")
                            st.write(f"**Tél:** {prospect.get('telephone', '')}")
                        with col2:
                            st.write(f"**Adresse:** {prospect.get('adresse', '')}")
                            st.write(f"**Source:** {prospect.get('source', '')}")
                            st.write(f"**Type:** {prospect.get('type_projet', '')}")
                        with col3:
                            st.write(f"**Budget:** {prospect.get('budget_estime', 0):,.0f}€")
                            st.write(f"**Premier contact:** {prospect.get('date_premier_contact', 'N/A')}")

                            # Relance alert
                            date_relance = prospect.get("date_relance")
                            if date_relance:
                                relance_date = datetime.fromisoformat(date_relance).date()
                                today = date.today()
                                if relance_date <= today:
                                    st.markdown(
                                        f"<span style='color: red; font-weight: bold;'>⚠️ Relance: {relance_date}</span>",
                                        unsafe_allow_html=True
                                    )
                                else:
                                    st.write(f"📅 Relance: {relance_date}")

                        st.write(f"**Notes:** {prospect.get('notes', '')}")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("✏️ Modifier", key=f"edit_{prospect['id']}"):
                                st.info("Modification non disponible actuellement - utilisez le Pipeline pour changer le statut")
                        with col2:
                            if prospect.get("statut") == "gagne":
                                if st.button("✅ Convertir en chantier", key=f"convert_{prospect['id']}"):
                                    convert_to_chantier(prospect)
                                    st.rerun()
                        with col3:
                            if st.button("🗑️ Supprimer", key=f"delete_{prospect['id']}"):
                                delete_prospect(prospect["id"])
                                st.success("Prospect supprimé ✓")
                                st.rerun()

    # TAB 3: Statistiques
    with tab3:
        st.header("Statistiques CRM")
        prospects = get_prospects()

        if not prospects:
            st.info("Aucune donnée pour afficher les statistiques.")
        else:
            # KPIs
            col1, col2, col3, col4 = st.columns(4)

            total_prospects = len(prospects)
            prospects_gagne = [p for p in prospects if p.get("statut") == "gagne"]
            taux_conversion = (len(prospects_gagne) / total_prospects * 100) if total_prospects > 0 else 0
            ca_potentiel = sum(p.get("budget_estime", 0) for p in prospects)
            ca_gagne = sum(p.get("budget_estime", 0) for p in prospects_gagne)

            with col1:
                st.metric("Prospects totaux", total_prospects)
            with col2:
                st.metric("Taux conversion", f"{taux_conversion:.1f}%")
            with col3:
                st.metric("CA potentiel", f"{ca_potentiel:,.0f}€")
            with col4:
                st.metric("CA gagné", f"{ca_gagne:,.0f}€")

            st.divider()

            # Funnel
            col1, col2 = st.columns(2)

            with col1:
                st.subheader* ���� Funnel de conversion")
                funnel_data = {}
                for status in ["nouveau", "contacte", "devis_envoye", "relance", "gagne"]:
                    count = len([p for p in prospects if p.get("statut") == status])
                    funnel_data[STATUS_LABELS[status]] = count

                for stage, count in funnel_data.items():
                    st.metric(stage, count)

            with col2:
                st.subheader* ���� Prospects par source")
                sources = Counter(p.get("source", "autre") for p in prospects)
                for source, count in sources.most_common():
                    st.metric(source, count)

            st.divider()

            # Relances à faire
            st.subheader*"⏰ Relances à faire")
            today = date.today()
            relances_a_faire = [
                p for p in prospects
                if p.get("date_relance") and datetime.fromisoformat(p["date_relance"]).date() <= today
                and p.get("statut") not in ["gagne", "perdu"]
            ]

            if relances_a_faire:
                for prospect in sorted(relances_a_faire, key=lambda x: x.get("date_relance", "")):
                    relance_date = datetime.fromisoformat(prospect["date_relance"]).date()
                    days_overdue = (today - relance_date).days
                    st.markdown(
                        f"<div style='background-color: #ffebee; padding: 10px; border-radius: 5px; margin: 5px 0;'>"
                        f"<b>{prospect['nom']}</b> - {prospect.get('contact_nom', '')} | "
                        f"<span style='color: red;'>⚠️ {days_overdue} jour(s) de retard</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
            else:
                st.success("Aucune relance en retard ✓")