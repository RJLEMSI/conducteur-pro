"""
import_manager.py — Import de données client (CSV, Excel, JSON).
Permet d'importer la base de données complète d'un client :
chantiers, factures, devis, étapes, documents.
"""
import io
import json
import streamlit as st
import pandas as pd
from datetime import datetime
from lib.supabase_client import get_supabase_client
from lib.db import (
    create_chantier, create_facture, create_devis,
    create_etape, create_document, log_activity
)


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATES CSV
# ═══════════════════════════════════════════════════════════════════════════════

TEMPLATE_CHANTIERS = """nom,client_nom,client_email,adresse,code_postal,ville,statut,budget_ht,facture_ht,encaisse_ht,date_debut,date_fin,avancement_pct,metier,notes
Résidence Les Pins,SCI Les Pins,contact@scipins.fr,123 Rue Lyon,69000,Lyon,En cours,285000,142500,114000,2025-01-15,2025-06-30,50,Maçon,Phase 2 en cours
Villa Beaumont,M. Beaumont Jean,,45 Rue Beaumont,69100,Villeurbanne,En cours,67000,20000,10000,2025-03-01,2025-07-15,25,Général,"""

TEMPLATE_FACTURES = """chantier_nom,numero,client_nom,type_facture,objet,date_facture,montant_ht,tva_pct,statut
Résidence Les Pins,FACT-2025-001,SCI Les Pins,Situation,Situation n°1 - Fondations,2025-02-15,71250,20,Payée
Résidence Les Pins,FACT-2025-002,SCI Les Pins,Situation,Situation n°2 - Gros oeuvre,2025-03-15,71250,20,Envoyée"""

TEMPLATE_ETAPES = """chantier_nom,nom,responsable,date_echeance,statut,priorite
Résidence Les Pins,Livraison armatures HA,Chef chantier Dupont,2025-04-15,À faire,Haute
Résidence Les Pins,Coulage dalle R+1,Équipe maçonnerie,2025-04-22,À faire,Haute"""


def get_template_csv(template_type: str) -> str:
    """Retourne le template CSV pour un type donné."""
    templates = {
        "chantiers": TEMPLATE_CHANTIERS,
        "factures": TEMPLATE_FACTURES,
        "etapes": TEMPLATE_ETAPES,
    }
    return templates.get(template_type, "")


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def validate_chantier_row(row: dict) -> dict:
    """Valide une ligne de chantier. Retourne {valid: bool, errors: list, data: dict}."""
    errors = []
    data = {}

    # Nom obligatoire
    nom = str(row.get("nom", "")).strip()
    if not nom:
        errors.append("Nom du chantier manquant")
    data["nom"] = nom

    # Client
    data["client_nom"] = str(row.get("client_nom", "")).strip()
    data["client_email"] = str(row.get("client_email", "")).strip()
    data["adresse"] = str(row.get("adresse", "")).strip()
    data["code_postal"] = str(row.get("code_postal", "")).strip()
    data["ville"] = str(row.get("ville", "")).strip()
    data["localisation"] = f"{data['ville']} ({data['code_postal'][:2]})" if data["ville"] else ""
    data["notes"] = str(row.get("notes", "")).strip()
    data["metier"] = str(row.get("metier", "")).strip()
    data["lot"] = str(row.get("lot", "")).strip()
    data["responsable"] = str(row.get("responsable", "")).strip()

    # Statut
    statut = str(row.get("statut", "Planifié")).strip()
    valid_statuts = ["En cours", "Planifié", "Terminé", "En attente", "En retard", "Archivé"]
    if statut not in valid_statuts:
        statut = "Planifié"
    data["statut"] = statut

    # Montants
    for field in ["budget_ht", "facture_ht", "encaisse_ht"]:
        try:
            val = float(row.get(field, 0) or 0)
            data[field] = val
        except (ValueError, TypeError):
            data[field] = 0
            errors.append(f"{field} : valeur non numérique")

    # Avancement
    try:
        av = int(float(row.get("avancement_pct", 0) or 0))
        data["avancement_pct"] = max(0, min(100, av))
    except (ValueError, TypeError):
        data["avancement_pct"] = 0

    # Dates
    for field in ["date_debut", "date_fin"]:
        val = str(row.get(field, "")).strip()
        if val:
            try:
                parsed = pd.to_datetime(val).strftime("%Y-%m-%d")
                data[field] = parsed
            except Exception:
                errors.append(f"{field} : format de date invalide ({val})")
                data[field] = None
        else:
            data[field] = None

    return {"valid": len(errors) == 0, "errors": errors, "data": data}


