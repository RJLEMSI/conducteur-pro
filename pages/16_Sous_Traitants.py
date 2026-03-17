import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import json
from datetime import datetime, date
import pandas as pd
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib.supabase_client import get_client
from utils import GLOBAL_CSS

user_id = page_setup("Sous-Traitants", icon="🏗️")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)
require_feature(user_id, "sous_traitants")

def format_currency(val):
    """Format number in French currency style."""
    if val is None or val == '':
        return "0,00"
    try:
        return f"{float(val):,.2f}".replace(",", " ").replace(".", ",")
    except:
        return "0,00"

def get_fournisseurs_sous_traitance(user_id):
    """Fetch subcontractor vendors."""
    try:
        sb = get_client()
        result = sb.table("fournisseurs").select("id, nom").eq("user_id", user_id).eq("categorie", "sous-traitance").execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Erreur lors du chargement des fournisseurs: {str(e)}")
        return []

def get_sous_traitants(user_id, chantier_id):
    """Fetch subcontractors for a project."""
    try:
        sb = get_client()
        result = sb.table("sous_traitants").select("*").eq("user_id", user_id).eq("chantier_id", chantier_id).execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Erreur lors du chargement des sous-traitants: {str(e)}")
        return []

def get_factures_sous_traitants(user_id, chantier_id):
    """Fetch invoices from subcontractors."""
    try:
        sb = get_client()
        result = sb.table("factures_sous_traitants").select("*").eq("user_id", user_id).eq("chantier_id", chantier_id).execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Erreur lors du chargement des factures: {str(e)}")
        return []

def get_fournisseur_nom(fournisseur_id, fournisseurs):
    """Get fournisseur name by ID."""
    for f in fournisseurs:
        if f.get("id") == fournisseur_id:
            return f.get("nom", "Inconnu")
    return "Inconnu"

def render_status_badge(status):
    """Render status badge with color."""
    colors = {"actif": "green", "termine": "blue", "suspendu": "red"}
    color = colors.get(status, "gray")
    return f'<span style="background-color:{color}; color:white; padding:4px 8px; border-radius:4px; font-size:12px;">{status}</span>'

st.title("Gestion des Sous-Traitants")

chantier_id = chantier_selector(key="st_chantier")
if not chantier_id:
    st.info("Veuillez sélectionner un chantier")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📋 Contrats", "💰 Factures", "📊 Tableau de Bord"])

