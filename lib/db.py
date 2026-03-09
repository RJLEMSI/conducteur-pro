"""
db.py — Opérations CRUD sur la base de données Supabase (PostgreSQL).
Chantiers, documents, factures, devis, plannings, étapes, études, métrés.
"""
import streamlit as st
from datetime import datetime, date
from lib.supabase_client import get_supabase_client


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _get_user_id():
    """Retourne le user_id courant depuis la session."""
    return st.session_state.get("user_id")


def _serialize_dates(data: dict) -> dict:
    """Convertit les objets date/datetime en strings ISO."""
    result = {}
    for k, v in data.items():
        if isinstance(v, (datetime, date)):
            result[k] = v.isoformat()
        elif v is not None:
            result[k] = v
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# CHANTIERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_chantiers(statut: str = None, limit: int = 100) -> list:
    """Récupère les chantiers de l'utilisateur courant."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return []

    query = client.table("chantiers").select("*").eq("user_id", uid)
    if statut:
        query = query.eq("statut", statut)
    query = query.order("created_at", desc=True).limit(limit)

    try:
        result = query.execute()
        return result.data or []
    except Exception as e:
        st.error(f"Erreur chargement chantiers : {e}")
        return []


def get_chantier(chantier_id: str) -> dict:
    """Récupère un chantier par son ID."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return {}

    try:
        result = client.table("chantiers").select("*").eq("id", chantier_id).eq("user_id", uid).execute()
        return result.data[0] if result.data else {}
    except Exception:
        return {}


def create_chantier(data: dict) -> dict:
    """Crée un nouveau chantier."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return {}

    data["user_id"] = uid
    data = _serialize_dates(data)

    try:
        result = client.table("chantiers").insert(data).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        st.error(f"Erreur création chantier : {e}")
        return {}


def update_chantier(chantier_id: str, data: dict) -> dict:
    """Met à jour un chantier existant."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return {}

    data["updated_at"] = datetime.now().isoformat()
    data = _serialize_dates(data)

    try:
        result = client.table("chantiers").update(data).eq("id", chantier_id).eq("user_id", uid).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        st.error(f"Erreur mise à jour chantier : {e}")
        return {}


def delete_chantier(chantier_id: str) -> bool:
    """Supprime un chantier (et ses documents associés via CASCADE)."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return False

    try:
        client.table("chantiers").delete().eq("id", chantier_id).eq("user_id", uid).execute()
        return True
    except Exception:
        return False


def count_chantiers() -> dict:
    """Retourne les compteurs de chantiers par statut."""
    chantiers = get_chantiers(limit=500)
    counts = {"total": 0, "En cours": 0, "Planifié": 0, "Terminé": 0, "En attente": 0, "En retard": 0}
    for ch in chantiers:
        counts["total"] += 1
        statut = ch.get("statut", "")
        if statut in counts:
            counts[statut] += 1
    return counts


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════════

def get_documents(chantier_id: str = None, famille: str = None,
                  statut: str = None, limit: int = 200) -> list:
    """Récupère les documents de l'utilisateur avec filtres optionnels."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return []

    query = client.table("documents").select("*").eq("user_id", uid)
    if chantier_id:
        query = query.eq("chantier_id", chantier_id)
    if famille:
        query = query.eq("famille", famille)
    if statut:
        query = query.eq("statut", statut)
    query = query.order("created_at", desc=True).limit(limit)

    try:
        result = query.execute()
        return result.data or []
    except Exception:
        return []


def create_document(data: dict) -> dict:
    """Crée un enregistrement de document."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return {}

    data["user_id"] = uid
    data = _serialize_dates(data)

    try:
        result = client.table("documents").insert(data).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        st.error(f"Erreur création document : {e}")
        return {}


def count_documents() -> dict:
    """Retourne les compteurs de documents par statut et famille."""
    docs = get_documents(limit=1000)
    counts = {"total": 0, "Validé": 0, "En attente": 0, "Brouillon": 0}
    familles = {}
    for doc in docs:
        counts["total"] += 1
        statut = doc.get("statut", "")
        if statut in counts:
            counts[statut] += 1
        fam = doc.get("famille", "Autre")
        familles[fam] = familles.get(fam, 0) + 1
    counts["familles"] = familles
    return counts


# ═══════════════════════════════════════════════════════════════════════════════
# FACTURES
# ═══════════════════════════════════════════════════════════════════════════════

def get_factures(chantier_id: str = None, statut: str = None, limit: int = 100) -> list:
    """Récupère les factures de l'utilisateur."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return []

    query = client.table("factures").select("*").eq("user_id", uid)
    if chantier_id:
        query = query.eq("chantier_id", chantier_id)
    if statut:
        query = query.eq("statut", statut)
    query = query.order("created_at", desc=True).limit(limit)

    try:
        result = query.execute()
        return result.data or []
    except Exception:
        return []


def create_facture(data: dict) -> dict:
    """Crée une nouvelle facture."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return {}

    data["user_id"] = uid
    data = _serialize_dates(data)

    try:
        result = client.table("factures").insert(data).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        st.error(f"Erreur création facture : {e}")
        return {}


def update_facture(facture_id: str, data: dict) -> dict:
    """Met à jour une facture."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return {}

    data["updated_at"] = datetime.now().isoformat()
    data = _serialize_dates(data)

    try:
        result = client.table("factures").update(data).eq("id", facture_id).eq("user_id", uid).execute()
        return result.data[0] if result.data else {}
    except Exception:
        return {}


