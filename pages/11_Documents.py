"""
Page 11 — Gestion Documentaire
Upload, téléchargement et organisation des documents par chantier.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from datetime import datetime
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector
from lib import db, storage
from utils import GLOBAL_CSS

page_setup(title="Documents", icon="📁")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
user_id = st.session_state.get("user_id")
render_saas_sidebar(user_id)

st.title("📁 Gestion Documentaire")

chantier = chantier_selector(key="doc_chantier")
if not chantier:
    st.stop()

# ─── Upload ─────────────────────────────────────────────────────────────────
st.subheader("📤 Importer un document")
doc_type = st.selectbox("Type de document", ["Plan", "DCE", "Devis", "Facture", "Étude", "Contrat", "PV", "Photo", "Autre"], key="doc_type_upload")
uploaded = st.file_uploader("Fichier", type=["pdf", "docx", "xlsx", "csv", "png", "jpg", "txt"], key="doc_upload")

if uploaded:
    if st.button("📤 Uploader", type="primary"):
        with st.spinner("Upload en cours..."):
            try:
                file_result = storage.upload_file(
                    file_bytes=uploaded.getvalue(),
                    filename=uploaded.name,
                    chantier_id=chantier["id"],
                    famille=doc_type,
                    doc_type=doc_type.lower(),
                )
                if file_result:
                    st.success(f"✅ Document '{uploaded.name}' uploadé avec succès.")
                    st.rerun()
                else:
                    st.error("Erreur lors de l'upload. Vérifiez que le stockage est configuré.")
            except Exception as e:
                st.error(f"Erreur : {str(e)[:100]}")

# ─── Documents existants ────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Documents du chantier")

# Filtres
filter_type = st.selectbox("Filtrer par type", ["Tous", "Plan", "DCE", "Devis", "Facture", "Étude", "Contrat", "PV", "Photo", "Autre"], key="doc_filter")

docs = db.get_documents(chantier_id=chantier["id"])
if filter_type != "Tous":
    docs = [d for d in docs if d.get("type", d.get("famille", "")) == filter_type]

if docs:
    total_size = sum(d.get("taille", d.get("file_size_bytes", 0)) or 0 for d in docs)
    size_display = f"{total_size / 1024 / 1024:.1f} Mo" if total_size > 1024 * 1024 else f"{total_size / 1024:.0f} Ko"
    st.info(f"📊 {len(docs)} documents — {size_display}")

    ICONS = {"Plan": "📐", "DCE": "📋", "Devis": "💰", "Facture": "🧾", "Étude": "📝", "Contrat": "📄", "PV": "📝", "Photo": "📷"}

    for doc in docs:
        doc_famille = doc.get("type", doc.get("famille", "Autre"))
        icon = ICONS.get(doc_famille, "📄")
        nom = doc.get("nom", doc.get("filename", "N/A"))
        taille = doc.get("taille", doc.get("file_size_bytes", 0)) or 0
        taille_str = f"{taille / 1024:.0f} Ko" if taille < 1024 * 1024 else f"{taille / 1024 / 1024:.1f} Mo"
        date = str(doc.get("created_at", ""))[:10]

        col1, col2, col3 = st.columns([4, 2, 1])
        col1.markdown(f"{icon} **{nom}**")
        col2.caption(f"{doc_famille} — {taille_str} — {date}")

        # Téléchargement
        storage_path = doc.get("storage_path", "")
        if storage_path and col3.button("📥", key=f"dl_{doc.get('id', '')}", help="Télécharger"):
            try:
                url = storage.get_signed_url(storage_path)
                if url:
                    st.markdown(f"[🔗 Télécharger le document]({url})")
                else:
                    st.warning("Fichier non disponible dans le stockage.")
            except Exception:
                st.warning("Erreur lors de la génération du lien.")
else:
    hint = " Essayez de modifier le filtre." if filter_type != "Tous" else ""
    st.info(f"Aucun document pour ce chantier.{hint}")

# ─── Usage stockage ───────────────────────────────────────────────────────
st.markdown("---")
st.subheader("💾 Utilisation du stockage")
try:
    usage = storage.get_storage_usage(user_id)
    if usage:
        plan = (db.get_profile(user_id) or {}).get("subscription_plan", "free")
        limit_mb = {"free": 50, "pro": 5120, "team": 20480}.get(plan, 50)
        used_mb = usage.get("total_bytes", 0) / 1024 / 1024
        pct = min(used_mb / limit_mb, 1.0) if limit_mb > 0 else 0

        c1, c2 = st.columns(2)
        c1.metric("📂 Documents", usage.get("nb_documents", 0))
        c2.metric("💾 Espace utilisé", f"{used_mb:.1f} Mo / {limit_mb} Mo")
        st.progress(pct, text=f"{used_mb:.1f} Mo utilisés sur {limit_mb} Mo ({pct*100:.0f}%)")
    else:
        st.info("Aucune donnée de stockage disponible.")
except Exception as e:
    st.warning(f"Impossible de charger les statistiques de stockage : {str(e)[:80]}")
