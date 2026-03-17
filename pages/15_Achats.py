import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import json
from datetime import datetime, date, timedelta
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib import db
from utils import GLOBAL_CSS
from lib.supabase_client import get_client
import pandas as pd

user_id = page_setup("Achats & Fournisseurs", icon="🛒")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)
require_feature(user_id, "achats")

sb = get_client()

# ==================== STYLES ====================
CATEGORY_COLORS = {
    "materiaux": "#1f77b4",      # Blue
    "location": "#ff7f0e",        # Orange
    "sous-traitance": "#9467bd",  # Purple
    "services": "#2ca02c"         # Green
}

def format_currency(value):
    """Format number as French currency."""
    try:
        if value is None:
            return "0,00 €"
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", " ") + " €"
    except:
        return "0,00 €"

def get_status_badge(status):
    """Return colored status badge."""
    badges = {
        "brouillon": "🟡 Brouillon",
        "commandé": "🟢 Commandé",
        "livré": "✅ Livré",
        "annulé": "🔴 Annulé"
    }
    return badges.get(status, status)

def get_category_badge(category):
    """Return colored category badge."""
    color = CATEGORY_COLORS.get(category, "#808080")
    return f":{color}[{category}]"

# ==================== TAB 1: FOURNISSEURS ====================
def tab_fournisseurs():
    st.subheader("📋 Répertoire des Fournisseurs")

    col1, col2 = st.columns([3, 1])
    search_term = col1.text_input("🔍 Chercher un fournisseur", "")
    category_filter = col2.selectbox("Catégorie", ["Tous", "materiaux", "location", "sous-traitance", "services"], key="filter_cat")

    try:
        response = sb.table("fournisseurs").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        suppliers = response.data if response.data else []

        # Filter
        if search_term:
            suppliers = [s for s in suppliers if search_term.lower() in s.get("bom", "").lower()]
        if category_filter != "Tous":
            suppliers = [s for s in suppliers if s.get("categorie") == category_filter]

        # Display as cards
        if suppliers:
            for supplier in suppliers:
                with st.expander(f"**{supplier['nom']}** {get_category_badge(supplier.get('categorie', 'N/A'))}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Contact:** {supplier.get('contact_nom', 'N/A')}")
                        st.write(f"**Email:** {supplier.get('email', 'N/A')}")
                        st.write(f"**Téléphone:** {supplier.get('telephone', 'N/A')}")
                    with col2:
                        st.write(f"**Adresse:** {supplier.get('adresse', 'N/A')}")
                        st.write(f"**SIRET:** {supplier.get('siret', 'N/A')}")
                        st.write(f"**Notes:** {supplier.get('notes', '')}")

                    col_edit, col_del = st.columns(2)
                    if col_edit.button("✏️ Modifier", key=f"edit_{supplier['id']}"):
                        st.session_state[f"edit_supplier_{supplier['id']}"] = True

                    if col_del.button("🗑️ Supprimer", key=f"del_{supplier['id']}"):
                        try:
                            sb.table("fournisseurs").delete().eq("id", supplier['id']).execute()
                            st.success("Fournisseur supprimé")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur: {str(e)}")
        else:
            st.info("Aucun fournisseur trouvé")

    except Exception as e:
        st.error(f"Erreur chargement fournisseurs: {str(e)}")

    st.divider()

    # Add supplier form
    st.subheader("➕ Ajouter un Fournisseur")
    with st.form("new_supplier", border=True):
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom du fournisseur*")
            contact_nom = st.text_input("Nom du contact")
            email = st.text_input("Email")
        with col2:
            telephone = st.text_input("Téléphone")
            siret = st.text_input("SIRET")
            categorie = st.selectbox("Catégorie*", ["materiaux", "location", "sous-traitance", "services"])

        adresse = st.text_area("Adresse")
        notes = st.text_area("Notes")

        submitted = st.form_submit_button("✅ Enregistrer", use_container_width=True)

        if submitted:
            if not nom or not categorie:
                st.error("Veuillez remplir nom et catégorie")
            else:
                try:
                    data = {
                        "user_id": user_id,
                        "nom": nom,
                        "contact_nom": contact_nom,
                        "email": email,
                        "telephone": telephone,
                        "siret": siret,
                        "categorie": categorie,
                        "adresse": adresse,
                        "notes": notes,
                        "created_at": datetime.now().isoformat()
                    }
                    sb.table("fournisseurs").insert(data).execute()
                    st.success("✅ Fournisseur enregistré")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur: {str(e)}")

