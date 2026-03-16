"""
ConducteurPro - Module de base de donnees (Supabase PostgreSQL).
Fournit toutes les operations CRUD pour les tables metier.
"""
import streamlit as st
from lib.supabase_client import get_supabase_client
from datetime import datetime


def _client():
    return get_supabase_client()


# --- Profils ---

def get_profile(user_id: str) -> dict | None:
    try:
        r = _client().table("user_profiles").select("*").eq("user_id", user_id).single().execute()
        return r.data
    except Exception:
        return None


def update_profile(user_id: str, data: dict) -> bool:
    try:
        _client().table("user_profiles").update(data).eq("user_id", user_id).execute()
        return True
    except Exception:
        return False


# --- Chantiers ---

def get_chantiers(user_id: str) -> list:
    try:
        r = _client().table("chantiers").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return r.data or []
    except Exception:
        return []


def get_chantier(chantier_id: str) -> dict | None:
    try:
        r = _client().table("chantiers").select("*").eq("id", chantier_id).single().execute()
        return r.data
    except Exception:
        return None


def create_chantier(user_id: str, data: dict) -> dict | None:
    try:
        data["user_id"] = user_id
        data["created_at"] = datetime.utcnow().isoformat()
        r = _client().table("chantiers").insert(data).execute()
        chantier = r.data[0] if r.data else None

        # Creer automatiquement les dossiers de stockage pour ce chantier
        if chantier:
            try:
                from lib.storage import create_chantier_folders
                create_chantier_folders(chantier["id"])
            except Exception:
                pass  # Ne pas bloquer la creation du chantier si les dossiers echouent

        return chantier
    except Exception:
        return None


def update_chantier(chantier_id: str, data: dict) -> bool:
    try:
        _client().table("chantiers").update(data).eq("id", chantier_id).execute()
        return True
    except Exception:
        return False


def delete_chantier(chantier_id: str) -> bool:
    try:
        _client().table("chantiers").delete().eq("id", chantier_id).execute()
        return True
    except Exception:
        return False


# --- Etudes / Analyses ---

def get_etudes(user_id: str = None, chantier_id: str = None, etude_type: str = None) -> list:
    try:
        q = _client().table("etudes").select("*")
        if user_id:
            q = q.eq("user_id", user_id)
        if chantier_id:
            q = q.eq("chantier_id", chantier_id)
        if etude_type:
            q = q.eq("type", etude_type)
        r = q.order("created_at", desc=True).execute()
        return r.data or []
    except Exception:
        return []


def save_etude(user_id: str, chantier_id: str, etude_type: str, titre: str, contenu: str, metadata: dict = None) -> dict | None:
    try:
        data = {
            "user_id": user_id,
            "chantier_id": chantier_id,
            "type": etude_type,
            "titre": titre,
            "contenu": contenu,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }
        r = _client().table("etudes").insert(data).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def delete_etude(etude_id: str) -> bool:
    try:
        _client().table("etudes").delete().eq("id", etude_id).execute()
        return True
    except Exception:
        return False


# --- Metres ---

def get_metres(chantier_id: str) -> list:
    try:
        r = _client().table("metres").select("*").eq("chantier_id", chantier_id).order("created_at", desc=True).execute()
        return r.data or []
    except Exception:
        return []


def save_metre(user_id: str, chantier_id: str, data: dict) -> dict | None:
    try:
        data["user_id"] = user_id
        data["chantier_id"] = chantier_id
        data["created_at"] = datetime.utcnow().isoformat()
        r = _client().table("metres").insert(data).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


# --- Devis ---

def get_devis(chantier_id: str = None, user_id: str = None) -> list:
    try:
        q = _client().table("devis").select("*")
        if chantier_id:
            q = q.eq("chantier_id", chantier_id)
        if user_id:
            q = q.eq("user_id", user_id)
        r = q.order("created_at", desc=True).execute()
        return r.data or []
    except Exception:
        return []


def save_devis(user_id: str, chantier_id: str, data: dict) -> dict | None:
    try:
        data["user_id"] = user_id
        data["chantier_id"] = chantier_id
        data["created_at"] = datetime.utcnow().isoformat()
        r = _client().table("devis").insert(data).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e


def update_devis(devis_id: str, data: dict) -> bool:
    try:
        _client().table("devis").update(data).eq("id", devis_id).execute()
        return True
    except Exception:
        return False


# --- Factures ---

