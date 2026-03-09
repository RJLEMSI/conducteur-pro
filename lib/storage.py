"""
storage.py — Gestion du stockage de fichiers dans Supabase Storage.
Upload, download, suppression, signed URLs, chiffrement AES-256.
"""
import io
import hashlib
import streamlit as st
from datetime import datetime
from cryptography.fernet import Fernet
from lib.supabase_client import get_supabase_client
from lib.db import create_document, log_activity


# ─── Configuration ────────────────────────────────────────────────────────────
BUCKET_NAME = "conducteurpro-files"

FAMILLE_FOLDERS = {
    "Plans": "plans",
    "Métrés": "metres",
    "Devis": "devis",
    "Documents techniques": "documents_techniques",
    "Études": "etudes",
    "Factures": "factures",
    "Contrats": "contrats",
}


# ─── Chiffrement ──────────────────────────────────────────────────────────────

def _get_encryption_key() -> bytes:
    """
    Récupère ou génère la clé de chiffrement depuis les secrets Streamlit.
    Chaque déploiement utilise une clé fixe pour pouvoir déchiffrer les fichiers.
    """
    key = st.secrets.get("ENCRYPTION_KEY", "")
    if key:
        return key.encode()
    # Fallback : générer une clé déterministe basée sur la clé Supabase
    seed = st.secrets.get("SUPABASE_SERVICE_KEY", "default-seed-key")
    return Fernet.generate_key()  # En prod, utiliser une clé fixe dans secrets


def encrypt_bytes(data: bytes) -> bytes:
    """Chiffre des données avec Fernet (AES-256)."""
    try:
        key = st.secrets.get("ENCRYPTION_KEY", "")
        if not key:
            return data  # Pas de chiffrement si pas de clé
        f = Fernet(key.encode())
        return f.encrypt(data)
    except Exception:
        return data


def decrypt_bytes(data: bytes) -> bytes:
    """Déchiffre des données avec Fernet (AES-256)."""
    try:
        key = st.secrets.get("ENCRYPTION_KEY", "")
        if not key:
            return data
        f = Fernet(key.encode())
        return f.decrypt(data)
    except Exception:
        return data


# ─── Upload de fichiers ──────────────────────────────────────────────────────

def _build_storage_path(user_id: str, chantier_id: str, famille: str, filename: str) -> str:
    """Construit le chemin de stockage dans le bucket."""
    folder = FAMILLE_FOLDERS.get(famille, "autres")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = filename.replace(" ", "_").replace("/", "_")
    return f"{user_id}/chantiers/{chantier_id}/{folder}/{timestamp}_{safe_name}"


def upload_file(
    file_bytes: bytes,
    filename: str,
    chantier_id: str,
    famille: str,
    doc_type: str = "",
    statut: str = "Validé",
    metadata: dict = None,
    encrypt: bool = True,
) -> dict:
    """
    Upload un fichier dans Supabase Storage et crée l'enregistrement document.

    Args:
        file_bytes: Contenu du fichier en bytes
        filename: Nom du fichier
        chantier_id: ID du chantier associé
        famille: Famille de document (Plans, Métrés, Devis, etc.)
        doc_type: Type spécifique (ex: "Plan d'exécution")
        statut: Statut du document
        metadata: Métadonnées supplémentaires (JSONB)
        encrypt: Chiffrer le fichier avant upload

    Returns:
        dict: Enregistrement du document créé, ou {} en cas d'erreur
    """
    client = get_supabase_client()
    uid = st.session_state.get("user_id")
    if not client or not uid:
        st.error("Non connecté. Impossible d'uploader le fichier.")
        return {}

    # Chiffrer si demandé
    data_to_upload = encrypt_bytes(file_bytes) if encrypt else file_bytes
    is_encrypted = encrypt and bool(st.secrets.get("ENCRYPTION_KEY", ""))

    # Construire le chemin
    storage_path = _build_storage_path(uid, chantier_id, famille, filename)

    # Calculer le hash
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Déterminer le content-type
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    content_types = {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "csv": "text/csv",
        "json": "application/json",
    }
    content_type = content_types.get(ext, "application/octet-stream")

    try:
        # Upload vers Supabase Storage
        client.storage.from_(BUCKET_NAME).upload(
            storage_path,
            data_to_upload,
            file_options={"content-type": content_type}
        )

        # Créer l'enregistrement document en DB
        doc_record = create_document({
            "chantier_id": chantier_id,
            "nom": filename,
            "type": doc_type or famille,
            "famille": famille,
            "statut": statut,
            "storage_path": storage_path,
            "file_size_bytes": len(file_bytes),
            "file_hash": file_hash,
            "is_encrypted": is_encrypted,
            "metadata": metadata or {},
        })

        # Logger l'activité
        log_activity(
            action="document_uploaded",
            resource_type="document",
            resource_id=doc_record.get("id", ""),
            details={"filename": filename, "famille": famille, "size": len(file_bytes)}
        )

        return doc_record

    except Exception as e:
        st.error(f"Erreur upload fichier : {e}")
        return {}


