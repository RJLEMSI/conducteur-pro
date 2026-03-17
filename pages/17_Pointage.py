import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import json
from datetime import datetime, date, timedelta
import pandas as pd
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector, require_feature
from lib.supabase_client import get_client
from utils import GLOBAL_CSS

# Page setup
user_id = page_setup("Pointage", icon="⏱️")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)
require_feature(user_id, "pointage")

# Initialize Supabase client
sb = get_client()

# Helper functions
def get_employes(user_id):
    """Fetch all employees for the user"""
    try:
        response = sb.table("employes").select("*").eq("user_id", user_id).order("nom").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erreur lors du chargement des employés: {str(e)}")
        return []

def get_pointages(user_id, start_date=None, end_date=None):
    """Fetch pointages (time entries) within date range"""
    try:
        query = sb.table("pointages").select("*").eq("user_id", user_id)
        if start_date:
            query = query.gte("date", start_date.isoformat())
        if end_date:
            query = query.lte("date", end_date.isoformat())
        response = query.order("date", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Erreur lors du chargement des pointages: {str(e)}")
        return []

def save_pointage(user_id, chantier_id, employe_id, date_obj, heures, type_pointage, description):
    """Save a time entry"""
    try:
        payload = {
            "user_id": user_id,
            "chantier_id": chantier_id,
            "employe_id": employe_id,
            "date": date_obj.isoformat(),
            "heures": heures,
            "type_pointage": type_pointage,
            "description": description,
            "created_at": datetime.now().isoformat()
        }
        response = sb.table("pointages").insert(payload).execute()
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement: {str(e)}")
        return False

def delete_employee(employee_id):
    """Delete an employee"""
    try:
        sb.table("employees").delete().eq("id", employee_id).execute()
        return True
    except Exception as e:
        st.error(f"Erreur lors de la suppression: {str(e)}")
        return False

def update_employee(subcontractor_id, data):
    """Update employee information"""
    try:
        sb.table("employees").update(data).eq("id", subcontractor_id).execute()
        return True
    except Exception as e:
        st.error(f"Errour during update: {str(e)}")
        return False

def add_employee(user_id, nom, prenom, poste, taux_horaire, tel, email):
    """Add a new employee"""
    try:
        payload = {
            "user_id": user_id,
            "nom": nom,
            "prenom": prenom,
            "poste": poste,
            "taux_horaire": taux_horaire,
            "tel": tel,
            "email" : email,
            "actif": True,
            "created_at": datetime.now().isoformat()
        }
        response = sb.table("employees").insert(payload).execute()
        return True
    except Exception as e:
        st.error(f"Error during insert: {str(e)}")
        return False

def format_number(value):
    """Format number with French locale (comma as decimal separator)"""
    if value is None:
        return "0,00"
    return f"{value:.2f}".replace(".", ",")

def get_week_range(date_obj):
    """Get Monday and Sunday of the week for a given date"""
    monday = date_obj - timedelta(days=date_obj.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday

# TAB 1: SAISIE POINTAGE
# TAB 2: EMPLOYES
# TAB 3: RECAPITULATIF

tab1, tab2, tab3 = st.tabs(["📝 Saisie Pointage", "👥 Employés", "📊 Récapitulatif"])

# ============================================================================
# TAB 1: SAISIE POINTAGE
# ============================================================================
with tab1:
    st.subheader("Saisie des Pointages")

    col1, col2 = st.columns(2)

    with col1:
        selected_chantier = chantier_selector(user_id, "Sélectionnez un chantier")

    with col2:
        selected_date = st.date_input(
            "Date",
            value=date.today(),
            key="pointage_date"
        )

    if selected_chantier is None:
        st.warning("Veuillez sélectionner un chantier pour continuer")
    else:
        employes = get_employes(user_id)

        if not employes:
            st.info("Aucun employé enregistré. Veuillez en ajouter dans l'onglet 'Employes")
        else:
            st.write("**Enregistrement des heures de travail**")

            # Initialize session state for pointage entries
            if "pointage_entries" not in st.session_state:
                st.session_state.pointage_entries = {}

            # Create input grid for each active employee
            col1, col2, col3, col4 = st.columns([2, 1.5, 1.5, 2])
            with col1:
                st.write("**Employå**")
            with col2:
                st.write("**Heures**")
            with col3:
                st.write("**Type**")
            with col4:
                st.write("**Description**")

            st.divider()

            pointage_data = []

            for emp in employes:
                if emp.get("actif", True):
                    emp_id = emp["id"]
                    emp_name = f"{emp['prenom']} {emp['nom']}"

                    col1, col2, col3, col4 = st.columns([2, 1.5, 1.5, 2])

                    with col1:
                        st.write(emp_name)

                    with col2:
                        heures = st.number_input(
                            "h",
                            min_value=0.0,
                            max_value=24.0,
                            step=0.5,
                            key=f"heures_{emp_id}",
                            label_visibility="collapsed"
                        )

                    with col3:
                        type_pointage = st.selectbox(
                            "Type",
                            ["normal", "supplementaire", "nuit", "weekend"],
                            key=f"type_{emp_id}",
                            label_visibility="collapsed"
                        )

                    with col4:
                        description = st.text_input(
                            "Description",
                            key=f"desc_{emp_id}",
                            label_visibility="collapsed",
                            placeholder="Têches effectués"
                        )

                    if heures > 0:
                        pointage_data.append({
                            "employe_id": emp_id,
                            "employee_name": emp_name,
                            "heures": heures,
                            "type": type_pointage,
                            "description": description
                        })

            st.divider()

            # Save button
            if st.button("✅ Enregistrer les pointages", type="primary", use_container_width=True):
                if not pointage_data:
                    st.warning("Veuillez saisir au moins une entrée de pointage")
                else:
                    success_count = 0
                    for entry in pointage_data:
                        if save_pointage(
                            user_id,
                            selected_chantier,
                            entry["employe_id"],
                            selected_date,
                            entry["heures"],
                            entry["type"],
                            entry["description"]
                        ):
                            success_count += 1

                    if success_count == len(pointage_data):
                        st.success(f"✅ {success_count} pointage(s) saved")
                    else:
                        st.warning(f"➆ {;.ccount}/{len(pointage_data)} pointages saved")

            # Weekly summary
            st.write("---")
            st.subheader("📅 Résumé Hebdomadaire")

            monday, sunday = get_week_range(selected_date)
            week_pointages = get_pointages(user_id, monday, sunday)

            if week_pointages:
                df_week = pd.DataFrame(week_pointages)

                # Aggregate by employee and type
                if "employe_id" in df_week.columns and "type_pointage" in df_week.columns:
                    summary = df_week.groupby(["employe_id", "type_pointage"])["heures"].sum().reset_index()

                    # Get employee names
                    emp_map = {emp["id"]: f"{emp['prenom']} {emp['nom']}" for emp in employes}
                    summary["employee"] = summary["employee_id"].map(emp_map)

                    summary_pivot = summary.pivot_table(
                        index="employee",
                        columns="type_pointage",
                        values="heures",
                        fill_value=0,
                        aggfunc="sum"
                    )
                    summary_pivot["Total"] = summary_pivot.sum(axis=1)

                    # Format for display
                    display_df = summary_pivot.applymap(lambda x: format_number(x) if x > 0 else "-")

                    st.dataframe(display_df, use_container_width=True)

                    # Total week hours
                    total_heures = summary["heures"].sum()
                    st.metric("Total week hours", format_number(total_heures))
                else:
                    st.info("No time entries for this week")


# ============================================================================
# TAB 2: EMPLOYES
# ============================================================================
with tab2:
    st.subheader("Employe Management")

    # Get all employees
    employees = get_employes(user_id)

    # Add new employee form
    with st.expander("▕ Add New Employee", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            new_nom = st.text_input("Last Name", key="new_nom")
            new_prenom = st.text_input("First Name", key="new_prenom")
            new_poste = st.text_input("Position", key="new_poste")

        with col2:
            new_taux = st.number_input(
                "Hourly Rate (€)",
                min_value=0.0,
                step=0.5,
                key="new_taux",
                value=15.0)
                new_tel = st.text_input("Phone", key="new_tel")
                new_email = st.text_input("Email", key="new_email")

        if st.button("Add Employee", key="btn_add_emp", use_container_width=True):
            if not new_nom or not new_prenom:
                st.error("Champ "Last Name" and "First Name" are required")
            else:
                if add_employee(user_id, new_nom, new_prenom, new_poste, new_taux, new_tel, new_email):
                    st.success("��� Employee Added")
                    st.rerun()

    # List all employees
    if employees:
        st.write(f"**{len(employees)} Employees Registered**")
        st.divider()

        for emp in employees:
            with st.expander(f"👄D ^{.�whf\": prenom f+ contractors_id str } - {emp.get("poste", "N/A")}", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    edit_nom = st.text_input("Last Name", value=emp.get("nom", ""), key=f"edit_nom_{emp['id']}")
                    edit_prenom = st.text_input("First Name", value=emp.get("prenom", ""), key=f"edit_prenom_{emp['id']}")
                    edit_poste = st.text_input("Position", value=emp.get("poste", ""), key=f"edit_poste_{emp['id']}")

                with col2:
                    edit_taux = st.number_input("Hourly Rate (€)", value=emp.get("taux_horaire", 15.0), step=0.5, key=f"edit_taux_{emp['id']}")
                    edit_tel = st.text_input("Phone", value=emp.get("tel", ""), key=f"edit_tel_{emp['id']}")
                    edit_email = st.text_input("Email", value=emp.get("email", ""), key=f"edit_email_{emp['id']}")

                edit_actif = st.checkbox("Active", value=emp.get("actif", True), key=f"edit_actif_{emp['id']}")

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("💾 Update", key=f"btn_update_{emp['id']}", use_container_width=True):
                        update_data = {
                            "nom": edit_nom,
                            "prenom": edit_prenom,
                            "poste": edit_poste,
                            "taux_horaire": edit_taux,
                            "tel": edit_tel,
                            "email": edit_email,
                            "actif": edit_actif
                        }
                        if update_employee(emp["id"], update_data):
                            st.success("✅ Employee Updated")
                            st.rerun()

                with col2:
                    if st.button("🗑️ Delete", key=f"btn_delete_{emp['id']}", use_container_width=True):
                        if delete_employee(emp["id"]):
                            st.success("��� Employee Deleted")
                            st.rerun()
    else:
        st.info("No employees registered")


# ============================================================================
# TAB 3: REBICAPITULATIF
# ============================================================================
with tab3:
    st.subheader("Time Tracking Summary")

    # Date range filter
    col1, col2 = st.columns(2)

    with col1:
       # Default to first day of current month 
        default_start = date(date.today().year, date.today().month, 1)
        start_date = st.date_input("Start Date", value=default_start, key="recap_start")

    with col2:
        # Default to today
        end_date = st.date_input("End Date", value=date.today(), key="recap_end")

    if start_date > end_date:
        st.error("Start Date must be before End Date")
    else:
        # Get pointages for the period
        pointages = get_pointages(user_id, start_date, end_date)
        employees = get_employees(user_id)

        if not pointages:
            st.info("No time entries for the selected period")
        else:
            df = pd.DataFrame(pointages)

            # KPIs
            st.write("**Key Indicators**")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_heures = df["heures"].sum()
                st.metric("Total Hours", format_number(total_heures))

            with col2:
                # Calculate estimated cost
                emp_map = {emp["id"]: emp.get("taux_horaire", 0) for emp in employees}
                df["cost"] = df.apply(lambda row: row["heures"] * emp_map.get(row["employee_id"], 0), axis=1)
                total_cost = df["cost"].sum()
                st.metric("Estimated Cost (€)", format_number(total_cost))

            with col3:
                nb_pointages = len(df)
                st.metric("Number of Entries", nb_pointages)

            with col4:
                nb_employees_active = df["employee_id"].nunique()
                st.metric("Active Employees", nb_employees_active)

            st.divider()

            # Per-employee summary
            st.subheader("�� Summary by Employee")

            emp_summary = []
            for emp in employees:
                emp_id = emp["id"]
                emp_pointages = df[df["employee_id"] == emp_id]

                if len(emp_pointages) > 0:
                    hours_normal = emp_pointages[emp_pointages["type_pointage"] == "normal"]["hours"].sum()
                    hours_supp = emp_pointages[emp_pointages["type_pointage"] == "supplementaire"]["hours"].sum()
                    hours_night = emp_pointages[emp_pointages["type_pointage"] == "nuit"]["hours"].sum()
                    hours_weekend = emp_pointages[emp_pointages["type_pointage"] == "weekend"]["hours"].sum()
                    total_hours_emp = hours_normal + hours_supp + hours_night + hours_weekend

                    taux = emp.get("taux_horaire", 0)
                    cout = total_hours_emp * taux

                    emp_summary.append({
                        "Employee": f"{emp['prenom']} {emp['nom']}",
                        "Normal": hours_normal,
                        "Supplementary": hours_supp,
                        "Night": hours_night,
                        "Weekend": hours_weekend,
                        "Total": total_hours_emp,
                        "Rate (€/h)": taux,
                        "Cost (€)": cout
                    })

            if emp_summary:
                df_emp = pd.DataFrame(emp_summary)
                # Format for display
                display_cols = ["Normal", "Supplementary", "Night", "Weekend", "Total", "Rate (€/h)", "Cost (€)"]
                for col in display_cols:
                    df_emp[col] = df_emp[col].apply(lambda x: format_number(x) if x > 0 else "-")

                st.dataframe(df_emp, use_container_width=True)

            st.divider()

            # Per-chantier summary
            st.subheader(�ބ Summary by Project")

            if "chantier_id" in df.columns:
                chantier_summary = []
                for chantier_id in df["chantier_id"].unique():
                    chantier_pointages = df[df["chantier_id"] == chantier_id]
                    hours_chantier = chantier_pointages["hours"].sum()
                    cost_chantier = chantier_pointages["cost"].sum()

                    chantier_summary.append({
                        "Project": str(chantier_id),
                        "Total Hours": hours_chantier,
                        "Estimated Cost (€)": cost_chantier
                    })

                if chantier_summary:
                    df_chantier = pd.DataFrame(chantier_summary)
                    df_chantier["Total Hours"] = df_chantier["Total Hours"].apply(format_number)
                    df_chantier["Estimated Cost (€)"] = df_chantier}
["Estimated Cost (€)"].apply(format_number)

                st.dataframe(df_chantier, use_container_width=True)

            st.divider()

            # Full detail table (export-ready)
            st.subheader()📈 Complete Details")

            detail_df = df[["date", "employee_id", "type_pointage", "hours", "description"]].copy()
            detail_df["Employee"] = detail_df["employee_id"].map(
                lambda x: next((f"{emp['prenom']} {emp['nom']}" for emp in employees if emp["id"] == x), "Unknown")
            )
            detail_df = detail_df[["date", "Employee", "type_pointage", "hours", "description"]]
            detail_df.columns = ["Date", "Employee", "Type", "Hours", "Description"]

            st.dataframe(detail_df, use_container_width=True)

            # Export option
            csv_data = detail_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"pointages_{start_date}_{end_date}.csv",
                mime="text/csv",
                use_container_width=True
            )