def validate_facture_row(row: dict, chantier_map: dict) -> dict:
    """Valide une ligne de facture."""
    errors = []
    data = {}

    # Chantier
    chantier_nom = str(row.get("chantier_nom", "")).strip()
    chantier_id = chantier_map.get(chantier_nom)
    if not chantier_id:
        errors.append(f"Chantier '{chantier_nom}' non trouvé")
    data["chantier_id"] = chantier_id

    # Numéro
    numero = str(row.get("numero", "")).strip()
    if not numero:
        numero = f"FACT-{datetime.now().strftime('%Y')}-{datetime.now().strftime('%f')[:3]}"
    data["numero"] = numero
    data["client_nom"] = str(row.get("client_nom", "")).strip()
    data["type_facture"] = str(row.get("type_facture", "Situation")).strip()
    data["objet"] = str(row.get("objet", "")).strip()

    # Date
    val = str(row.get("date_facture", "")).strip()
    if val:
        try:
            data["date_facture"] = pd.to_datetime(val).strftime("%Y-%m-%d")
        except Exception:
            data["date_facture"] = None
    else:
        data["date_facture"] = None

    # Montants
    try:
        montant_ht = float(row.get("montant_ht", 0) or 0)
        data["montant_ht"] = montant_ht
    except (ValueError, TypeError):
        data["montant_ht"] = 0
        errors.append("montant_ht : valeur non numérique")

    try:
        tva_pct = float(row.get("tva_pct", 20) or 20)
        data["tva_pct"] = tva_pct
    except (ValueError, TypeError):
        data["tva_pct"] = 20.0

    data["tva_montant"] = data["montant_ht"] * data["tva_pct"] / 100
    data["montant_ttc"] = data["montant_ht"] + data["tva_montant"]

    # Statut
    statut = str(row.get("statut", "Brouillon")).strip()
    valid_statuts = ["Brouillon", "Envoyée", "Payée", "Retard"]
    if statut not in valid_statuts:
        statut = "Brouillon"
    data["statut"] = statut

    return {"valid": len(errors) == 0, "errors": errors, "data": data}


# ═══════════════════════════════════════════════════════════════════════════════
# IMPORT
# ═══════════════════════════════════════════════════════════════════════════════

def parse_file(uploaded_file, file_type: str = "csv") -> pd.DataFrame:
    """Parse un fichier uploadé (CSV, Excel, JSON) en DataFrame."""
    try:
        if file_type == "csv":
            return pd.read_csv(uploaded_file)
        elif file_type in ("xlsx", "xls", "excel"):
            return pd.read_excel(uploaded_file)
        elif file_type == "json":
            data = json.loads(uploaded_file.read().decode("utf-8"))
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                # Chercher la première clé qui contient une liste
                for key, val in data.items():
                    if isinstance(val, list):
                        return pd.DataFrame(val)
                return pd.DataFrame([data])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur lecture fichier : {e}")
        return pd.DataFrame()


def import_chantiers(df: pd.DataFrame) -> dict:
    """
    Importe des chantiers depuis un DataFrame.
    Retourne {success: int, errors: int, details: list}
    """
    results = {"success": 0, "errors": 0, "details": []}

    for idx, row in df.iterrows():
        validation = validate_chantier_row(row.to_dict())

        if validation["valid"]:
            created = create_chantier(validation["data"])
            if created:
                results["success"] += 1
                results["details"].append(f"✅ Ligne {idx+1} : {validation['data']['nom']} importé")
            else:
                results["errors"] += 1
                results["details"].append(f"❌ Ligne {idx+1} : Erreur création en base")
        else:
            results["errors"] += 1
            errors_str = ", ".join(validation["errors"])
            results["details"].append(f"⚠️ Ligne {idx+1} : {errors_str}")

    # Logger
    log_activity(
        action="import_chantiers",
        resource_type="chantier",
        details={"nb_success": results["success"], "nb_errors": results["errors"]}
    )

    return results