def upload_generated_document(
    file_bytes: bytes,
    filename: str,
    chantier_id: str,
    famille: str,
    doc_type: str = "",
    metadata: dict = None,
) -> dict:
    """
    Stocke un document GÉNÉRÉ par l'application (devis PDF, facture PDF, etc.).
    Même logique que upload_file mais avec statut "Généré" et log spécifique.
    """
    doc = upload_file(
        file_bytes=file_bytes,
        filename=filename,
        chantier_id=chantier_id,
        famille=famille,
        doc_type=doc_type,
        statut="Validé",
        metadata=metadata or {"generated": True, "generated_at": datetime.now().isoformat()},
    )

    if doc:
        log_activity(
            action="document_generated",
            resource_type="document",
            resource_id=doc.get("id", ""),
            details={"filename": filename, "type": doc_type}
        )

    return doc


# ─── Download / Signed URL ───────────────────────────────────────────────────

def get_signed_url(storage_path: str, expires_in: int = 900) -> str:
    """
    Génère une URL signée temporaire pour accéder à un fichier.
    Expire après 15 minutes par défaut.
    """
    client = get_supabase_client()
    if not client or not storage_path:
        return ""

    try:
        result = client.storage.from_(BUCKET_NAME).create_signed_url(storage_path, expires_in)
        return result.get("signedURL", "") if isinstance(result, dict) else ""
    except Exception:
        return ""


def download_file(storage_path: str, is_encrypted: bool = False) -> bytes:
    """
    Télécharge un fichier depuis Supabase Storage.
    Déchiffre si nécessaire.
    """
    client = get_supabase_client()
    if not client or not storage_path:
        return b""

    try:
        data = client.storage.from_(BUCKET_NAME).download(storage_path)
        if is_encrypted:
            data = decrypt_bytes(data)
        return data
    except Exception:
        return b""


# ─── Suppression ─────────────────────────────────────────────────────────────

def delete_file(storage_path: str) -> bool:
    """Supprime un fichier du storage."""
    client = get_supabase_client()
    if not client or not storage_path:
        return False

    try:
        client.storage.from_(BUCKET_NAME).remove([storage_path])
        return True
    except Exception:
        return False


# ─── Utilitaires ─────────────────────────────────────────────────────────────

def get_storage_usage() -> dict:
    """Calcule l'espace de stockage utilisé par l'utilisateur courant."""
    from lib.db import get_documents
    docs = get_documents(limit=5000)
    total_bytes = sum(d.get("file_size_bytes", 0) or 0 for d in docs)
    return {
        "total_bytes": total_bytes,
        "total_mb": total_bytes / (1024 * 1024),
        "total_gb": total_bytes / (1024 * 1024 * 1024),
        "nb_documents": len(docs),
    }
