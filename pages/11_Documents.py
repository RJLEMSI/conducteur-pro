"""
Page 11 - Gestion Documentaire
Upload, telechargement, visualisation et organisation des documents par chantier.
Classification automatique intelligente des documents.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime
from lib.helpers import page_setup, render_saas_sidebar, chantier_selector
from lib import db, storage
from utils import GLOBAL_CSS

page_setup(title="Documents", icon="")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# --- Custom CSS ---
st.markdown("""
<style>
/* Document cards */
.doc-card {
    background: white;
    border: 1px solid #e8ecf1;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.doc-card:hover {
    border-color: #2563eb;
    box-shadow: 0 2px 8px rgba(37,99,235,0.12);
}
.doc-name {
    font-weight: 600;
    font-size: 0.95rem;
    color: #1e293b;
    margin: 0;
}
.doc-meta {
    font-size: 0.78rem;
    color: #64748b;
    margin-top: 2px;
}
.doc-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 500;
    margin-right: 6px;
}
.badge-plan { background: #dbeafe; color: #1d4ed8; }
.badge-dce { background: #fef3c7; color: #92400e; }
.badge-devis { background: #d1fae5; color: #065f46; }
.badge-facture { background: #fee2e2; color: #991b1b; }
.badge-etude { background: #ede9fe; color: #5b21b6; }
.badge-contrat { background: #fce7f3; color: #9d174d; }
.badge-pv { background: #e0f2fe; color: #075985; }
.badge-photo { background: #f0fdf4; color: #166534; }
.badge-metre { background: #fff7ed; color: #9a3412; }
.badge-autre { background: #f1f5f9; color: #475569; }

/* Upload zone */
.upload-section {
    background: linear-gradient(135deg, #f0f7ff 0%, #f8fafc 100%);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
    border: 1px solid #e2e8f0;
}

/* Stats cards */
.storage-card {
    background: white;
    border-radius: 10px;
    padding: 16px;
    border: 1px solid #e8ecf1;
    text-align: center;
}
.storage-number {
    font-size: 1.8rem;
    font-weight: 700;
    color: #1e293b;
}
.storage-label {
    font-size: 0.8rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Delete confirmation */
.delete-warning {
    background: #fff5f5;
    border: 1px solid #fed7d7;
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)

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
VIEWABLE_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".txt", ".csv"}

CAT_ICONS = {
    "Plan": "\U0001f4d0", "DCE": "\U0001f4d1", "Devis": "\U0001f4b0",
    "Facture": "\U0001f9fe", "Etude": "\U0001f4d6", "Contrat": "\U0001f4dc",
    "PV": "\U0001f4dd", "Photo": "\U0001f4f7", "Metre": "\U0001f4cf", "Autre": "\U0001f4c4",
}

BADGE_CLASSES = {
    "Plan": "badge-plan", "DCE": "badge-dce", "Devis": "badge-devis",
    "Facture": "badge-facture", "Etude": "badge-etude", "Contrat": "badge-contrat",
    "PV": "badge-pv", "Photo": "badge-photo", "Metre": "badge-metre", "Autre": "badge-autre",
}


def classify_file(filename: str) -> str:
    name_lower = filename.lower()
    _, ext = os.path.splitext(name_lower)
    if ext in IMAGE_EXTENSIONS:
        for kw, cat in KEYWORD_MAP.items():
            if kw in name_lower and cat != "Photo":
                return cat
        return "Photo"
    if ext in PLAN_EXTENSIONS:
        return "Plan"
    name_clean = name_lower.replace(ext, "")
    name_clean = name_clean.replace("-", " ").replace("_", " ").replace(".", " ")
    for kw, cat in KEYWORD_MAP.items():
        if kw in name_clean:
            return cat
    return "Autre"


def can_view_in_browser(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in VIEWABLE_EXTENSIONS


def format_size(size_bytes):
    if not size_bytes:
        return "0 Ko"
    if size_bytes < 1024:
        return f"{size_bytes} o"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.0f} Ko"
    return f"{size_bytes / 1024 / 1024:.1f} Mo"


def delete_document_full(doc):
    """Supprime un document du storage ET de la base de donnees."""
    storage_path = doc.get("storage_path", "")
    doc_id = doc.get("id", "")
    success = True
    if storage_path:
        try:
            storage.delete_file(storage_path)
        except Exception:
            success = False
    if doc_id:
        try:
            db.delete_document(doc_id)
        except Exception:
            success = False
    return success


def render_document_card(doc, prefix=""):
    """Affiche un document en carte avec actions."""
    doc_famille = doc.get("famille", doc.get("type", "Autre"))
    icon = CAT_ICONS.get(doc_famille, "\U0001f4c4")
    badge_class = BADGE_CLASSES.get(doc_famille, "badge-autre")
    nom = doc.get("nom", doc.get("filename", "Sans nom")) or "Sans nom"
    taille = doc.get("file_size_bytes", doc.get("taille", 0)) or 0
    taille_str = format_size(taille)
    date = str(doc.get("created_at", ""))[:10]
    storage_path = doc.get("storage_path", "")
    doc_id = doc.get("id", "")

    # Carte document HTML
    st.markdown(f"""
    <div class="doc-card">
        <div style="display:flex; align-items:center; justify-content:space-between;">
            <div>
                <p class="doc-name">{icon} {nom}</p>
                <p class="doc-meta">
                    <span class="doc-badge {badge_class}">{doc_famille}</span>
                    {taille_str} &bull; {date}
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Actions en colonnes
    col_view, col_dl, col_del = st.columns([1, 1, 1])

    # Bouton visualiser
    if storage_path and can_view_in_browser(nom):
        if col_view.button("\U0001f441\ufe0f Voir", key=f"{prefix}view_{doc_id}", width="stretch"):
            try:
                url = storage.get_signed_url(storage_path, expires_in=1800)
                if url:
                    st.session_state[f"{prefix}viewing_{doc_id}"] = url
                else:
                    st.warning("Impossible de generer le lien.")
            except Exception:
                st.error("Erreur lors de la generation du lien.")
    else:
        col_view.button("\U0001f441\ufe0f Voir", key=f"{prefix}view_{doc_id}_disabled", disabled=True, width="stretch")

    # Bouton telecharger
    if storage_path:
        if col_dl.button("\U0001f4e5 Telecharger", key=f"{prefix}dl_{doc_id}", width="stretch"):
            try:
                url = storage.get_signed_url(storage_path)
                if url:
                    st.markdown(f'<a href="{url}" target="_blank">\U0001f4e5 Cliquez ici pour telecharger</a>', unsafe_allow_html=True)
            except Exception:
                st.error("Erreur.")
    else:
        col_dl.button("\U0001f4e5 Telecharger", key=f"{prefix}dl_{doc_id}_disabled", disabled=True, width="stretch")

    # Bouton supprimer avec confirmation
    delete_key = f"{prefix}confirm_delete_{doc_id}"
    if st.session_state.get(delete_key):
        st.markdown("""<div class="delete-warning">
            <strong>\u26a0\ufe0f Confirmer la suppression ?</strong><br>
            Cette action est irreversible.
        </div>""", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if c1.button("\u2705 Oui, supprimer", key=f"{prefix}yes_del_{doc_id}", type="primary", width="stretch"):
            if delete_document_full(doc):
                st.success(f"'{nom}' supprime avec succes.")
                del st.session_state[delete_key]
                st.rerun()
            else:
                st.error("Erreur lors de la suppression.")
        if c2.button("\u274c Annuler", key=f"{prefix}no_del_{doc_id}", width="stretch"):
            del st.session_state[delete_key]
            st.rerun()
    else:
        if col_del.button("\U0001f5d1\ufe0f Supprimer", key=f"{prefix}del_{doc_id}", width="stretch"):
            st.session_state[delete_key] = True
            st.rerun()

    # Visionneuse inline
    view_key = f"{prefix}viewing_{doc_id}"
    if st.session_state.get(view_key):
        url = st.session_state[view_key]
        _, ext = os.path.splitext(nom.lower())
        st.markdown("---")
        if ext == ".pdf":
            st.markdown(f'<iframe src="{url}" width="100%" height="600" style="border: 1px solid #ddd; border-radius: 8px;"></iframe>', unsafe_allow_html=True)
        elif ext in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}:
            st.image(url, caption=nom, width="stretch")
        elif ext in {".txt", ".csv"}:
            try:
                file_data = storage.download_file(storage_path, is_encrypted=doc.get("is_encrypted", False))
                if file_data:
                    st.code(file_data.decode("utf-8", errors="replace"), language="text")
            except Exception:
                st.markdown(f"[Ouvrir dans le navigateur]({url})")
        if st.button("\u2716 Fermer la visualisation", key=f"{prefix}close_{doc_id}"):
            del st.session_state[view_key]
            st.rerun()
        st.markdown("---")


# --- Upload Section ---
st.markdown('<div class="upload-section">', unsafe_allow_html=True)
st.subheader("Importer des documents")

auto_classify = st.toggle(
    "Classification automatique",
    value=True,
    help="Les documents sont automatiquement classes selon leur nom de fichier.",
)

if not auto_classify:
    doc_type = st.selectbox("Type de document", CATEGORIES, key="doc_type_upload")

uploaded_files = st.file_uploader(
    "Fichiers",
    type=["pdf", "docx", "xlsx", "csv", "png", "jpg", "jpeg", "txt", "dwg", "dxf", "zip", "pptx"],
    accept_multiple_files=True,
    key="doc_upload",
    help="Glissez-deposez vos fichiers. La classification se fait automatiquement.",
)

if uploaded_files:
    nb = len(uploaded_files)

    if auto_classify:
        classifications = {}
        for f in uploaded_files:
            classifications[f.name] = classify_file(f.name)

        by_cat = {}
        for fname, cat in classifications.items():
            by_cat.setdefault(cat, []).append(fname)

        st.markdown(f"**{nb} fichier{'s' if nb > 1 else ''} detecte{'s' if nb > 1 else ''} :**")

        for cat in CATEGORIES:
            if cat in by_cat:
                icon = CAT_ICONS.get(cat, "\U0001f4c4")
                files_list = by_cat[cat]
                with st.expander(f"{icon} **{cat}** ({len(files_list)} fichier{'s' if len(files_list) > 1 else ''})", expanded=False):
                    for fname in files_list:
                        st.caption(f"  - {fname}")

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

        if st.button(f"\U0001f4e4 Uploader et classer {nb} fichier{'s' if nb > 1 else ''}", type="primary"):
            progress = st.progress(0, text="Upload en cours...")
            success_count = 0
            error_count = 0
            for i, uploaded in enumerate(uploaded_files):
                cat = classifications[uploaded.name]
                progress.progress(i / nb, text=f"Upload de {uploaded.name} \u2192 {cat}...")
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
                    st.error(f"Erreur: '{uploaded.name}': {e}")
            progress.progress(1.0, text="Termine !")
            if success_count > 0:
                st.success(f"\u2705 {success_count} fichier{'s' if success_count > 1 else ''} uploade{'s' if success_count > 1 else ''} avec succes !")
            if error_count > 0:
                st.error(f"{error_count} fichier{'s' if error_count > 1 else ''} en erreur.")
            st.rerun()
    else:
        st.info(f"{nb} fichier{'s' if nb > 1 else ''} \u2192 {doc_type}")
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
                        doc_type=doc_type,
                    )
                    if file_result:
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    error_count += 1
                    st.error(f"Erreur: '{uploaded.name}': {e}")
            progress.progress(1.0, text="Termine !")
            if success_count > 0:
                st.success(f"\u2705 {success_count} fichier{'s' if success_count > 1 else ''} uploade{'s' if success_count > 1 else ''} !")
            if error_count > 0:
                st.error(f"{error_count} en erreur.")
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# --- Documents existants ---
st.markdown("---")
st.subheader("Documents du chantier")

docs = db.get_documents(user_id=user_id, chantier_id=chantier["id"])

# Barre de recherche
if docs:
    search_query = st.text_input(
        "\U0001f50d Rechercher un document",
        placeholder="Tapez un nom de fichier...",
        key="doc_search",
    )
    if search_query:
        search_lower = search_query.lower()
        docs = [d for d in docs if search_lower in (d.get("nom", "") or "").lower()]

tab_names = ["Tous"] + [f"{CAT_ICONS.get(c, '\U0001f4c4')} {c}" for c in CATEGORIES]
tabs = st.tabs(tab_names)

# Onglet "Tous"
with tabs[0]:
    if docs:
        total_size = sum(d.get("file_size_bytes", d.get("taille", 0)) or 0 for d in docs)
        st.info(f"\U0001f4c1 {len(docs)} document{'s' if len(docs) > 1 else ''} - {format_size(total_size)}")
        for doc in docs:
            render_document_card(doc, prefix="all_")
    else:
        if search_query if 'search_query' in dir() else False:
            st.warning("Aucun document ne correspond a votre recherche.")
        else:
            st.info("Aucun document pour ce chantier. Importez vos premiers fichiers ci-dessus !")

# Onglets par categorie
for i, cat in enumerate(CATEGORIES):
    with tabs[i + 1]:
        cat_docs = [d for d in docs if d.get("famille", d.get("type", "Autre")) == cat]
        if cat_docs:
            total_size = sum(d.get("file_size_bytes", d.get("taille", 0)) or 0 for d in cat_docs)
            st.info(f"{len(cat_docs)} document{'s' if len(cat_docs) > 1 else ''} - {format_size(total_size)}")
            for doc in cat_docs:
                render_document_card(doc, prefix=f"cat{cat}_")
        else:
            st.info(f"Aucun document de type {cat}.")

# --- Utilisation stockage ---
st.markdown("---")
st.subheader("Utilisation du stockage")

try:
    all_docs = db.get_documents(user_id=user_id)
    total_docs = len(all_docs)
    total_bytes = sum(d.get("file_size_bytes", d.get("taille", 0)) or 0 for d in all_docs)
    total_mb = total_bytes / 1024 / 1024

    profile = db.get_profile(user_id) or {}
    plan = profile.get("subscription_plan", "free")
    limits = {"free": 1024, "pro": 5120, "team": 20480}
    limit_mb = limits.get(plan, 1024)

    c1, c2, c3 = st.columns(3)

    c1.markdown(f"""
    <div class="storage-card">
        <div class="storage-number">{total_docs}</div>
        <div class="storage-label">Documents</div>
    </div>
    """, unsafe_allow_html=True)

    c2.markdown(f"""
    <div class="storage-card">
        <div class="storage-number">{total_mb:.1f} Mo</div>
        <div class="storage-label">Espace utilise</div>
    </div>
    """, unsafe_allow_html=True)

    c3.markdown(f"""
    <div class="storage-card">
        <div class="storage-number">{limit_mb} Mo</div>
        <div class="storage-label">Limite ({plan.title()})</div>
    </div>
    """, unsafe_allow_html=True)

    pct = min(total_mb / limit_mb, 1.0) if limit_mb > 0 else 0
    st.progress(pct)
    st.caption(f"{total_mb:.1f} Mo utilises sur {limit_mb} Mo ({pct*100:.0f}%)")

    if pct > 0.9:
        st.warning("\u26a0\ufe0f Stockage presque plein ! Pensez a mettre a niveau votre abonnement.")
except Exception:
    st.info("Utilisation du stockage non disponible.")