# ==================== TAB 1: CONTRATS ====================
with tab1:
    st.subheader("Contrats Sous-Traitants")

    fournisseurs = get_fournisseurs_sous_traitance(user_id)
    sous_traitants = get_sous_traitants(user_id, chantier_id)

    # Display existing contracts
    if sous_traitants:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("**Sous-Traitants Actifs**")
        with col2:
            tri = st.selectbox("Trier par:", ["Tous", "Actif", "Terminé", "Suspendu"], key="tri_st")

        filtered = sous_traitants
        if tri != "Tous":
            filtered = [st for st in sous_traitants if st.get("statut", "actif").lower() == tri.lower()]

        for st_item in filtered:
            with st.expander(f"🏢 {st_item.get('fournisseur_nom', 'Inconnu')} - {st_item.get('lot_concerne', 'N/A')}", expanded=False):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Montant Marché", f"{format_currency(st_item.get('montant_marche', 0))} €")
                with col2:
                    st.metric("Montant Facturé", f"{format_currency(st_item.get('montant_facture', 0))} €")
                with col3:
                    st.metric("Montant Payé", f"{format_currency(st_item.get('montant_paye', 0))} €")

                avancement = st_item.get('avancement_pct', 0) or 0
                st.progress(float(avancement) / 100, text=f"Avancement: {avancement}%")

                retenue = st_item.get('retenue_garantie', 0) or 0
                st.metric("Retenue de Garantie", f"{format_currency(retenue)} €")

                st.markdown(f"**DC4 Référence:** {st_item.get('dc4_reference', 'N/A')}")
                st.markdown(f"**Contrat Signé:** {✄ Oui' if st_item.get('contrat_signe') else 'z❌ Non'}")
                st.markdown(f"**Statut:** {render_status_badge(st_item.get('statut', 'actif'))}", unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Modifier", key=f"edit_{st_item.get('id')}"):
                        st.session_state[f"edit_st_{st_item.get('id')}"] = True

                with col2:
                    if st.button("🗑️ Supprimer", key=f"del_{st_item.get('id')}"):
                        try:
                            sb = get_client()
                            sb.table("sous_traitants").delete().eq("id", st_item.get("id")).execute()
                            st.success("Sous-traitant supprimé")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur: {str(e)}")
    else:
        st.info("Aucun sous-traitant pour ce chantier")

    # Add new subcontractor form
    st.divider()
    st.subheader("➕ Ajouter un Sous-Traitant")

    with st.form("form_nouveau_st"):
        col1, col2 = st.columns(2)

        with col1:
            fournisseur_id = st.selectbox(
                "Fournisseur",
                options=[f.get("id") for f in fournisseurs],
                format_func=lambda x: get_fournisseur_nom(x, fournisseurs),
                key="st_fournisseur"
            )

        with col2:
            lot = st.text_input("Lot Concerné", value="", key="st_lot")

        col1, col2 = st.columns(2)
        with col1:
            montant_marche = st.number_input("Montant Marché (€)", value=0.0, min_value=0.0, key="st_montant")

        with col2:
            retenue_pct = st.number_input("Retenue de Garantie (%)", value=5.0, min_value=0.0, max_value=100.0, key="st_retenue_pct")

        dc4_ref = st.text_input("DC4 Référence", value="", key="st_dc4")
        contrat_signe = st.checkbox("Contrat Signé", value=False, key="st_contrat_signe")

        if st.form_submit_button("💾 Enregistrer", use_container_width=True):
            if not fournisseur_id or not lot or montant_marche <= 0:
                st.error("Veuillez remplir tous les champs obligatoires")
            else:
                try:
                    sb = get_client()
                    sb.table("sous_traitants").insert({
                        "user_id": user_id,
                        "chantier_id": chantier_id,
                        "fournisseur_id": fournisseur_id,
                        "fournisseur_nom": get_fournisseur_nom(fournisseur_id, fournisseurs),
                        "lot_concerne": lot,
                        "montant_marche": montant_marche,
                        "retenue_garantie_pct": retenue_pct,
                        "retenue_garantie": montant_marche * retenue_pct / 100,
                        "dc4_reference": dc4_ref,
                        "contrat_signe": contrat_signe,
                        "avancement_pct": 0,
                        "montant_facture": 0,
                        "montant_paye": 0,
                        "statut": "actif",
                        "created_at": datetime.now().isoformat()
                    }).execute()
                    st.success("Sous-traitant ajouté avec succès")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors de l'enregistrement: {str(e)}")

# ==================== TAB 2: FACTURES ====================
with tab2:
    st.subheader("Factures Sous-Traitants")

    sous_traitants = get_sous_traitants(user_id, chantier_id)
    factures = get_factures_sous_traitants(user_id, chantier_id)

    # Display existing invoices
    if factures:
        st.markdown("**Factures Reçues**")

        status_filter = st.selectbox("Filtrer par statut:", ["Tous", "recue", "validee", "payee"], key="status_filter")

        filtered_factures = factures
        if status_filter != "Tous":
            filtered_factures = [f for f in factures if f.get("statut") == status_filter]

        for facture in filtered_factures:
            st_nom = next((s.get("fournisseur_nom") for s in sous_traitants if s.get("id") == facture.get("sous_traitant_id")), "Inconnu")

            with st.expander(f"📄 {st_nom} - Facture {facture.get('numero_facture', 'N/A')} - {facture.get('date_facture', 'N/A')}", expanded=False):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Montant HT", f"{format_currency(facture.get('montant_ht', 0))} €")
                with col2:
                    st.metric("Montant TTC", f"{format_currency(facture.get('montant_ttc', 0))} €")
                with col3:
                    st.metric("Avancement", f"{facture.get('avancement_cumule_pct', 0)}%")

                st.markdown(f"**Statut:** {render_status_badge(facture.get('statut', 'recue'))}", unsafe_allow_html=True)

                if st.button("Mettre à jour le statut", key=f"status_{facture.get('id')}"):
                    statuses = ["recue", "validee", "payee"]
                    current = facture.get("statut", "recue")
                    next_status = statuses[(statuses.index(current) + 1) % len(statuses)]

                    try:
                        sb = get_client()
                        sb.table("factures_sous_traitants").update({"statut": next_status}).eq("id", facture.get("id")).execute()
                        st.success(f"Facture passée en '{next_status}'")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur: {str(e)}")
    else:
        st.info("Aucune facture pour ce chantier")

    # Register new invoice form
    st.divider()
    st.subheader("➕ Enregistrer une Facture")

    with st.form("form_nouvelle_facture"):
        st_options = {s.get("id"): s.get("fournisseur_nom") for s in sous_traitants}

        if not st_options:
            st.warning("Aucun sous-traitant disponible. Ajoutez-en d'abord dans l'onglet Contrats.")
            st.form_submit_button("Annuler", disabled=True)
        else:
            sous_traitant_id = st.selectbox(
                "Sous-Traitant",
                options=list(st_options.keys()),
                format_func=lambda x: st_options[x],
                key="fac_st"
            )

            col1, col2 = st.columns(2)
            with col1:
                numero = st.text_input("Numéro de Facture", key="fac_numero")
            with col2:
                date_fac = st.date_input("Date de Facture", value=date.today(), key="fac_date")

            col1, col2 = st.columns(2)
            with col1:
                montant_ht = st.number_input("Montant HT (€)", value=0.0, min_value=0.0, key="fac_ht")
            with col2:
                avancement = st.number_input("Avancement Cumulé (%)", value=0.0, min_value=0.0, max_value=100.0, key="fac_avancement")

            montant_ttc = montant_ht * 1.20
            st.markdown(f"**Montant TTC (20% TVA):** {format_currency(montant_ttc)} €")

            if st.form_submit_button("💾 Enregistrer", use_container_width=True):
                if not numero or montant_ht <= 0:
                    st.error("Veuillez remplir tous les champs obligatoires")
                else:
                    try:
                        sb = get_client()
                        sb.table("factures_sous_traitants").insert({
                            "user_id": user_id,
                            "chantier_id": chantier_id,
                            "sous_traitant_id": sous_traitant_id,
                            "numero_facture": numero,
                            "date_facture": str(date_fac),
                            "montant_ht": montant_ht,
                            "montant_ttc": montant_ttc,
                            "avancement_cumule_pct": avancement,
                            "statut": "recue",
                            "created_at": datetime.now().isoformat()
                        }).execute()
                        st.success("Facture enregistrée avec succès")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur lors de l'enregistrement: {str(e)}")

# ==================== TAB 3: TABLEAU DE BORD ====================
with tab3:
    st.subheader("📊 Tableau de Bord Sous-Traitants")

    sous_traitants = get_sous_traitants(user_id, chantier_id)
    factures = get_factures_sous_traitants(user_id, chantier_id)

    if sous_traitants:
        # KPIs
        total_marche = sum(float(st.get("montant_marche", 0) or 0) for st in sous_traitants)
        total_facture = sum(float(st.get("montant_facture", 0) or 0) for st in sous_traitants)
        total_paye = sum(float(st.get("montant_paye", 0) or 0) for st in sous_traitants)
        total_retenue = sum(float(st.get("retenue_garantie", 0) or 0) for st in sous_traitants)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Marchäs Totaux", f"{format_currency(total_marche)} €")
        with col2:
            st.metric("Facturé", f"{format_currency(total_facture)} €")
        with col3:
            st.metric("Payé", f"{format_currency(total_paye)} €")
        with col4:
            st.metric("Retenues", f"{format_currency(total_retenue)} €")

        # Summary table
        st.markdown("**Résumé par Sous-Traitant**")

        summary_data = []
        for st_item in sous_traitants:
            summary_data.append({
                "Fournisseur": st_item.get("fournisseur_nom", "Inconnu"),
                "Lot": st_item.get("lot_concerne", "N/A"),
                "Marché": format_currency(st_item.get("montant_marche", 0)),
                "Facturé": format_currency(st_item.get("montant_facture", 0)),
                "Payé": format_currency(st_item.get("montant_paye", 0)),
                "Avancement": f"{st_item.get('avancement_pct', 0)}%",
                "Statut": st_item.get("statut", "actif")
            })

        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True)

        # Alerts
        st.markdown("**⚠️ Alertes**")

        alerts = []
        for st_item in sous_traitants:
            if not st_item.get("dc4_reference"):
                alerts.append(f"🔴 {st_item.get('fournisseur_nom', 'Inconnu')} - Pas de DC4")
            if not st_item.get("contrat_signe"):
                alerts.append(f"🟡 {st_item.get('fournisseur_nom', 'Inconnu')} - Contrat non signé")
            if float(st_item.get("montant_facture", 0) or 0) > float(st_item.get("montant_marche", 0) or 0):
                alerts.append(f"🔴 {st_item.get('fournisseur_nom', 'Inconnu')} - Factures > Marché")

        if alerts:
            for alert in alerts:
                st.warning(alert)
        else:
            st.success("✅ Aucune alerte")
    else:
        st.info("Aucun sous-traitant pour ce chantier. Commencez par en ajouter un.")