def import_factures(df: pd.DataFrame, chantier_map: dict) -> dict:
    """
    Importe des factures depuis un DataFrame.
    chantier_map = {nom_chantier: chantier_id}
    """
    results = {"success": 0, "errors": 0, "details": []}

    for idx, row in df.iterrows():
        validation = validate_facture_row(row.to_dict(), chantier_map)

        if validation["valid"]:
            created = create_facture(validation["data"])
            if created:
                results["success"] += 1
                results["details"].append(f"✅ Ligne {idx+1} : {validation['data']['numero']} importé")
            else:
                results["errors"] += 1
                results["details"].append(f"❌ Ligne {idx+1} : Erreur création en base")
        else:
            results["errors"] += 1
            errors_str = ", ".join(validation["errors"])
            results["details"].append(f"⚠️ Ligne {idx+1} : {errors_str}")

    log_activity(
        action="import_factures",
        resource_type="facture",
        details={"nb_success": results["success"], "nb_errors": results["errors"]}
    )

    return results


def import_etapes(df: pd.DataFrame, chantier_map: dict) -> dict:
    """Importe des étapes depuis un DataFrame."""
    results = {"success": 0, "errors": 0, "details": []}

    for idx, row in df.iterrows():
        chantier_nom = str(row.get("chantier_nom", "")).strip()
        chantier_id = chantier_map.get(chantier_nom)

        if not chantier_id:
            results["errors"] += 1
            results["details"].append(f"⚠️ Ligne {idx+1} : Chantier '{chantier_nom}' non trouvé")
            continue

        data = {
            "chantier_id": chantier_id,
            "nom": str(row.get("nom", "")).strip(),
            "responsable": str(row.get("responsable", "")).strip(),
            "statut": str(row.get("statut", "À faire")).strip(),
            "priorite": str(row.get("priorite", "Normale")).strip(),
        }

        # Date
        date_val = str(row.get("date_echeance", "")).strip()
        if date_val:
            try:
                data["date_echeance"] = pd.to_datetime(date_val).strftime("%Y-%m-%d")
            except Exception:
                data["date_echeance"] = None

        if data["nom"]:
            created = create_etape(data)
            if created:
                results["success"] += 1
                results["details"].append(f"✅ Ligne {idx+1} : {data['nom']} importé")
            else:
                results["errors"] += 1
                results["details"].append(f"❌ Ligne {idx+1} : Erreur création")
        else:
            results["errors"] += 1
            results["details"].append(f"⚠️ Ligne {idx+1} : Nom d'étape manquant")

    return results


def build_chantier_map() -> dict:
    """Construit un mapping {nom_chantier: chantier_id} pour les chantiers existants."""
    from lib.db import get_chantiers
    chantiers = get_chantiers(limit=500)
    return {ch["nom"]: ch["id"] for ch in chantiers}


def import_json_full(data: dict) -> dict:
    """
    Import complet depuis un export JSON ConducteurPro.
    Gère chantiers + étapes + factures.
    """
    results = {"chantiers": None, "etapes": None, "factures": None}

    # 1. Importer les chantiers d'abord
    if "chantiers" in data:
        df_ch = pd.DataFrame(data["chantiers"])
        results["chantiers"] = import_chantiers(df_ch)

    # Reconstruire le mapping
    chantier_map = build_chantier_map()

    # 2. Importer les étapes
    if "etapes" in data:
        df_et = pd.DataFrame(data["etapes"])
        # Renommer 'chantier' → 'chantier_nom' si nécessaire
        if "chantier" in df_et.columns and "chantier_nom" not in df_et.columns:
            df_et = df_et.rename(columns={"chantier": "chantier_nom"})
        if "etape" in df_et.columns and "nom" not in df_et.columns:
            df_et = df_et.rename(columns={"etape": "nom"})
        results["etapes"] = import_etapes(df_et, chantier_map)

    # 3. Importer les factures
    if "factures" in data:
        df_f = pd.DataFrame(data["factures"])
        if "chantier" in df_f.columns and "chantier_nom" not in df_f.columns:
            df_f = df_f.rename(columns={"chantier": "chantier_nom"})
        results["factures"] = import_factures(df_f, chantier_map)

    return results