def get_factures_stats() -> dict:
    """Calcule les statistiques financières des factures."""
    factures = get_factures(limit=500)
    stats = {
        "total_ht": 0, "total_ttc": 0,
        "encaisse": 0, "en_attente": 0, "en_retard": 0,
        "nb_total": len(factures), "nb_payees": 0, "nb_retard": 0,
    }
    for f in factures:
        montant_ttc = float(f.get("montant_ttc", 0) or 0)
        stats["total_ht"] += float(f.get("montant_ht", 0) or 0)
        stats["total_ttc"] += montant_ttc
        statut = f.get("statut", "")
        if statut == "Payée":
            stats["encaisse"] += montant_ttc
            stats["nb_payees"] += 1
        elif statut == "Retard":
            stats["en_retard"] += montant_ttc
            stats["nb_retard"] += 1
        else:
            stats["en_attente"] += montant_ttc
    return stats


# ═══════════════════════════════════════════════════════════════════════════════
# DEVIS
# ═══════════════════════════════════════════════════════════════════════════════

def get_devis(chantier_id: str = None, statut: str = None, limit: int = 100) -> list:
    """Récupère les devis de l'utilisateur."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return []

    query = client.table("devis").select("*").eq("user_id", uid)
    if chantier_id:
        query = query.eq("chantier_id", chantier_id)
    if statut:
        query = query.eq("statut", statut)
    query = query.order("created_at", desc=True).limit(limit)

    try:
        result = query.execute()
        return result.data or []
    except Exception:
        return []


def create_devis(data: dict) -> dict:
    """Crée un nouveau devis."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return {}

    data["user_id"] = uid
    data = _serialize_dates(data)

    try:
        result = client.table("devis").insert(data).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        st.error(f"Erreur création devis : {e}")
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
# ÉTAPES / PLANNING
# ═══════════════════════════════════════════════════════════════════════════════

def get_etapes(chantier_id: str = None, statut: str = None, limit: int = 200) -> list:
    """Récupère les étapes de planning."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return []

    query = client.table("etapes").select("*").eq("user_id", uid)
    if chantier_id:
        query = query.eq("chantier_id", chantier_id)
    if statut:
        query = query.eq("statut", statut)
    query = query.order("date_echeance").limit(limit)

    try:
        result = query.execute()
        return result.data or []
    except Exception:
        return []


def create_etape(data: dict) -> dict:
    """Crée une nouvelle étape."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return {}

    data["user_id"] = uid
    data = _serialize_dates(data)

    try:
        result = client.table("etapes").insert(data).execute()
        return result.data[0] if result.data else {}
    except Exception:
        return {}


def update_etape(etape_id: str, data: dict) -> dict:
    """Met à jour une étape."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return {}

    data = _serialize_dates(data)
    try:
        result = client.table("etapes").update(data).eq("id", etape_id).eq("user_id", uid).execute()
        return result.data[0] if result.data else {}
    except Exception:
        return {}


def get_plannings(chantier_id: str = None, limit: int = 50) -> list:
    """Récupère les plannings sauvegardés."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return []

    query = client.table("plannings").select("*").eq("user_id", uid)
    if chantier_id:
        query = query.eq("chantier_id", chantier_id)
    query = query.order("created_at", desc=True).limit(limit)

    try:
        result = query.execute()
        return result.data or []
    except Exception:
        return []


def save_planning(data: dict) -> dict:
    """Sauvegarde un planning."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return {}

    data["user_id"] = uid
    data = _serialize_dates(data)

    try:
        result = client.table("plannings").insert(data).execute()
        return result.data[0] if result.data else {}
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
# ÉTUDES / MÉTRÉS / DCE
# ═══════════════════════════════════════════════════════════════════════════════

def save_etude(data: dict) -> dict:
    """Sauvegarde une étude technique."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return {}
    data["user_id"] = uid
    data = _serialize_dates(data)
    try:
        result = client.table("etudes").insert(data).execute()
        return result.data[0] if result.data else {}
    except Exception:
        return {}


def save_metre(data: dict) -> dict:
    """Sauvegarde un métré."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return {}
    data["user_id"] = uid
    data = _serialize_dates(data)
    try:
        result = client.table("metres").insert(data).execute()
        return result.data[0] if result.data else {}
    except Exception:
        return {}


def save_dce(data: dict) -> dict:
    """Sauvegarde une analyse DCE."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return {}
    data["user_id"] = uid
    data = _serialize_dates(data)
    try:
        result = client.table("dces").insert(data).execute()
        return result.data[0] if result.data else {}
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
# ACTIVITY LOG
# ═══════════════════════════════════════════════════════════════════════════════

def log_activity(action: str, resource_type: str = "", resource_id: str = "", details: dict = None):
    """Enregistre une action dans le journal d'activité."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return

    try:
        client.table("activity_log").insert({
            "user_id": uid,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
        }).execute()
    except Exception:
        pass  # Ne pas bloquer l'app si le log échoue


# ═══════════════════════════════════════════════════════════════════════════════
# USER PROFILE
# ═══════════════════════════════════════════════════════════════════════════════

def update_user_profile(data: dict) -> dict:
    """Met à jour le profil utilisateur."""
    client = get_supabase_client()
    uid = _get_user_id()
    if not client or not uid:
        return {}

    data["updated_at"] = datetime.now().isoformat()
    try:
        result = client.table("user_profiles").update(data).eq("user_id", uid).execute()
        if result.data:
            st.session_state.user_profile = result.data[0]
        return result.data[0] if result.data else {}
    except Exception:
        return {}
