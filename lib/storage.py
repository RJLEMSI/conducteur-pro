"""
storage.py  Gestion du stockage de fichiers dans Supabase Storage.
Upload, download, suppression, signed URLs, chiffrement AES-256.
"""

import io
import hashlib
import streamlit as st
from datetime import datetime
from cryptography.fernet import Fernet
from lib.supabase_client import get_supabase_client
from lib.db import create_document, log_activity

# Configuration
BUCKET_NAME = "conducteurpro-files"

# Mapping categories -> dossiers storage (correspond aux CATEGORIES de 11_Documents.py)
FAMILLE_FOLDERS = {
    "Plan": "plans",
    "Plans": "plans",
    "DCE": "dce",
    "Devis": "devis",
    "Facture": "factures",
    "Factures": "factures",
    "Etude": "etudes",
    "Etudes": "etudes",
    "Contrat": "contrats",
    "Contrats": "contrats",
    "PV": "pv",
    "Photo": "photos",
    "Metre": "metres",
    "Autre": "autres",
    # Accented versions
    "Mettre": "metres",
    # Legacy plural/accented versions
    "Documents techniques": "documents_techniques",
}


# Chiffrement

def _get_encryption_key() -> bytes:
    key = st.secrets.get("ENCRYPTION_KEY", "")
    if key:
        return key.encode()
    seed = st.secrets.get("SUPABASE_SERVICE_KEY", "default-seed-key")
    return Fernet.generate_key()


def encrypt_bytes(data: bytes) -> bytes:
    """Chiffre des donnees avec Fernet (AES-256)."""
    try:
        key = st.secrets.get("ENCRYPTION_KEY", "")
        if not key:
            return data
        f = Fernet(key.encode())
        return f.encrypt(data)
    except Exception:
        return data


def decrypt_bytes(data: bytes) -> bytes:
    """Dechiffre des donnees avec Fernet (AES-256)."""
    try:
        key = st.secrets.get("ENCRYPTION_KEY", "")
        if not key:
            return data
        f = Fernet(key.encode())
        return f.decrypt(data)
    except Exception:
        return data


# Upload de fichiers

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
    statut: str = "Valide",
    metadata: dict = None,
    encrypt: bool = True,
) -> dict:
    """
    Upload un fichier dans Supabase Storage et cree l'enregistrement document.
    """
    client = get_supabase_client()
    uid = st.session_state.get("user_id")

    if not client or not uid:
        st.error("Non connecte. Impossible d'uploader le fichier.")
        return {}

    # Chiffrer si demande
    data_to_upload = encrypt_bytes(file_bytes) if encrypt else file_bytes
    is_encrypted = encrypt and bool(st.secrets.get("ENCRYPTION_KEY", ""))

    # Construire le chemin
    storage_path = _build_storage_path(uid, chantier_id, famille, filename)

    # Calculer le hash
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Determiner le content-type
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    content_types = {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "csv": "text/csv",
        "json": "application/json",
        "txt": "text/plain",
        "dwg": "application/acad",
        "dxf": "application/dxf",
        "zip": "application/zip",
    }
    content_type = content_types.get(ext, "application/octet-stream")

    try:
        # Upload vers Supabase Storage
        client.storage.from_(BUCKET_NAME).upload(
            storage_path,
            data_to_upload,
            file_options={"content-type": content_type}
        )

        # Creer l'enregistrement document en DB
        doc_record = create_document({
            "chantier_id": chantier_id,
            "nom": filename,
            "type": famille,
            "famille": famille,
            "statut": statut,
            "storage_path": storage_path,
            "file_size_bytes": len(file_bytes),
            "file_hash": file_hash,
            "is_encrypted": is_encrypted,
            "metadata": metadata or {},
        })

        # Logger l'activite
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
    Stocke un document genere par l'application (devis PDF, facture PDF, etc.).
    """
    doc = upload_file(
        file_bytes=file_bytes,
        filename=filename,
        chantier_id=chantier_id,
        famille=famille,
        doc_type=doc_type,
        statut="Valide",
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


# Download / Signed URL

def get_signed_url(storage_path: str, expires_in: int = 900) -> str:
    """Genere une URL signee temporaire pour acceder a un fichier."""
    client = get_supabase_client()
    if not client or not storage_path:
        return ""
    try:
        result = client.storage.from_(BUCKET_NAME).create_signed_url(storage_path, expires_in)
        if isinstance(result, dict):
            return result.get("signedURL", result.get("signedUrl", ""))
        return ""
    except Exception:
        return ""


def download_file(storage_path: str, is_encrypted: bool = False) -> bytes:
    """Telecharge un fichier depuis Supabase Storage."""
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


# Suppression

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


# Utilitaires

def get_storage_usage(user_id: str = None) -> dict:
    """Calcule l'espace de stockage utilise par l'utilisateur."""
    from lib.db import get_documents
    docs = get_documents(user_id=user_id) if user_id else get_documents()
    total_bytes = sum(d.get("taille", d.get("file_size_bytes", 0)) or 0 for d in docs)
    return {
        "total_bytes": total_bytes,
        "total_mb": total_bytes / (1024 * 1024),
        "total_gb": total_bytes / (1024 * 1024 * 1024),
        "nb_documents": len(docs),
    }