def get_factures(chantier_id: str = None, user_id: str = None) -> list:
    try:
        q = _client().table("factures").select("*")
        if chantier_id:
            q = q.eq("chantier_id", chantier_id)
        if user_id:
            q = q.eq("user_id", user_id)
        r = q.order("created_at", desc=True).execute()
        return r.data or []
    except Exception:
        return []


def save_facture(user_id: str, chantier_id: str, data: dict) -> dict | None:
    try:
        data["user_id"] = user_id
        data["chantier_id"] = chantier_id
        data["created_at"] = datetime.utcnow().isoformat()
        r = _client().table("factures").insert(data).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None


def update_facture(facture_id: str, data: dict) -> bool:
    try:
        _client().table("factures").update(data).eq("id", facture_id).execute()
        return True
    except Exception:
        return False


# --- Etapes (Planning) ---

def get_etapes(chantier_id: str) -> list:
    try:
        r = _client().table("etapes").select("*").eq("chantier_id", chantier_id).order("ordre").execute()
        return r.data or []
    except Exception:
        return []


def save_etape(user_id: str, chantier_id: str, data: dict) -> dict | None:
    try:
        data["user_id"] = user_id
        data["chantier_id"] = chantier_id
        data["created_at"] = datetime.utcnow().isoformat()
        r = _client().table("etapes").insert(data).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def update_etape(etape_id: str, data: dict) -> bool:
    try:
        _client().table("etapes").update(data).eq("id", etape_id).execute()
        return True
    except Exception:
        return False


def delete_etape(etape_id: str) -> bool:
    try:
        _client().table("etapes").delete().eq("id", etape_id).execute()
        return True
    except Exception:
        return False


# --- Documents ---

def save_document(user_id: str, chantier_id: str, data: dict) -> dict | None:
    try:
        data["user_id"] = user_id
        data["chantier_id"] = chantier_id
        data["created_at"] = datetime.utcnow().isoformat()
        r = _client().table("documents").insert(data).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def create_document(data: dict) -> dict:
    """Cree un enregistrement de document dans la table documents."""
    client = _client()
    if not client:
        return data
    try:
        user_id = st.session_state.get("user_id")
        if user_id:
            data["user_id"] = user_id
        data["created_at"] = datetime.utcnow().isoformat()
        result = client.table("documents").insert(data).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]
        return data
    except Exception:
        return data


def get_documents(user_id: str = None, chantier_id: str = None, famille: str = None, doc_type: str = None) -> list:
    """Recupere les documents avec filtres optionnels."""
    client = _client()
    if not client:
        return []
    try:
        query = client.table("documents").select("*")
        if user_id:
            query = query.eq("user_id", user_id)
        if chantier_id:
            query = query.eq("chantier_id", chantier_id)
        if famille:
            query = query.eq("famille", famille)
        if doc_type:
            query = query.eq("type", doc_type)
        result = query.order("created_at", desc=True).execute()
        return result.data or []
    except Exception:
        return []


def delete_document(document_id: str) -> bool:
    """Supprime un document."""
    client = _client()
    if not client:
        return False
    try:
        client.table("documents").delete().eq("id", document_id).execute()
        return True
    except Exception:
        return False



def delete_devis(devis_id: str) -> bool:
    """Supprime un devis."""
    client = _client()
    if not client:
        return False
    try:
        client.table("devis").delete().eq("id", devis_id).execute()
        return True
    except Exception:
        return False


def delete_facture(facture_id: str) -> bool:
    """Supprime une facture."""
    client = _client()
    if not client:
        return False
    try:
        client.table("factures").delete().eq("id", facture_id).execute()
        return True
    except Exception:
        return False


def delete_metre(metre_id: str) -> bool:
    """Supprime un metre."""
    client = _client()
    if not client:
        return False
    try:
        client.table("metres").delete().eq("id", metre_id).execute()
        return True
    except Exception:
        return False


# --- Abonnements ---

def get_subscription(user_id: str) -> dict | None:
    try:
        r = _client().table("subscriptions").select("*").eq("user_id", user_id).eq("active", True).single().execute()
        return r.data
    except Exception:
        return None


def update_subscription(user_id: str, data: dict) -> bool:
    try:
        _client().table("subscriptions").upsert({**data, "user_id": user_id}).execute()
        return True
    except Exception:
        return False


# --- Statistiques Dashboard ---