# ==================== TAB 2: BONS DE COMMANDE ====================
def tab_bons_commande():
    st.subheader("📦 Bons de Commande")

    chantier_id = chantier_selector(key="achats_chantier")

    if not chantier_id:
        st.warning("Veuillez sélectionner un chantier")
        return

    # Load purchase orders
    try:
        response = sb.table("achats").select("*").eq("chantier_id", chantier_id).eq("user_id", user_id).order("created_at", desc=True).execute()
        orders = response.data if response.data else []
    except Exception as e:
        st.error(f"Erreur chargement commandes: {str(e)}")
        orders = []

    # Display existing orders
    if orders:
        st.write(f"**{len(orders)} bon(s) de commande(s)**")
        for order in orders:
            status_badge = get_status_badge(order.get("statut", "brouillon"))
            numero = order.get("numero", "N/A")
            fournisseur = order.get("fournisseur_nom", "N/A")
            montant_ttc = order.get("montant_ttc", 0)

            with st.expander(f"{numero} | {fournisseur} | {status_badge} | {format_currency(montant_ttc)}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Objet:** {order.get('objet', '')}")
                    st.write(f"**Commandé le:** {order.get('date_commande', '')}")
                with col2:
                    st.write(f"**Livraison prévue:** {order.get('date_livraison_prevue', '')}")
                    st.write(f"**Fournisseur ID:** {order.get('fournisseur_id', '')}")
                with col3:
                    st.write(f"**Montant HT:** {format_currency(order.get('montant_ht', 0))}")
                    st.write(f"**TVA:** {format_currency(order.get('montant_tva', 0))}")
                    st.write(f"**TTC:** {format_currency(montant_ttc)}")
              # Line items
               try:
                    items_resp = sb.table("achats_lignes").select("*").eq("achat_id", order["id"]).execute()
                    if items_resp.data:
                        st.write("**Détail des lignes:**")
                        items_df = pd.DataFrame(items_resp.data)
                        st.dataframe(items_df[["designation", "quantite", "unite", "prix_unitaire", "montant"]], use_container_width=True)
                except Exception as e:
                    st.warning(f"Erreur chargement lignes: {'str(e)}")

                # Status change buttons
                st.write("**Changer le statut:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if order.get("statut") == "brouillon" and st.button("→ Commandé", key=f"cmd_{order['id']}"):
                        try:
                            sb.table("achats").update({"statut": "commandé"}).eq("id", order["id"]).execute()
                            st.success("Statut mis à jour")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur: {str(e)}")
                with col2:
                    if order.get("statut") == "commandé" and st.button("→ Livré", key=f"liv_{order['id']}"):
                        try:
                            sb.table("achats").update({"statut": "livré"}).eq("id", order["id"]).execute()
                            st.success("Commande livrée")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur: {str(e)}")
                with col3:
                    if st.button("🗑️ Supprimer", key=f"delete_{order['id']}"):
                        try:
                            sb.table("achats_lignes").delete().eq("achat_id", order["id"]).execute()
                            sb.table("achats").delete().eq("id", order["id"]).execute()
                            st.success("Commande supprimée")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur: {str(e)}")
    else:
        st.info("Aucune commande pour ce chantier")

    st.divider()

    # New purchase order form
    st.subheader("➕ Nouveau Bon de Commande")

    try:
        fournisseurs_resp = sb.table("fournisseurs").select("id, nom").eq("user_id", user_id).execute()
        fournisseurs = {f["nom"]: f["id"] for f in (fournisseurs_resp.data or [])}
    except Exception as e:
        st.error(f"Erreur chargement fournisseurs: {str(e)}")
        fournisseurs = {}

    if not fournisseurs:
        st.warning("Créez d'abord un fournisseur dans l'onglet 'Fournisseurs'")
        return

    with st.form("new_order", border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            fournisseur_nom = st.selectbox("Fournisseur*", list(fournisseurs.keys()))
            fournisseur_id = fournisseurs[fournisseur_nom]
        with col2:
            date_commande = st.date_input("Date de commande*", value=date.today())
        with col3:
            date_livraison = st.date_input("Date livraison prévue*", value=date.today() + timedelta(days=7))

        objet = st.text_input("Objet de la commande*")

        st.write("**Lignes de commande:**")
        num_lines = st.number_input("Nombre de lignes", min_value=1, max_value=10, value=1)

        lines = []
        for i in range(int(num_lines)):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                designation = st.text_input("Désignation", key=f"des_{i}")
            with col2:
                quantite = st.number_input("Quantité", min_value=0.0, value=1.0, key=f"qty_{i}")
            with col3:
                unite = st.text_input("Unité (m, l, pc...)", value="pc", key=f"unit_{i}")
            with col4:
                prix_unitaire = st.number_input("Prix unitaire", min_value=0.0, key=f"price_{i}")

            montant = quantite * prix_unitaire
            st.caption(f"Montant ligne: {format_currency(montant)}")

            if designation:
                lines.append({
                    "designation": designation,
                    "quantite": quantite,
                    "unite": unite,
                    "prix_unitaire": prix_unitaire,
                    "montant": montant
                })

        # Calculate totals
        total_ht = sum(line["montant"] for line in lines)
        tva = total_ht * 0.20
        total_ttc = total_ht + tva

        col1, col2, col3 = st.columns(3)
        col1.metric("Total HT", format_currency(total_ht))
        col2.metric("TVA (20%)", format_currency(tva))
        col3.metric("Total TTC", format_currency(total_ttc))

        submitted = st.form_submit_button("✅ Créer la commande", use_container_width=True)

        if submitted:
            if not objet or not lines:
                st.error("Veuillez remplir objet et au moins une ligne")
            else:
                try:
                    # Generate numero BC-YYYYMM-NNN
                    now = datetime.now()
                    count_resp = sb.table("achats").select("id").eq("user_id", user_id).execute()
                    numero = f"BC-{now.strftime('%Y%m')}-{len(count_resp.data or []) + 1:03d}"

                    achat_data = {
                        "user_id": user_id,
                        "chantier_id": chantier_id,
                        "numero": numero,
                        "fournisseur_id": fournisseur_id,
                        "fournisseur_nom": fournisseur_nom,
                        "objet": objet,
                        "date_commande": date_commande.isoformat(),
                        "date_livraison_prevue": date_livraison.isoformat(),
                        "montant_ht": total_ht,
                        "montant_tva": tva,
                        "montant_ttc": total_ttc,
                        "statut": "brouillon",
                        "created_at": datetime.now().isoformat()
                    }

                    result = sb.table("achats").insert(achat_data).execute()
                    achat_id = result.data[0]["id"] if result.data else None

                    # Insert line items
                    if achat_id:
                        for idx, line in enumerate(lines):
                            ligne_data = {
                                "achat_id": achat_id,
                                "designation": line["designation"],
                                "quantite": line["quantite"],
                                "unite": line["unite"],
                                "prix_unitaire": line["prix_unitaire"],
                                "montant": line["montant"],
                                "order_index": idx
                            }
                            sb.table("achats_lignes").insert(ligne_data).execute()

                    st.success(f"✅ Commande créée: {numero}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur: {str(e)}")

# ==================== TAB 3: SUIVI ====================
def tab_suivi():
    st.subheader("📊 Suivi & Analytique")

    try:
        # Get all orders for user
        orders_resp = sb.table("achats").select("*").eq("user_id", user_id).execute()
        orders = orders_resp.data if orders_resp.data else []

        # KPIs
        col1, col2, col3, col4 = st.columns(4)

        total_commande = sum(o.get("montant_ttc", 0) for o in orders)
        total_livre = sum(o.get("montant_ttc", 0) for o in orders if o.get("statut") == "livré")
        total_en_attente = sum(o.get("montant_ttc", 0) for o in orders if o.get("statut") in ["brouillon", "commandé"])
        nb_commandes = len(orders)

        col1.metric("📦 Total commandé", format_currency(total_commande))
        col2.metric("✅ Total livré", format_currency(total_livre))
        col3.metric("⏳ En attente", format_currency(total_en_attente))
        col4.metric("🔢 Commandes", str(nb_commandes))

        st.divider()

        # Charts by chantier
        if orders:
            st.write("**Achats par chantier (TTC):**")
            try:
                chantiers_resp = sb.table("chantiers").select("id, nom").eq("user_id", user_id).execute()
                chantiers_dict = {c["id"]: c["nom"] for c in (chantiers_resp.data or [])}

                by_chantier = {}
                for order in orders:
                    chantier_id = order.get("chantier_id")
                    chantier_nom = chantiers_dict.get(chantier_id, "N/A")
                    by_chantier[chantier_nom] = by_chantier.get(chantier_nom, 0) + order.get("montant_ttc", 0)

                if by_chantier:
                    df = pd.DataFrame(list(by_chantier.items()), columns=["Chantier", "Montant TTC"])
                    st.bar_chart(df.set_index("Chantier"))
            except Exception as e:
                st.warning(f"Erreur graphique chantiers: {str(e)}")

        st.divider()

        # Top fournisseurs
        st.write("**Top 5 Fournisseurs par montant:**")
        by_fournisseur = {}
        for order in orders:
            fournisseur = order.get("fournisseur_nom", "N/A")
            by_fournisseur[fournisseur] = by_fournisseur.get(fournisseur, 0) + order.get("montant_ttc", 0)

        if by_fournisseur:
            top_5 = sorted(by_fournisseur.items(), key=lambda x: x[1], reverse=True)[:5]
            df_top = pd.DataFrame(top_5, columns=["Fournisseur", "Montant TTC"])
            st.dataframe(df_top, use_container_width=True)

        st.divider()

        # Pending deliveries
        st.write("**Commandes en attente de livraison:**")
        pending = [o for o in orders if o.get("statut") in ["brouillon", "commandé"]]
        if pending:
            pending_df = pd.DataFrame([
                {
                    "Numéro": o.get("numero"),
                    "Fournisseur": o.get("fournisseur_nom"),
                    "Statut": get_status_badge(o.get("statut")),
                    "Montant": format_currency(o.get("montant_ttc", 0)),
                    "Livraison prévue": o.get("date_livraison_prevue")
                }
                for o in pending
            ])
            st.dataframe(pending_df, use_container_width=True)
        else:
            st.success("✅ Aucune commande en attente!")

    except Exception as e:
        st.error(f"Erreur suivi: {str(e)}")

# ==================== MAIN LAYOUT ====================
tab1, tab2, tab3 = st.tabs(["Fournisseurs", "Bons de Commande", "Suivi"])

with tab1:
    tab_fournisseurs()

with tab2:
    tab_bons_commande()

with tab3:
    tab_suivi()