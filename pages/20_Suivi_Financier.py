import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import json
from datetime import datetime, date
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib.supabase_client import get_client
from utils import GLOBAL_CSS
import pandas as pd
import plotly.graph_objects as go
from collections import defaultdict

# Page setup
user_id = page_setup("Suivi Financier", icon="📊")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)
require_feature(user_id, "suivi_financier")

# Initialize Supabase client
sb = get_client()

# Formatting helper
def fmt(val):
    """Format value as French currency"""
    if val is None:
        val = 0
    return f"{val:,.2f}".replace(",", " ").replace(".", ",") + " €"

def fmt_percent(val):
    """Format percentage"""
    if val is None:
        val = 0
    return f"{val:.1f}".replace(".", ",") + " %"

# ============================================================================
# SECTION 1: CHANTIER SELECTION & OVERVIEW
# ============================================================================
st.markdown("## 📍 Sélection du Chantier")

chantier_id = chantier_selector(user_id)

if not chantier_id:
    st.warning("Sélectionnez un chantier pour accéder au suivi financier")
    st.stop()

try:
    # Get chantier details
    chantier_resp = sb.table("chantiers").select("*").eq("id", chantier_id).single().execute()
    chantier = chantier_resp.data
    chantier_name = chantier.get("nom", "N/A")

    st.markdown(f"### {chantier_name}")

except Exception as e:
    st.error(f"Erreur chargement chantier: {str(e)}")
    st.stop()

# ============================================================================
# DATA AGGREGATION FUNCTIONS
# ============================================================================

def get_budget_data(chantier_id):
    """Get budget for the project"""
    try:
        resp = sb.table("budgets_chantier").select("*").eq("chantier_id", chantier_id).execute()
        if resp.data:
            return resp.data[0]
        return None
    except Exception as e:
        st.error(f"Erreur budget: {str(e)}")
        return None

def get_achats(chantier_id):
    """Get all purchases (achats) for the project"""
    try:
        resp = sb.table("achats").select("*").eq("chantier_id", chantier_id).execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error(f"Erreur achats: {str(e)}")
        return []

def get_sous_traitants(chantier_id):
    """Get all subcontractor expenses"""
    try:
        resp = sb.table("sous_traitants").select("*").eq("chantier_id", chantier_id).execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error(f"Erreur sous-traitants: {str(e)}")
        return []

def get_pointages(chantier_id):
    """Get all labor timesheets"""
    try:
        resp = sb.table("pointages").select("*").eq("chantier_id", chantier_id).execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error(f"Erreur pointages: {str(e)}")
        return []

def get_factures(chantier_id):
    """Get all invoices (revenue)"""
    try:
        resp = sb.table("factures").select("*").eq("chantier_id", chantier_id).execute()
        return resp.data if resp.data else []
    except Exception as e:
        st.error(f"Erreur factures: {str(e)}")
        return []

def get_employes_taux():
    """Get employee hourly rates"""
    try:
        resp = sb.table("employees").select("id,nom,taux_horaire").execute()
        return {emp["id"]: emp.get("taux_horaire", 0) for emp in resp.data}
    except Exception as e:
        st.error(f"Erreur employes: {str(e)}")
        return {}

def calculate_labor_cost(pointages, employes_taux):
    """Calculate total labor cost from timesheets"""
    total = 0
    for pointage in pointages:
        emp_id = pointage.get("employee_id")
        heures = pointage.get("jeures", 0)
        taux = employees_taux.get(emp_id, 0)
        total += heures * taux
    return total

