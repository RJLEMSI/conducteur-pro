"""
ConducteurPro — Module de base de données (Supabase PostgreSQL).
Fournit toutes les opérations CRUD pour les tables métier.
"""
from lib.supabase_client import get_supabase_client
from datetime import datetime


def _client():
    return get_supabase_client()


# ─── Profils ──────────────────────────────────────────────────────────────────

def get_profile(user_id: str) -> dict | None:
    """Récupère le profil utilisateur."""
    try:
        r = _client().table("user_profiles").select("*").eq("user_id", user_id).single().execute()
        return r.data
    except Exception:
        return None


def update_profile(user_id: str, data: dict) -> bool:
    """Met à jour le profil utilisateur."""
    try:
        _client().table("user_profiles").update(data).eq("user_id", user_id).execute()
        return True
    except Exception:
        return False


# ─── Chantiers ────────────────────────────────────────────────────────────────

def get_chantiers(user_id: str) -> list:
    """Récupère tous les chantiers de l'utilisateur."""
    try:
        r = _client().table("chantiers").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return r.data or []
    except Exception:
        return []


def get_chantier(chantier_id: str) -> dict | None:
    """Récupère un chantier par ID."""
    try:
        r = _client().table("chantiers").select("*").eq("id", chantier_id).single().execute()
        return r.data
    except Exception:
        return None


def create_chantier(user_id: str, data: dict) -> dict | None:
    """Crée un nouveau chantier."""
    try:
        data["user_id"] = user_id
        data["created_at"] = datetime.utcnow().isoformat()
        r = _client().table("chantiers").insert(data).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def update_chantier(chantier_id: str, data: dict) -> bool:
    """Met à jour un chantier."""
    try:
        _client().table("chantiers").update(data).eq("id", chantier_id).execute()
        return True
    except Exception:
        return False


def delete_chantier(chantier_id: str) -> bool:
    """Supprime un chantier et ses données associées."""
    try:
        _client().table("chantiers").delete().eq("id", chantier_id).execute()
        return True
    except Exception:
        return False


# ─── Études / Analyses ────────────────────────────────────────────────────────

def get_etudes(user_id: str = None, chantier_id: str = None, etude_type: str = None) -> list:
    """Récupère les études, avec filtrage optionnel."""
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
    """Sauvegarde une nouvelle étude/analyse."""
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
    """Supprime une étude."""
    try:
        _client().table("etudes").delete().eq("id", etude_id).execute()
        return True
    except Exception:
        return False


# ─── Métrés ───────────────────────────────────────────────────────────────────

def get_metres(chantier_id: str) -> list:
    """Récupère les métrés d'un chantier."""
    try:
        r = _client().table("metres").select("*").eq("chantier_id", chantier_id).order("created_at", desc=True).execute()
        return r.data or []
    except Exception:
        return []


def save_metre(user_id: str, chantier_id: str, data: dict) -> dict | None:
    """Sauvegarde un métré."""
    try:
        data["user_id"] = user_id
        data["chantier_id"] = chantier_id
        data["created_at"] = datetime.utcnow().isoformat()
        r = _client().table("metres").insert(data).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


# ─── Devis ────────────────────────────────────────────────────────────────────

def get_devis(chantier_id: str = None, user_id: str = None) -> list:
    """Récupère les devis."""
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
    """Sauvegarde un devis."""
    try:
        data["user_id"] = user_id
        data["chantier_id"] = chantier_id
        data["created_at"] = datetime.utcnow().isoformat()
        r = _client().table("devis").insert(data).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def update_devis(devis_id: str, data: dict) -> bool:
    """Met à jour un devis."""
    try:
        _client().table("devis").update(data).eq("id", devis_id).execute()
        return True
    except Exception:
        return False


# ─── Factures ─────────────────────────────────────────────────────────────────

def get_factures(chantier_id: str = None, user_id: str = None) -> list:
    """Récupère les factures."""
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
    """Sauvegarde une facture."""
    try:
        data["user_id"] = user_id
        data["chantier_id"] = chantier_id
        data["created_at"] = datetime.utcnow().isoformat()
        r = _client().table("factures").insert(data).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def update_facture(facture_id: str, data: dict) -> bool:
    """Met à jour une facture."""
    try:
        _client().table("factures").update(data).eq("id", facture_id).execute()
        return True
    except Exception:
        return False


# ─── Étapes (Planning) ────────────────────────────────────────────────────────

