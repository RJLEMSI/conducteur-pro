import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
from datetime import datetime
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector
from lib import db, storage
from utils import GLOBAL_CSS

user_id = page_setup(title="Documents", icon="📁")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
render_saas_sidebar(user_id)

st.title("📁 Gestion Documentaire")

chantier = chantier_selector(key="docs_chantier")
if not chantier:
    st.stop()

# ─── Upload ───────────────────────────────────────────────────────────────────
st.subheader("📤 Importer un document")
doc_type = st.selectbox("Type de document", ["Plan", "DCE", "Devis", "Facture", "Étude", "Contrat", "PV", "Photo", "Autre"])
uploaded = st.file_uploader("Fichier", type=["pdf", "docx", "xlsx", "csv", "png", "jpg", "txt"], key="doc_upload")

if uploaded:
    if st.button("📤 Uploader", type="primary"):
        with st.spinner("Upload et chiffrement en cours..."):
            file_url = storage.upload_file(user_id, chantier["id"], uploaded.name, uploaded.getvalue(), doc_type.lower())
            if file_url:
                # Enregistrer en base
                db.save_document(user_id, chantier["id"], {
                    "nom": uploaded.name,
                    "type": doc_type,
                    "taille": len(uploaded.getvalue()),
                    "storage_path": file_url,
                })
                st.success(f"Document '{uploaded.name}' uploadé et chiffré.")
                st.rerun()
            else:
                st.error("Erreur lors de l'upload.")

# ─── Documents existants ──────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Documents du chantier")

# Filtres
filter_type = st.selectbox("Filtrer par type", ["Tous"] + ["Plan", "DCE", "Devis", "Facture", "Étude", "Contrat", "PV", "Photo", "Autre"])

docs = db.get_documents(chantier_id=chantier["id"])
if filter_type != "Tous":
    docs = [d for d in docs if d.get("type") == filter_type]

if docs:
    # Stats
    total_size = sum(d.get("taille", 0) or 0 for d in docs)
    st.info(f"📊 {len(docs)} documents — {total_size / 1024 / 1024:.1f} Mo total")
    
    for doc in docs:
        icon = {"Plan": "📐", "DCE": "📋", "Devis": "💰", "Facture": "🧾", "Étude": "📝", "Contrat": "📄", "PV": "📝", "Photo": "📸"}.get(doc.get("type", ""), "📁")
        col1, col2, col3 = st.columns([4, 2, 1])
        col1.write(f"{icon} **{doc.get('nom', 'N/A')}**")
        col2.write(f"{doc.get('type', 'N/A')} — {doc.get('created_at', '')[:10]}")
        
        # Téléchargement avec URL signée
        if col3.button("📥", key=f"dl_{doc.get('id', '')}"):
            url = storage.get_signed_url(doc.get("storage_path", ""))
            if url:
                st.markdown(f"[Télécharger]({url})")
            else:
                st.warning("Fichier non disponible.")
else:
    st.info("Aucun document pour ce chantier." + (" Essayez de modifier le filtre." if filter_type != "Tous" else ""))

# ─── Usage stockage ──────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("💾 Utilisation du stockage")
usage = storage.get_storage_usage(user_id)
if usage:
    limit_mb = {"free": 50, "pro": 5120, "team": 20480}.get(
        (db.get_profile(user_id) or {}).get("plan", "free"), 50
    )
    used_mb = usage.get("total_bytes", 0) / 1024 / 1024
    st.progress(min(used_mb / limit_mb, 1.0), text=f"{used_mb:.1f} Mo / {limit_mb} Mo")
