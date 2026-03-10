"""
Page 11 - Gestion Documentaire
Upload, tÃ©lÃ©chargement et organisation des documents par chantier.
Classification automatique intelligente des documents.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from datetime import datetime
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector
from lib import db, storage
from utils import GLOBAL_CSS

page_setup(title="Documents", icon="\U0001f4c1")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
user_id = st.session_state.get("user_id")
render_saas_sidebar(user_id)

st.title("\U0001f4c1 Gestion Documentaire")

chantier = chantier_selector(key="doc_chantier")
if not chantier:
    st.stop()


# --- Classification automatique ---
CATEGORIES = ["Plan", "DCE", "Devis", "Facture", "Ãtude", "Contrat", "PV", "Photo", "MÃ©trÃ©", "Autre"]

KEYWORD_MAP = {
    "devis": "Devis",
    "quotation": "Devis",
    "quote": "Devis",
    "facture": "Facture",
    "invoice": "Facture",
    "avoir": "Facture",
    "plan": "Plan",
    "coupe": "Plan",
    "facade": "Plan",
    "elevation": "Plan",
    "implantation": "Plan",
    "masse": "Plan",
    "situation": "Plan",
    "detail": "Plan",
    "dce": "DCE",
    "cctp": "DCE",
    "ccap": "DCE",
    "dpgf": "DCE",
    "cahier": "DCE",
    "rc": "DCE",
    "reglement": "DCE",
    "bpu": "DCE",
    "etude": "Ãtude",
    "etudes": "Ãtude",
    "rapport": "Ãtude",
    "diagnostic": "Ãtude",
    "analyse": "Ãtude",
    "thermique": "Ãtude",
    "acoustique": "Ãtude",
    "geotechnique": "Ãtude",
    "beton": "Ãtude",
    "structure": "Ãtude",
    "contrat": "Contrat",
    "marche": "Contrat",
    "avenant": "Contrat",
    "convention": "Contrat",
    "sous-traitance": "Contrat",
    "soustraitance": "Contrat",
    "pv": "PV",
    "proces": "PV",
    "compte-rendu": "PV",
    "compte_rendu": "PV",
    "cr_": "PV",
    "reunion": "PV",
    "reception": "PV",
    "ope": "PV",
    "metre": "MÃ©trÃ©",
    "metr": "MÃ©trÃ©",
    "quantitatif": "MÃ©trÃ©",
    "quantite": "MÃ©trÃ©",
    "dqe": "MÃ©trÃ©",
    "bordereau": "MÃ©trÃ©",
    "photo": "Photo",
    "img": "Photo",
    "image": "Photo",
    "chantier_photo": "Photo",
    "dsc": "Photo",
    "dcim": "Photo",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
PLAN_EXTENSIONS = {".dwg", ".dxf", ".dwf"}


def classify_file(filename: str) -> str:
    """Classifie un fichier selon son nom et son extension."""
    name_lower = filename.lower()
    _, ext = os.path.splitext(name_lower)

    # 1. Images -> Photo
    if ext in IMAGE_EXTENSIONS:
        # Sauf si le nom contient un mot-clÃ© spÃ©cifique
        for kw, cat in KEYWORD_MAP.items():
            if kw in name_lower and cat != "Photo":
                return cat
        return "Photo"

    # 2. Fichiers CAO -> Plan
    if ext in PLAN_EXTENSIONS:
        return "Plan"

    # 3. Recherche par mots-clÃ©s dans le nom
    # Nettoyer le nom : retirer extension, remplacer separateurs
    name_clean = name_lower.replace(ext, "")
    name_clean = name_clean.replace("-", " ").replace("_", " ").replace(".", " ")

    for kw, cat in KEYWORD_MAP.items():
        if kw in name_clean:
            return cat

    # 4. Pas de correspondance
    return "Autre"


# --- Upload ---
st.subheader("\U0001f4e4 Importer des documents")

auto_classify = st.toggle(
    "\U0001f916 Classification automatique",
    value=True,
    help="Quand activÃ©, les documents sont automatiquement classÃ©s (Devis, Facture, Plan, Ãtude, MÃ©trÃ©...) selon leur nom de fichier.",
)

if not auto_classify:
    doc_type = st.selectbox(
        "Type de document",
        CATEGORIES,
        key="doc_type_upload",
    )

uploaded_files = st.file_uploader(
    "Fichiers",
    type=["pdf", "docx", "xlsx", "csv", "png", "jpg", "jpeg", "txt", "dwg", "dxf", "zip"],
    accept_multiple_files=True,
    key="doc_upload",
    help="Glissez-dÃ©posez tous vos fichiers d'un coup. La classification se fait automatiquement.",
)

if uploaded_files:
    nb = len(uploaded_files)

    if auto_classify:
        # Classifier chaque fichier et afficher un aperÃªu
        classifications = {}
        for f in uploaded_files:
            cat = classify_file(f.name)
            classifications[f.name] = cat

        # Grouper par catÃ©gorie pour l'aperÃªu
        by_cat = {}
        for fname, cat in classifications.items():
            by_cat.setdefault(cat, []).append(fname)

        st.markdown(f"**\U0001f4ce {nb} fichier{'s' if nb > 1 else ''} dÃ©tectÃ©{'s' if nb > 1 else ''} :**")

        CAT_ICONS = {
            "Plan": "\U0001f4d0", "DCE": "\U0001f4d1", "Devis": "\U0001f4b0",
            "Facture": "\U0001f9fe", "Ãtude": "\U0001f4d6", "Contrat": "\U0001f4dc",
            "PV": "\U0001f4dd", "Photo": "\U0001f4f7", "MÃ©trÃ©": "\U0001f4cf",
            "Autre": "\U0001f4c4",
        }

        for cat in CATEGORIES:
            if cat in by_cat:
                icon = CAT_ICONS.get(cat, "\U0001f4c4")
                files_list = by_cat[cat]
                with st.expander(f"{icon} **{cat}** ({len(files_list)} fichier{'s' if len(files_list) > 1 else ''})", expanded=False):
                    for fname in files_list:
                        st.caption(f"  \u2022 {fname}")

        # Permettre de corriger la classification
        with st.expander("\u270f\ufe0f Corriger la classification", expanded=False):
            corrected = {}
            for f in uploaded_files:
                corrected[f.name] = st.selectbox(
                    f"{f.name}",
                    CATEGORIES,
                    index=CATEGORIES.index(classifications[f.name]) if classifications[f.name] in CATEGORIES else len(CATEGORIES) - 1,
                    key=f"correct_{f.name}",
                )
            classifications = corrected

        if st.button(f"\U0001f4e4 Uploader et classer {nb} fichier{'s' if nb > 1 else ''}", type="primary"):
            progress = st.progress(0, text="Upload en cours...")
            success_count = 0
            error_count = 0
            for i, uploaded in enumerate(uploaded_files):
                cat = classifications[uploaded.name]
                progress.progress(i / nb, text=f"Upload de {uploaded.name} -> {cat}...")
                try:
                    file_result = storage.upload_file(
                        file_bytes=uploaded.getvalue(),
                        filename=uploaded.name,
                        chantier_id=chantier["id"],
                        famille=cat,
                        doc_type=cat.lower(),
                    )
                    if file_result:
                        success_count += 1
                    else:
                        error_count += 1
                        st.warning(f"\u26a0\ufe0f Ãchec pour '{uploaded.name}'")
                except Exception as e:
                    error_count += 1
                    st.error(f"Erreur pour '{uploaded.name}' : {str(e)[:100]}")
            progress.progress(1.0, text="TerminÃ© !")
            if success_count > 0:
                st.success(f"\u2705 {success_count} fichier{'s' if success_count > 1 else ''} classÃ©{'s' if success_count > 1 else ''} et uploadÃ©{'s' if success_count > 1 else ''} avec succÃ¨s !")
            if error_count > 0:
                st.error(f"{error_count} fichier{'s' if error_count > 1 else ''} en erreur.")
            st.rerun()
    else:
        # Mode manuel - un seul type pour tous les fichiers
        st.info(f"\U0001f4ce {nb} fichier{'s' if nb > 1 else ''} sÃ©lectionnÃ©{'s' if nb > 1 else ''} -> {doc_type}")
        if st.button(f"\U0001f4e4 Uploader {nb} fichier{'s' if nb > 1 else ''}", type="primary"):
            progress = st.progress(0, text="Upload en cours...")
            success_count = 0
            error_count = 0
            for i, uploaded in enumerate(uploaded_files):
                progress.progress(i / nb, text=f"Upload de {uploaded.name}...")
                try:
                    file_result = storage.upload_file(
                        file_bytes=uploaded.getvalue(),
                        filename=uploaded.name,
                        chantier_id=chantier["id"],
                        famille=doc_type,
                        doc_type=doc_type.lower(),
                    )
                    if file_result:
                        success_count += 1
                    else:
                        error_count += 1
                        st.warning(f"\u26a0\ufe0f Ãchec pour '{uploaded.name}'")
                except Exception as e:
                    error_count += 1
                    st.error(f"Erreur pour '{uploaded.name}' : {str(e)[:100]}")
            progress.progress(1.0, text="TerminÃ© !")
            if success_count > 0:
                st.success(f"\u2705 {success_count} fichier{'s' if success_count > 1 else ''} uploadÃ©{'s' if success_count > 1 else ''} avec succÃ¨s.")
            if error_count > 0:
                st.error(f"{error_count} fichier{'s' if error_count > 1 else ''} en erreur.")
            st.rerun()

# --- Documents existants ---
st.markdown("---")
st.subheader("\U0001f4cb Documents du chantier")

docs = db.get_documents(user_id=user_id, chantier_id=chantier["id"])

filter_type = st.selectbox("Filtrer par type", ["Tous"] + CATEGORIES, key="doc_filter")
if filter_type != "Tous":
    docs = [d for d in docs if d.get("type", d.get("famille", "")) == filter_type]

if docs:
    total_size = sum(d.get("taille", d.get("file_size_bytes", 0)) or 0 for d in docs)
    size_display = f"{total_size / 1024 / 1024:.1f} Mo" if total_size > 1024 * 1024 else f"{total_size / 1024:.0f} Ko"
    st.info(f"\U0001f4c2 {len(docs)} documents - {size_display}")

    CAT_ICONS = {
        "Plan": "\U0001f4d0", "DCE": "\U0001f4d1", "Devis": "\U0001f4b0",
        "Facture": "\U0001f9fe", "Ãtude": "\U0001f4d6", "Contrat": "\U0001f4dc",
        "PV": "\U0001f4dd", "Photo": "\U0001f4f7", "MÃ©trÃ©": "\U0001f4cf",
        "Autre": "\U0001f4c4",
    }

    for doc in docs:
        doc_famille = doc.get("type", doc.get("famille", "Autre"))
        icon = CAT_ICONS.get(doc_famille, "\U0001f4c4")
        nom = doc.get("nom", doc.get("filename", "N/A"))
        taille = doc.get("taille", doc.get("file_size_bytes", 0)) or 0
        taille_str = f"{taille / 1024:.0f} Ko" if taille < 1024 * 1024 else f"{taille / 1024 / 1024:.1f} Mo"
        date = str(doc.get("created_at", ""))[:10]

        col1, col2, col3 = st.columns([4, 2, 1])
        col1.markdown(f"{icon} **{nom}**")
        col2.caption(f"{doc_famille} - {taille_str} - {date}")

        storage_path = doc.get("storage_path", "")
        if storage_path and col3.button("\U0001f4e5", key=f"dl_{doc.get('id', '')}", help="TÃ©lÃ©charger"):
            try:
                url = storage.get_signed_url(storage_path)
                if url:
                    st.markdown(f"[\U0001f4e5 TÃ©lÃ©charger le document]({url})")
                else:
                    st.warning("Impossible de gÃ©nÃ©rer le lien.")
            except Exception as e:
                st.error(f"Erreur : {str(e)[:100]}")
else:
    st.warning("Aucun document pour ce chantier.")

# --- Utilisation stockage ---
st.markdown("---")
st.subheader("\U0001f4be Utilisation du stockage")

try:
    usage = storage.get_storage_usage(user_id=user_id)
    total_docs = usage.get("nb_documents", 0)
    total_bytes = usage.get("total_bytes", 0)
    total_mb = total_bytes / 1024 / 1024

    profile = db.get_user_profile(user_id) or {}
    plan = profile.get("subscription_plan", "free")
    limits = {"free": 1024, "pro": 5120, "team": 20480}
    limit_mb = limits.get(plan, 1024)

    c1, c2 = st.columns(2)
    c1.metric("\U0001f4c1 DOCUMENTS", total_docs)
    c2.metric("\U0001f4be ESPACE UTILISÃ", f"{total_mb:.1f} Mo / {limit_mb} Mo")

    pct = min(total_mb / limit_mb, 1.0) if limit_mb > 0 else 0
    st.progress(pct)
    st.caption(f"{total_mb:.1f} Mo utilisÃ©s sur {limit_mb} Mo ({pct*100:.0f}%)")

    if pct > 0.9:
        st.warning("\u26a0\ufe0f Stockage presque plein ! Pensez Ã  mettre Ã  niveau votre abonnement.")
except Exception as e:
    st.info("Utilisation du stockage non disponible.")