def get_etapes(chantier_id: str) -> list:
    """Récupère les étapes d'un chantier."""
    try:
        r = _client().table("etapes").select("*").eq("chantier_id", chantier_id).order("ordre").execute()
        return r.data or []
    except Exception:
        return []


def save_etape(user_id: str, chantier_id: str, data: dict) -> dict | None:
    """Sauvegarde une étape."""
    try:
        data["user_id"] = user_id
        data["chantier_id"] = chantier_id
        data["created_at"] = datetime.utcnow().isoformat()
        r = _client().table("etapes").insert(data).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def update_etape(etape_id: str, data: dict) -> bool:
    """Met à jour une étape."""
    try:
        _client().table("etapes").update(data).eq("id", etape_id).execute()
        return True
    except Exception:
        return False


def delete_etape(etape_id: str) -> bool:
    """Supprime une étape."""
    try:
        _client().table("etapes").delete().eq("id", etape_id).execute()
        return True
    except Exception:
        return False


# ─── Documents ────────────────────────────────────────────────────────────────

def get_documents(chantier_id: str = None, user_id: str = None, doc_type: str = None) -> list:
    """Récupère les documents."""
    try:
        q = _client().table("documents").select("*")
        if chantier_id:
            q = q.eq("chantier_id", chantier_id)
        if user_id:
            q = q.eq("user_id", user_id)
        if doc_type:
            q = q.eq("type", doc_type)
        r = q.order("created_at", desc=True).execute()
        return r.data or []
    except Exception:
        return []


def save_document(user_id: str, chantier_id: str, data: dict) -> dict | None:
    """Sauvegarde un document."""
    try:
        data["user_id"] = user_id
        data["chantier_id"] = chantier_id
        data["created_at"] = datetime.utcnow().isoformat()
        r = _client().table("documents").insert(data).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def delete_document(doc_id: str) -> bool:
    """Supprime un document."""
    try:
        _client().table("documents").delete().eq("id", doc_id).execute()
        return True
    except Exception:
        return False


# ─── Abonnements ──────────────────────────────────────────────────────────────

def get_subscription(user_id: str) -> dict | None:
    """Récupère l'abonnement actif de l'utilisateur."""
    try:
        r = _client().table("subscriptions").select("*").eq("user_id", user_id).eq("active", True).single().execute()
        return r.data
    except Exception:
        return None


def update_subscription(user_id: str, data: dict) -> bool:
    """Met à jour l'abonnement."""
    try:
        _client().table("subscriptions").upsert({**data, "user_id": user_id}).execute()
        return True
    except Exception:
        return False


# ─── Statistiques Dashboard ───────────────────────────────────────────────────

def get_dashboard_stats(user_id: str) -> dict:
    """Calcule les statistiques pour le tableau de bord."""
    try:
        chantiers = get_chantiers(user_id)
        devis = get_devis(user_id=user_id)
        factures = get_factures(user_id=user_id)
        
        # Montants
        total_devis = sum(float(d.get("montant_ht", 0) or 0) for d in devis)
        total_factures = sum(float(f.get("montant_ttc", 0) or 0) for f in factures)
        factures_payees = [f for f in factures if f.get("statut") == "payée"]
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
            "nb_chantiers": 0, "nb_chantiers_actifs": 0,
            "nb_devis": 0, "total_devis_ht": 0,
            "nb_factures": 0, "total_factures_ttc": 0,
            "total_paye": 0, "taux_recouvrement": 0,
            "chantiers": [], "devis": [], "factures": [],
        }

# ─── Documents ──────────────────────────────────────────────────────────────

def create_document(data: dict) -> dict:
    """Crée un enregistrement de document dans la table documents."""
    client = _client()
    if not client:
        return data
    try:
        user_id = st.session_state.get("user_id")
        if user_id:
            data["user_id"] = user_id
        result = client.table("documents").insert(data).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]
        return data
    except Exception:
        return data


def get_documents(user_id: str = None, chantier_id: str = None, famille: str = None) -> list:
    """Récupère les documents avec filtres optionnels."""
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


# ─── Activity Log ───────────────────────────────────────────────────────────

def log_activity(action: str, resource_type: str = "", resource_id: str = "", details: dict = None):
    """Enregistre une action dans le journal d'activité."""
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
        pass  # Ne pas bloquer l'app si le logging échoue


# ─── Aliases pour compatibilité import_manager ─────────────────────────────
create_facture = save_facture
create_devis = save_devis
create_etape = save_etape