def get_dashboard_stats(user_id: str) -> dict:
    try:
        chantiers = get_chantiers(user_id)
        devis = get_devis(user_id=user_id)
        factures = get_factures(user_id=user_id)

        total_devis = sum(float(d.get("montant_ht", 0) or 0) for d in devis)
        total_factures = sum(float(f.get("montant_ttc", 0) or 0) for f in factures)
        factures_payees = [f for f in factures if f.get("statut") == "payee"]
        total_paye = sum(float(f.get("montant_ttc", 0) or 0) for f in factures_payees)

        return {
            "nb_chantiers": len(chantiers),
            "nb_chantiers_actifs": len([c for c in chantiers if c.get("statut") == "en_cours"]),
            "nb_devis": len(devis),
            "total_devis_ht": total_devis,
            "nb_factures": len(factures),
            "total_factures_ttc": total_factures,
            "total_paye": total_paye,
            "taux_recouvrement": (total_paye / total_factures * 100) if total_factures > 0 else 0,
            "chantiers": chantiers,
            "devis": devis,
            "factures": factures,
        }
    except Exception:
        return {
            "nb_chantiers": 0, "nb_chantiers_actifs": 0, "nb_devis": 0,
            "total_devis_ht": 0, "nb_factures": 0, "total_factures_ttc": 0,
            "total_paye": 0, "taux_recouvrement": 0, "chantiers": [], "devis": [], "factures": [],
        }


# --- Activity Log ---

def log_activity(action: str, resource_type: str = "", resource_id: str = "", details: dict = None):
    """Enregistre une action dans le journal d'activite."""
    client = _client()
    if not client:
        return
    try:
        user_id = st.session_state.get("user_id")
        if not user_id:
            return
        client.table("activity_log").insert({
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
        }).execute()
    except Exception:
        pass


# --- Reunions ---

def get_reunions(user_id: str = None, chantier_id: str = None) -> list:
    """Recupere les reunions."""
    client = _client()
    if not client:
        return []
    try:
        query = client.table("reunions").select("*")
        if user_id:
            query = query.eq("user_id", user_id)
        if chantier_id:
            query = query.eq("chantier_id", chantier_id)
        result = query.order("date_reunion", desc=True).execute()
        return result.data or []
    except Exception:
        return []


def save_reunion(user_id: str, chantier_id: str, data: dict) -> dict | None:
    """Sauvegarde une reunion."""
    try:
        data["user_id"] = user_id
        data["chantier_id"] = chantier_id
        data["created_at"] = datetime.utcnow().isoformat()
        r = _client().table("reunions").insert(data).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def delete_reunion(reunion_id: str) -> bool:
    """Supprime une reunion."""
    try:
        _client().table("reunions").delete().eq("id", reunion_id).execute()
        return True
    except Exception:
        return False


# --- Aliases pour compatibilite import_manager ---
create_facture = save_facture
create_devis = save_devis
create_etape = save_etape

# Aliases accentes pour compatibilite fichiers git clone
get_étapes = get_etapes
save_étape = save_etape
update_étape = update_etape
delete_étape = delete_etape
create_étape = save_etape


# ─── Phases Chantier (Planning) ───────────────────────────────────────────────

def get_phases(chantier_id: str) -> list:
    try:
        r = _client().table("phases_chantier").select("*").eq("chantier_id", chantier_id).order("ordre").execute()
        return r.data or []
    except Exception:
        return []


def get_all_phases_user(user_id: str) -> list:
    try:
        r = _client().table("phases_chantier").select("*, chantiers(nom, adresse, statut)").eq("user_id", user_id).order("date_debut").execute()
        return r.data or []
    except Exception:
        return []


def save_phase(user_id: str, chantier_id: str, data: dict) -> dict | None:
    try:
        data["user_id"] = user_id
        data["chantier_id"] = chantier_id
        r = _client().table("phases_chantier").insert(data).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def update_phase(phase_id: str, data: dict) -> bool:
    try:
        _client().table("phases_chantier").update(data).eq("id", phase_id).execute()
        return True
    except Exception:
        return False


def delete_phase(phase_id: str) -> bool:
    try:
        _client().table("phases_chantier").delete().eq("id", phase_id).execute()
        return True
    except Exception:
        return False


def save_phases_batch(user_id: str, chantier_id: str, phases: list) -> bool:
    try:
        for p in phases:
            p["user_id"] = user_id
            p["chantier_id"] = chantier_id
        _client().table("phases_chantier").insert(phases).execute()
        return True
    except Exception:
        return False