def calculate_financial_data(chantier_id):
    """Aggregate all financial data for the project"""
    budget = get_budget_data(chantier_id)
    achats = get_achats(chantier_id)
    sous_traitants = get_sous_traitants(chantier_id)
    pointages = get_pointages(chantier_id)
    factures = get_factures(chantier_id)
    employes_taux = get_employes_taux()

    # Budget
    budget_total = 0
    budget_lots = {}
    if budget:
        budget_total = budget.get("montant_total_ht", 0)
        lots_data = budget.get("lots", [])
        if isinstance(lots_data, str):
            try:
                lots_data = json.loads(lots_data)
            except:
                lots_data = []
        for lot in lots_data:
            budget_lots[lot.get("nom", "N/A")] = lot.get("prevu_ht", 0)

    # Expenses
    achats_total = sum(a.get("montant_ht", 0) for a in achats)
    sous_traitants_data = []
    sous_traitants_engages = 0
    sous_traitants_factures = 0
    for st in sous_traitants:
        marche = st.get("montant_marche_ht", 0)
        facture = st.get("montant_facture_ht", 0)
        sous_traitants_engages += marche
        sous_traitants_factures += facture
        sous_traitants_data.append({
            "nom": st.get("nom", "N/A"),
            "marche": marche,
            "facture": facture
        })

    labor_total = calculate_labor_cost(pointages, employes_taux)

    # Revenue
    factures_data = []
    factures_total_ht = 0
    factures_payees = 0
    for fac in factures:
        montant = fac.get("montant_ht", 0)
        statut = fac.get("statut", "brouillon")
        factures_total_ht += montant
        if statut == "payee":
            factures_payees += montant
        factures_data.append({
            "numero": fac.get("numero", "N/A"),
            "date": fac.get("date", "N/A"),
            "montant": montant,
            "statut": statut
        })

    # Calculations
    total_expenses = achats_total + sous_traitants_engages + labor_total
    marge_brute = factures_total_ht - total_expenses
    marge_percent = (marge_brute / factures_total_ht * 100) if factures_total_ht > 0 else 0

    return {
        "budget_total": budget_total,
        "budget_lots": budget_lots,
        "achats_total": achats_total,
        "achats_list": achats,
        "sous_traitants_engages": sous_traitants_engages,
        "sous_traitants_factures": sous_traitants_factures,
        "sous_traitants_data": sous_traitants_data,
        "labor_total": labor_total,
        "pointages": pointages,
        "factures_total_ht": factures_total_ht,
        "factures_payees": factures_payees,
        "factures_data": factures_data,
        "total_expenses": total_expenses,
        "marge_brute": marge_brute,
        "marge_percent": marge_percent,
        "budget_obj": budget
    }

# Calculate financial data
fin_data = calculate_financial_data(chantier_id)

# Display KPIs
st.markdown("### 📈 Indicateurs Clés")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Budget Global", fmt(fin_data["budget_total"]))

with col2:
    st.metric("CA Facturé", fmt(fin_data["factures_total_ht"]))

with col3:
    st.metric("Dépenses", fmt(fin_data["total_expenses"]))

with col4:
    st.metric("Marge Brute", fmt(fin_data["marge_brute"]))

with col5:
    marge_pct = fin_data["marge_percent"]
    if marge_pct > 10:
        color = "green"
    elif marge_pct > 0:
        color = "orange"
    else:
        color = "red"

    st.metric("Marge %", fmt_percent(marge_pct))

# ============================================================================
# SECTION 2: BUDGET PAR LOT
# ============================================================================
st.markdown("---")
st.markdown("## 💰 Budget par Lot")

budget_lots = fin_data["budget_lots"]
if budget_lots and fin_data["budget_obj"]:
    st.markdown("### Suivi des Lots")

    lot_data = []
    for lot_name, prevu_ht in budget_lots.items():
        # Estimate engagé from achats with lot reference (if available)
        # Simplified: pro-rata based on achats total vs budget
        if fin_data["budget_total"] > 0:
            ratio = prevu_ht / fin_data["budget_total"]
            engages = fin_data["achats_total"] * ratio
        else:
            engages = 0

        factures_lot = 0  # Would need facture.lot field
        ecart = prevu_ht - engages
        ecart_pct = (ecart / prevu_ht * 100) if prevu_ht > 0 else 0

        lot_data.append({
            "Lot": lot_name,
            "Prévu HT": fmt(prevu_ht),
            "Engagé HT": fmt(engages),
            "Facturé HT": fmt(factures_lot),
            "Écart HT": fmt(ecart),
            "Écart %": fmt_percent(ecart_pct)
        })

    if lot_data:
        df_lots = pd.DataFrame(lot_data)
        st.dataframe(df_lots, use_container_width=True, hide_index=True)

    # Visualize budget vs engaged
    fig = go.Figure()
    lots = list(budget_lots.keys())
    prevus = list(budget_lots.values())
    engages = []
    for lot_name, prevu_ht in budget_lots.items():
        if fin_data["budget_total"] > 0:
            ratio = prevu_ht / fin_data["budget_total"]
            engages.append(fin_data["achats_total"] * ratio)
        else:
            engages.append(0)

    fig.add_trace(go.Bar(x=lots, y=prevus, name="Prévu HT", marker_color="lightblue"))
    fig.add_trace(go.Bar(x=lots, y=engages, name="Engagé HT", marker_color="orange"))
    fig.update_layout(title="Comparaison Prévu vs Engagé par Lot", barmode="group", height=400)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Aucun budget défini pour ce chantier.")

