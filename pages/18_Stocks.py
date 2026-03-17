import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import json
import pandas as pd
from datetime import datetime, date, timedelta
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib.supabase_client import get_client
from utils import GLOBAL_CSS

user_id = page_setup("Stocks", icon="📦")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)
require_feature(user_id, "stocks")

sb = get_client()


def get_stocks():
    try:
        response = sb.table("stocks").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erreur chargement stocks: {e}")
        return []


def get_mouvements():
    try:
        response = sb.table("mouvements_stock").select("*").order("date", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erreur chargement mouvements: {e}")
        return []


def get_fournisseurs():
    try:
        response = sb.table("fournisseurs").select("id, nom").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erreur chargement fournisseurs: {e}")
        return []


def add_stock(designation, reference, categorie, unite, stock_minimum, prix_unitaire, emplacement, fournisseur_id):
    try:
        sb.table("stocks").insert({
            "designation": designation,
            "reference": reference,
            "categorie": categorie,
            "unite": unite,
            "quantite_stock": 0,
            "stock_minimum": stock_minimum,
            "prix_unitaire": prix_unitaire,
            "emplacement": emplacement,
            "fournisseur_id": fournisseur_id,
            "created_at": datetime.now().isoformat()
        }).execute()
        st.success("Article ajouté avec succès")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur ajout article: {e}")


def add_mouvement(stock_id, quantite, type_mouvement, chantier_id, motif, mouvement_date):
    try:
        stocks = get_stocks()
        stock = next((s for s in stocks if s["id"] == stock_id), None)

        if not stock:
            st.error("Article non trouvé")
            return

        nouvelle_quantite = stock["quantite_stock"]
        if type_mouvement == "entree":
            nouvelle_quantite += quantite
        else:
            if quantite > stock["quantite_stock"]:
                st.error(f"Quantité insuffisante. Disponible: {stock['quantite_stock']}")
                return
            nouvelle_quantite -= quantite

        sb.table("mouvements_stock").insert({
            "stock_id": stock_id,
            "type": type_mouvement,
            "quantite": quantite,
            "chantier_id": chantier_id if type_mouvement == "sortie" else None,
            "motif": motif,
            "date": mouvement_date,
            "created_at": datetime.now().isoformat()
        }).execute()

        sb.table("stocks").update({"quantite_stock": nouvelle_quantite}).eq("id", stock_id).execute()

        st.success(f"Mouvement enregistré")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur enregistrement mouvement: {e}")


def delete_stock(stock_id):
    try:
        sb.table("stocks").delete().eq("id", stock_id).execute()
        st.success("Article supprimé")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur suppression: {e}")


def update_stock(stock_id, data):
    try:
        sb.table("stocks").update(data).eq("id", stock_id).execute()
        st.success("Article modifié")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur modification: {e}")


# TABS
tab1, tab2, tab3 = st.tabs(["📋 Inventaire", "↔️ Mouvements", "📊 Tableau de bord"])

# TAB 1: INVENTAIRE
with tab1:
    st.subheader("Gestion de l'Inventaire")

    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("Rechercher par désignation ou référence", "")
    with col2:
        categorie_filter = st.selectbox("Catégorie", ["Tous", "materiaux", "outillage", "EPI", "consommables"])

    stocks = get_stocks()
    df_stocks = pd.DataFrame(stocks) if stocks else pd.DataFrame()

    if not df_stocks.empty:
        if search:
            mask = (df_stocks["designation"].str.contains(search, case=False, na=False)) | \
                   (df_stocks["reference"].str.contains(search, case=False, na=False))
            df_stocks = df_stocks[mask]

        if categorie_filter != "Tous":
            df_stocks = df_stocks[df_stocks["categorie"] == categorie_filter]

        df_stocks["valeur_stock"] = df_stocks["quantite_stock"] * df_stocks["prix_unitaire"]

        display_df = df_stocks[["designation", "reference", "categorie", "quantite_stock",
                                "stock_minimum", "prix_unitaire", "valeur_stock"]].copy()

        for idx, row in display_df.iterrows():
            stock_id = df_stocks.iloc[idx]["id"]
            quantite = row["quantite_stock"]
            minimum = row["stock_minimum"]

            if quantite < minimum:
                color = "🔴"
            elif quantite < minimum * 1.5:
                color = "🟠"
            else:
                color = "🟢"

            display_df.at[idx, "designation"] = f"{color} {row['designation']}"

        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("Aucun article en stock")

    st.divider()
    st.subheader("Ajouter un article")

    with st.form("form_new_stock"):
        col1, col2 = st.columns(2)
        with col1:
            designation = st.text_input("Désignation *")
            reference = st.text_input("Référence *")
            categorie = st.selectbox("Catégorie *", ["materiaux", "outillage", "EPI", "consommables"])
        with col2:
            unite = st.text_input("Unité (ex: m, kg, pcs)", "pcs")
            stock_minimum = st.number_input("Stock minimum *", min_value=0, step=1)
            prix_unitaire = st.number_input("Prix unitaire (€) *", min_value=0.0, step=0.01)

        emplacement = st.text_input("Emplacement (ex: Rack A12)")
        fournisseurs = get_fournisseurs()
        fournisseur_dict = {f["nom"]: f["id"] for f in fournisseurs}
        fournisseur = st.selectbox("Fournisseur", list(fournisseur_dict.keys()) + [""])

        submitted = st.form_submit_button("Ajouter l'article")
        if submitted:
            if designation and reference and stock_minimum >= 0 and prix_unitaire >= 0:
                fournisseur_id = fournisseur_dict.get(fournisseur)
                add_stock(designation, reference, categorie, unite, stock_minimum, prix_unitaire, emplacement, fournisseur_id)
            else:
                st.error("Veuillez remplir tous les champs obligatoires")

    st.divider()
    st.subheader("Modifier/Supprimer")

    if df_stocks is not None and not df_stocks.empty:
        select_article = st.selectbox("Sélectionner un article", df_stocks["designation"].tolist())
        selected = df_stocks[df_stocks["designation"] == select_article].iloc[0]
        stock_id = selected["id"]

        with st.expander("✏️ Modifier cet article"):
            col1, col2 = st.columns(2)
            with col1:
                new_minimum = st.number_input("Nouveau stock minimum", value=int(selected["stock_minimum"]))
                new_prix = st.number_input("Nouveau prix unitaire", value=float(selected["prix_unitaire"]), step=0.01)
            with col2:
                new_quantity = st.number_input("Quantité en stock", value=int(selected["quantite_stock"]))
                new_emplacement = st.text_input("Emplacement", value=selected.get("emplacement", ""))

            if st.button("💾 Enregistrer modifications"):
                update_stock(stock_id, {
                    "stock_minimum": new_minimum,
                    "prix_unitaire": new_prix,
                    "quantite_stock": new_quantite,
                    "emplacement": new_emplacement
                })

        with st.expander("🗑️ Supprimer cet article", expanded=False):
            st.warning(f"Supprimer '{select_article}' ? Cette action est irréversible.")
            if st.button("Confirmer la suppression", key="delete_confirm"):
                delete_stock(stock_id)


# TAB 2: MOUVEMENTS
with tab2:
    st.subheader("Gestion des Mouvements")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Nouvelle entrée", use_container_width=True):
            st.session_state.mouvement_type = "entree"
    with col2:
        if st.button("➖ Nouvelle sortie", use_container_width=True):
            st.session_state.mouvement_type = "sortie"

    if "mouvement_type" in st.session_state:
        st.divider()
        st.subheader(f"{'Entrée' if st.session_state.mouvement_type == 'entree' else 'Sortie'} de stock")

        with st.form("form_mouvement"):
            stocks = get_stocks()
            stock_options = {s["designation"]: s["id"] for s in stocks}

            col1, col2 = st.columns(2)
            with col1:
                selected_stock = st.selectbox("Article *", list(stock_options.keys()))
                quantite = st.number_input("Quantité *", min_value=1, step=1)
            with col2:
                mouvement_date = st.date_input("Date", value=date.today())
                motif = st.text_input("Motif (ex: achat, transfert, casse)", "")

            chantier_id = None
            if st.session_state.mouvement_type == "sortie":
                chantier_id = chantier_selector("Chantier concerné")

            submitted = st.form_submit_button("Enregistrer le mouvement")
            if submitted:
                if selected_stock and quantite > 0:
                    stock_id = stock_options[selected_stock]
                    add_mouvement(stock_id, quantite, st.session_state.mouvement_type, chantier_id, motif, mouvement_date.isoformat())
                else:
                    st.error("Veuillez remplir tous les champs")

    st.divider()
    st.subheader("Historique des Mouvements")

    col1, col2, col3 = st.columns(3)
    with col1:
        date_debut = st.date_input("Du", value=date.today() - timedelta(days=30))
    with col2:
        date_fin = st.date_input("Au", value=date.today())
    with col3:
        type_filter = st.selectbox("Type", ["Tous", "entree", "sortie"])

    mouvements = get_mouvements()
    df_mouvements = pd.DataFrame(mouvements) if mouvements else pd.DataFrame()

    if not df_mouvements.empty:
        df_mouvements["date"] = pd.to_datetime(df_mouvements["date"]).dt.date

        mask = (df_mouvements["date"] >= date_debut) & (df_mouvements["date"] <= date_fin)
        df_mouvements = df_mouvements[mask]

        if type_filter != "Tous":
            df_mouvements = df_mouvements[df_mouvements["type"] == type_filter]

        stocks_dict = {s["id"]: s["designation"] for s in stocks}
        df_mouvements["article"] = df_mouvements["stock_id"].map(stocks_dict)

        df_display = df_mouvements[["date", "type", "article", "quantite", "motif"]].copy()
        df_display["type"] = df_display["type"].apply(lambda x: f"📥 Entrée" if x == "entree" else "📤 Sortie")

        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun mouvement")


# TAB 3: TABLEAU DE BORD
with tab3:
    st.subheader("Tableau de Bord Stocks")

    stocks = get_stocks()
    mouvements = get_mouvements()

    if stocks:
        df_stocks = pd.DataFrame(stocks)

        # KPIs
        valeur_totale = (df_stocks["quantite_stock"] * df_stocks["prix_unitaire"]).sum()
        ruptures = len(df_stocks[df_stocks["quantite_stock"] < df_stocks["stock_minimum"]])
        nb_mouvements = len(mouvements)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Valeur totale stock", f"{valeur_totale:,.2f} €")
        with col2:
            st.metric("🔴 Articles en rupture", ruptures)
        with col3:
            st.metric("↔️ Mouvements", nb_mouvements)

        st.divider()

        # Alertes
        st.subheader("⚠️ Alertes Stock Minimum")
        alertes = df_stocks[df_stocks["quantite_stock"] < df_stocks["stock_minimum"]][["designation", "quantite_stock", "stock_minimum"]]

        if not alertes.empty:
            for _, row in alertes.iterrows():
                st.warning(f"**{row['designation']}**: {int(row['quantite_stock'])} unités (minimum: {int(row['stock_minimum'])})")
        else:
            st.success("✅ Tous les articles respectent le stock minimum")

        st.divider()

        col1, col2 = st.columns(2)

        # Top articles par mouvements
        with col1:
            st.subheader("📈 Top 5 Articles (mouvements)")
            if mouvements:
                df_mouvements = pd.DataFrame(mouvements)
                top_articles = df_mouvements["stock_id"].value_counts().head(5)
                stocks_dict = {s["id"]: s["designation"] for s in stocks}

                chart_data = pd.DataFrame({
                    "Article": [stocks_dict.get(sid, "?") for sid in top_articles.index],
                    "Mouvements": top_articles.values
                })
                st.bar_chart(chart_data.set_index("Article"))
            else:
                st.info("Aucun mouvement")

        # Valeur par catégorie
        with col2:
            st.subheader("💳 Valeur Stock par Catégorie")
            df_stocks["valeur"] = df_stocks["quantite_stock"] * df_stocks["prix_unitaire"]
            valeur_cat = df_stocks.groupby("categorie")["valeur"].sum()

            if not valeur_cat.empty:
                st.bar_chart(valuer_cat)
            else:
                st.info("Aucune catégorie")
    else:
        st.info("📦 Aucun article en stock. Commencez par en ajouter dans l'onglet Inventaire.")
