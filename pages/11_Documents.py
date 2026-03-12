"""
Page 11 - Gestion Documentaire
Upload, telechargement, visualisation et organisation des documents par chantier.
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

page_setup(title="Documents", icon="")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

user_id = st.session_state.get("user_id")
render_saas_sidebar(user_id)

st.title("Gestion Documentaire")

chantier = chantier_selector(key="doc_chantier")
if not chantier:
    st.stop()

# --- Classification automatique ---
CATEGORIES = ["Plan", "DCE", "Devis", "Facture", "Etude", "Contrat", "PV", "Photo", "Metre", "Autre"]

KEYWORD_MAP = {
    "devis": "Devis", "quotation": "Devis", "quote": "Devis",
    "facture": "Facture", "invoice": "Facture", "avoir": "Facture",
    "plan": "Plan", "coupe": "Plan", "facade": "Plan", "elevation": "Plan",
    "implantation": "Plan", "masse": "Plan", "situation": "Plan", "detail": "Plan",
    "dce": "DCE", "cctp": "DCE", "ccap": "DCE", "dpgf": "DCE",
    "cahier": "DCE", "rc": "DCE", "reglement": "DCE", "bpu": "DCE",
    "etude": "Etude", "etudes": "Etude", "rapport": "Etude",
    "diagnostic": "Etude", "analyse": "Etude", "thermique": "Etude",
    "acoustique": "Etude", "geotechnique": "Etude", "beton": "Etude", "structure": "Etude",
    "contrat": "Contrat", "marche": "Contrat", "avenant": "Contrat",
    "convention": "Contrat", "sous-traitance": "Contrat", "soustraitance": "Contrat",
    "pv": "PV", "proces": "PV", "compte-rendu": "PV", "compte_rendu": "PV",
    "cr_": "PV", "reunion": "PV", "reception": "PV", "ope": "PV",
    "metre": "Metre", "metr": "Metre", "quantitatif": "Metre",
    "quantite": "Metre", "dqe": "Metre", "bordereau": "Metre",
    "photo": "Photo", "img": "Photo", "image": "Photo",
    "chantier_photo": "Photo", "dsc": "Photo", "dcim": "Photo",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
PLAN_EXTENSIONS = {".dwg", ".dxf", ".dwf"}

# Extensions visualisables dans le navigateur
VIEWABLE_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".txt", ".csv"}

CAT_ICONS = {
    "Plan": "📐", "DCE": "📑", "Devis": "💰", "Facture": "🧾",
    "Etude": "📖", "Contrat": "📜", "PV": "📝", "Photo": "📷",
    "Metre": "📏", "Autre": "📄",
}


def classify_file(filename: str) -> str:
    """Classifie un fichier selon son nom et son extension."""
    name_lower = filename.lower()
    _, ext = os.path.splitext(name_lower)

    # 1. Images -> Photo
    if ext in IMAGE_EXTENSIONS:
        for kw, cat in KEYWORD_MAP.items():
            if kw in name_lower and cat != "Photo":
                return cat
        return "Photo"

    # 2. Fichiers CAO -> Plan
    if ext in PLAN_EXTENSIONS:
        return "Plan"

    # 3. Recherche par mots-cles dans le nom
    name_clean = name_lower.replace(ext, "")
    name_clean = name_clean.replace("-", " ").replace("_", " ").replace(".", " ")

    for kw, cat in KEYWORD_MAP.items():
        if kw in name_clean:
            return cat

    # 4. Pas de correspondance
    return "Autre"


def can_view_in_browser(filename: str) -> bool:
    """Verifie si le fichier peut etre visualise dans le navigateur."""
    _, ext = os.path.splitext(filename.lower())
    return ext in VIEWABLE_EXTENSIONS


# --- Upload ---
st.subheader("Importer des documents")

auto_classify = st.toggle(
    "Classification automatique",
    value=True,
    help="Quand active, les documents sont automatiquement classes (Devis, Facture, Plan, Etude, Metre...) selon leur nom de fichier.",
)

if not auto_classify:
    doc_type = st.selectbox(
        "Type de document",
        CATEGORIES,
        key="doc_type_upload",
    )

uploaded_files = st.file_uploader(
    "Fichiers",
    type=["pdf", "docx", "xlsx", "csv", "png", "jpg", "jpeg", "txt", "dwg", "dxf", "zip", "pptx"],
    accept_multiple_files=True,
    key="doc_upload",
    help="Glissez-deposez tous vos fichiers d'un coup. La classification se fait automatiquement.",
)

if uploaded_files:
    nb = len(uploaded_files)

    if auto_classify:
        # Classifier chaque fichier
        classifications = {}
        for f in uploaded_files:
            cat = classify_file(f.name)
            classifications[f.name] = cat

        # Grouper par categorie
        by_cat = {}
        for fname, cat in classifications.items():
            by_cat.setdefault(cat, []).append(fname)

        st.markdown(f"**{nb} fichier{'s' if nb > 1 else ''} detecte{'s' if nb > 1 else ''} :**")

        for cat in CATEGORIES:
            if cat in by_cat:
                icon = CAT_ICONS.get(cat, "📄")
                files_list = by_cat[cat]
                with st.expander(f"{icon} **{cat}** ({len(files_list)} fichier{'s' if len(files_list) > 1 else ''})", expanded=False):
                    for fname in files_list:
                        st.caption(f"  - {fname}")

        # Corriger la classification
        with st.expander("Corriger la classification", expanded=False):
            corrected = {}
            for f in uploaded_files:
                corrected[f.name] = st.selectbox(
                    f"{f.name}",
                    CATEGORIES,
                    index=CATEGORIES.index(classifications[f.name]) if classifications[f.name] in CATEGORIES else len(CATEGORIES) - 1,
                    key=f"correct_{f.name}",
                )
            classifications = corrected

        if st.button(f"Uploader et classer {nb} fichier{'s' if nb > 1 else ''}", type="primary"):
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
                        doc_type=cat,
                    )

                    if file_result:
                        success_count += 1
                    else:
                        error_count += 1
                        st.warning(f"Echec pour '{uploaded.name}'")
                except Exception as e:
                    error_count += 1
                    st.error(f"Erreur lors de l'import de '{uploaded.name}': {e}")

            progress.progress(1.0, text="Termine !")
            if success_count > 0:
                st.success(f"{success_count} fichier{'s' if success_count > 1 else ''} classe{'s' if success_count > 1 else ''} et uploade{'s' if success_count > 1 else ''} avec succes !")
            if error_count > 0:
                st.error(f"{error_count} fichier{'s' if error_count > 1 else ''} en erreur.")
            st.rerun()

    else:
        # Mode manuel
        st.info(f"{nb} fichier{'s' if nb > 1 else ''} selectionne{'s' if nb > 1 else ''} -> {doc_type}")

        if st.button(f"Uploader {nb} fichier{'s' if nb > 1 else ''}", type="primary"):
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
                        doc_type=doc_type,
                    )

                    if file_result:
                        success_count += 1
                    else:
                        error_count += 1
                        st.warning(f"Echec pour '{uploaded.name}'")
                except Exception as e:
                    error_count += 1
                    st.error(f"Erreur lors de l'import de '{uploaded.name}': {e}")

            progress.progress(1.0, text="Termine !")
            if success_count > 0:
                st.success(f"{success_count} fichier{'s' if success_count > 1 else ''} uploade{'s' if success_count > 1 else ''} avec succes.")
            if error_count > 0:
                st.error(f"{error_count} fichier{'s' if error_count > 1 else ''} en erreur.")
            st.rerun()


# --- Documents existants ---
st.markdown("---")
st.subheader("Documents du chantier")

docs = db.get_documents(user_id=user_id, chantier_id=chantier["id"])

# Onglets par categorie
tab_names = ["Tous"] + [f"{CAT_ICONS.get(c, '📄')} {c}" for c in CATEGORIES]
tabs = st.tabs(tab_names)

# Onglet "Tous"
with tabs[0]:
    if docs:
        total_size = sum(d.get("taille", d.get("file_size_bytes", 0)) or 0 for d in docs)
        size_display = f"{total_size / 1024 / 1024:.1f} Mo" if total_size > 1024 * 1024 else f"{total_size / 1024:.0f} Ko"
        st.info(f"{len(docs)} documents - {size_display}")

        for doc in docs:
            _render_document_card(doc) if False else None  # placeholder

        for doc in docs:
            doc_famille = doc.get("famille", doc.get("type", "Autre"))
            icon = CAT_ICONS.get(doc_famille, "📄")
            nom = doc.get("nom", doc.get("filename", "N/A"))
            taille = doc.get("taille", doc.get("file_size_bytes", 0)) or 0
            taille_str = f"{taille / 1024:.0f} Ko" if taille < 1024 * 1024 else f"{taille / 1024 / 1024:.1f} Mo"
            date = str(doc.get("created_at", ""))[:10]
            storage_path = doc.get("storage_path", "")
            doc_id = doc.get("id", "")

            col1, col2, col3, col4 = st.columns([4, 2, 1, 1])
            col1.markdown(f"{icon} **{nom}**")
            col2.caption(f"{doc_famille} - {taille_str} - {date}")

            # Bouton visualiser
            if storage_path and can_view_in_browser(nom):
                if col3.button("👁", key=f"view_{doc_id}", help="Visualiser"):
                    try:
                        url = storage.get_signed_url(storage_path, expires_in=1800)
                        if url:
                            st.session_state[f"viewing_{doc_id}"] = url
                        else:
                            st.warning("Impossible de generer le lien de visualisation.")
                    except Exception:
                        st.error("Erreur lors de la generation du lien.")

            # Bouton telecharger
            if storage_path:
                if col4.button("📥", key=f"dl_{doc_id}", help="Telecharger"):
                    try:
                        url = storage.get_signed_url(storage_path)
                        if url:
                            st.markdown(f"[Telecharger {nom}]({url})")
                        else:
                            st.warning("Impossible de generer le lien.")
                    except Exception:
                        st.error("Erreur lors du telechargement.")

            # Afficher la visionneuse si active
            view_key = f"viewing_{doc_id}"
            if st.session_state.get(view_key):
                url = st.session_state[view_key]
                _, ext = os.path.splitext(nom.lower())
                if ext == ".pdf":
                    st.markdown(f'<iframe src="{url}" width="100%" height="600" style="border: 1px solid #ddd; border-radius: 8px;"></iframe>', unsafe_allow_html=True)
                elif ext in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}:
                    st.image(url, caption=nom, use_container_width=True)
                elif ext in {".txt", ".csv"}:
                    try:
                        file_data = storage.download_file(storage_path, is_encrypted=doc.get("is_encrypted", False))
                        if file_data:
                            st.code(file_data.decode("utf-8", errors="replace"), language="text")
                    except Exception:
                        st.markdown(f"[Ouvrir dans le navigateur]({url})")
                if st.button("Fermer", key=f"close_{doc_id}"):
                    del st.session_state[view_key]
                    st.rerun()
    else:
        st.warning("Aucun document pour ce chantier.")

# Onglets par categorie
for i, cat in enumerate(CATEGORIES):
    with tabs[i + 1]:
        cat_docs = [d for d in docs if d.get("famille", d.get("type", "Autre")) == cat]

        if cat_docs:
            total_size = sum(d.get("taille", d.get("file_size_bytes", 0)) or 0 for d in cat_docs)
            size_display = f"{total_size / 1024 / 1024:.1f} Mo" if total_size > 1024 * 1024 else f"{total_size / 1024:.0f} Ko"
            st.info(f"{len(cat_docs)} document{'s' if len(cat_docs) > 1 else ''} - {size_display}")

            for doc in cat_docs:
                nom = doc.get("nom", doc.get("filename", "N/A"))
                taille = doc.get("taille", doc.get("file_size_bytes", 0)) or 0
                taille_str = f"{taille / 1024:.0f} Ko" if taille < 1024 * 1024 else f"{taille / 1024 / 1024:.1f} Mo"
                date = str(doc.get("created_at", ""))[:10]
                storage_path = doc.get("storage_path", "")
                doc_id = doc.get("id", "")

                col1, col2, col3, col4 = st.columns([4, 2, 1, 1])
                col1.markdown(f"**{nom}**")
                col2.caption(f"{taille_str} - {date}")

                if storage_path and can_view_in_browser(nom):
                    if col3.button("👁", key=f"viewcat_{cat}_{doc_id}", help="Visualiser"):
                        try:
                            url = storage.get_signed_url(storage_path, expires_in=1800)
                            if url:
                                st.session_state[f"viewingcat_{cat}_{doc_id}"] = url
                        except Exception:
                            st.error("Erreur.")

                if storage_path:
                    if col4.button("📥", key=f"dlcat_{cat}_{doc_id}", help="Telecharger"):
                        try:
                            url = storage.get_signed_url(storage_path)
                            if url:
                                st.markdown(f"[Telecharger {nom}]({url})")
                        except Exception:
                            st.error("Erreur.")

                view_key = f"viewingcat_{cat}_{doc_id}"
                if st.session_state.get(view_key):
                    url = st.session_state[view_key]
                    _, ext = os.path.splitext(nom.lower())
                    if ext == ".pdf":
                        st.markdown(f'<iframe src="{url}" width="100%" height="600" style="border: 1px solid #ddd; border-radius: 8px;"></iframe>', unsafe_allow_html=True)
                    elif ext in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}:
                        st.image(url, caption=nom, use_container_width=True)
                    elif ext in {".txt", ".csv"}:
                        try:
                            file_data = storage.download_file(storage_path, is_encrypted=doc.get("is_encrypted", False))
                            if file_data:
                                st.code(file_data.decode("utf-8", errors="replace"), language="text")
                        except Exception:
                            st.markdown(f"[Ouvrir dans le navigateur]({url})")
                    if st.button("Fermer", key=f"closecat_{cat}_{doc_id}"):
                        del st.session_state[view_key]
                        st.rerun()
        else:
            st.info(f"Aucun document de type {cat} pour ce chantier.")


# --- Utilisation stockage ---
st.markdown("---")
st.subheader("Utilisation du stockage")

try:
    usage = storage.get_storage_usage(user_id=user_id)
    total_docs = usage.get("nb_documents", 0)
    total_bytes = usage.get("total_bytes", 0)
    total_mb = total_bytes / 1024 / 1024

    profile = db.get_profile(user_id) or {}
    plan = profile.get("subscription_plan", "free")
    limits = {"free": 1024, "pro": 5120, "team": 20480}
    limit_mb = limits.get(plan, 1024)

    c1, c2 = st.columns(2)
    c1.metric("DOCUMENTS", total_docs)
    c2.metric("ESPACE UTILISE", f"{total_mb:.1f} Mo / {limit_mb} Mo")

    pct = min(total_mb / limit_mb, 1.0) if limit_mb > 0 else 0
    st.progress(pct)
    st.caption(f"{total_mb:.1f} Mo utilises sur {limit_mb} Mo ({pct*100:.0f}%)")

    if pct > 0.9:
        st.warning("Stockage presque plein ! Pensez a mettre a niveau votre abonnement.")
except Exception:
    st.info("Utilisation du stockage non disponible.")