# Budget definition form
st.markdown("### Définir/Modifier le Budget")
with st.form("budget_form"):
    num_lots = st.number_input("Nombre de lots", min_value=1, max_value=10, value=len(budget_lots) if budget_lots else 1)

    lot_inputs = []
    for i in range(num_lots):
        col1, col2 = st.columns(2)
        with col1:
            lot_name = st.text_input(f"Nom Lot {i+1}", value=list(budget_lots.keys())[i] if i < len(budget_lots) else "")
        with col2:
            lot_prevu = st.number_input(f"Prévu HT Lot {i+1}", min_value=0.0, value=float(list(budget_lots.values())[i]) if i < len(budget_lots) else 0.0)

        if lot_name:
            lot_inputs.append({"nom": lot_name, "prevu_ht": lot_prevu})

    budget_total = st.number_input("Budget Total HT", min_value=0.0, value=fin_data["budget_total"])

    if st.form_submit_button("Enregistrer le Budget"):
        try:
            budget_payload = {
                "montant_total_ht": budget_total,
                "lots": lot_inputs,
                "date_maj": datetime.now().isoformat()
            }

            if fin_data["budget_obj"]:
                # Update
                sb.table("budgets_chantier").update(budget_payload).eq("chantier_id", chantier_id).execute()
                st.success("Budget mis à jour ✓")
            else:
                # Insert
                budget_payload["chantier_id"] = chantier_id
                sb.table("budgets_chantier").insert(budget_payload).execute()
                st.success("Budget créé ✓")

            st.rerun()
        except Exception as e:
            st.error(f"Erreur enregistrement: {str(e)}")

# ============================================================================
# SECTION 3: DÉTAIL DES DÉPENSES
# ============================================================================
st.markdown("---")
st.markdown("## 💸 Détail des Dépenses")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Achats Fournisseurs")
    achats_total = fin_data["achats_total"]
    st.metric("Total Achats", fmt(achats_total))

    achats_list = fin_data["achats_list"]
    if achats_list:
        achats_df_data = []
        for achat in achats_list:
            achats_df_data.append({
                "Fournisseur": achat.get("fournisseur", "N/A"),
                "Montant HT": fmt(achat.get("montant_ht", 0)),
                "Date": achat.get("date", "N/A")
            })
        achats_df = pd.DataFrame(achats_df_data)
        st.dataframe(achats_df, use_container_width=True, hide_index=True, height=300)
    else:
        st.write("Aucun achat enregistré")

with col2:
    st.markdown("### Sous-traitance")
    st.metric("Engagements ST", fmt(fin_data["sous_traitants_engages"]))
    st.metric("Facturé ST", fmt(fin_data["sous_traitants_factures"]))

    st_data = fin_data["sous_traitants_data"]
    if st_data:
        st_df_data = []
        for st in st_data:
            st_df_data.append({
                "Sous-traitant": st.get("nom", "N/A"),
                "Marché HT": fmt(st.get("marche", 0)),
                "Facturé HT": fmt(st.get("facture", 0))
            })
        st_df = pd.DataFrame(st_df_data)
        st.dataframe(st_df, use_container_width=True, hide_index=True, height=300)
    else:
        st.write("Aucun sous-traitant")

with col3:
    st.markdown("### Main d'Œuvre")
    labor_total = fin_data["labor_total"]
    st.metric("Total MO", fmt(labor_total))

    pointages = fin_data["pointages"]
    if pointages:
        employees_taux = get_employes_taux()
        mo_df_data = []
        for pointage in pointages:
            emp_id = pointage.get("employee_id")
            heures = pointage.get("jeures", 0)
            taux = employees_taux.get(emp_id, 0)
            cout = heures * taux

            # Get employee name
            try:
                emp_resp = sb.table("employees").select("nom").eq("id", emp_id).single().execute()
                emp_name = emp_resp.data.get("nom", "N/A") if emp_resp.data else "N/A"
            except:
                emp_name = "N/A"

            mo_df_data.append({
                "Employmé": emp_name,
                "Jej Heures": f"{heures:.1f}".replace(".", ","),
                "Coût": fmt(cout)
            })
        mo_df = pd.DataFrame(mo_df_data)
        st.dataframe(mo_df, use_container_width=True, hide_index=True, height=300)
    else:
        st.write("Aucun pointage")

# ============================================================================
# SECTION 4: FACTURATION (RECETTES)
# ============================================================================
st.markdown("---")
st.markdown("## 📋 Facturation (Recettes)")

col1, col2 = st.columns(2)
with col1:
    st.metric("Total Facturé HT", fmt(fin_data["factures_total_ht"]))
with col2:
    st.metric("Total Encaissé", fmt(fin_data["factures_payees"]))

st.markdown("### Liste des Factures")
factures_data = fin_data["factures_data"]
if factures_data:
    fac_df_data = []
    for fac in factures_data:
        fac_df_data.append({
            "N° Facture": fac.get("numero", "N/A"),
            "Date": fac.get("date", "N/A"),
            "Montant HT": fmt(fac.get("montant", 0)),
            "Statut": fac.get("statut", "brouillon")
        })
    fac_df = pd.DataFrame(fac_df_data)
    st.dataframe(fac_df, use_container_width=True, hide_index=True)
else:
    st.write("Aucune facture")

# ============================================================================
# SECTION 5: COURBE DE RENTABILITÉ
# ============================================================================
st.markdown("---")
st.markdown("## 📈 Courbe de Rentabilité")

try:
    # Aggregate factures and expenses by month
    monthly_data = defaultdict(lambda: {"factures": 0, "depenses": 0})

    # Add factures by month
    for fac in fin_data["factures_data"]:
        date_str = fac.get("date", "")
        if date_str:
            try:
                fac_date = datetime.fromisoformat(date_str) if isinstance(date_str, str) else fac_date
                month_key = fac_date.strftime("%Y-%m")
                monthly_data[month_key]["factures"] += fac.get("montant", 0)
            except:
                pass

    # Add expenses by month (simplified: spread evenly or by achat date)
    for achat in fin_data["achats_list"]:
        date_str = achat.get("date", "")
        if date_str:
            try:
                achat_date = datetime.fromisoformat(date_str) if isinstance(date_str, str) else achat_date
                month_key = achat_date.strftime("%Y-%m")
                monthly_data[month_key]["depenses"] += achat.get("montant_ht", 0)
            except:
                pass

    if monthly_data:
        months = sorted(monthly_data.keys())
        cumul_factures = []
        cumul_depenses = []
        cumul_fac = 0
        cumul_dep = 0

        for month in months:
            cumul_fac += monthly_data[month]["factures"]
            cumul_dep += monthly_data[month]["depenses"]
            cumul_factures.append(cumul_fac)
            cumul_depenses.append(cumul_dep)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=months, y=cumul_factures, mode="lines+markers", name="Cumul Facturé", line=dict(color="green")))
        fig.add_trace(go.Scatter(x=months, y=cumul_depenses, mode="lines+markers", name="Cumul Dépenses", line=dict(color="red")))
        fig.update_layout(title="Courbe de Rentabilité", xaxis_title="Mois", yaxis_title="Montant (€)", height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Pas assez de données pour afficher la courbe")
except Exception as e:
    st.warning(f"Erreur courbe: {str(e)}")

st.markdown("---")
st.markdown("*Dernière mise à jour: " + datetime.now().strftime("%d/%m/%Y %H:%M") + "*")
