"""
Module de personnalisation PDF pour ConducteurPro.
Permet d'ajouter le logo de l'entreprise du client sur les devis et factures.
"""
import streamlit as st
import base64
import io
import logging

logger = logging.getLogger('conducteurpro.pdf_branding')


def get_company_logo(supabase, user_id):
    """Récupère le logo de l'entreprise depuis le profil utilisateur.
    
    Returns:
        bytes ou None: Le contenu du logo en bytes, ou None si pas de logo.
    """
    try:
        profile = supabase.table("profiles").select("logo_url").eq("id", user_id).single().execute()
        if profile.data and profile.data.get("logo_url"):
            logo_url = profile.data["logo_url"]
            # Télécharger depuis Supabase Storage
            logo_data = supabase.storage.from_("logos").download(logo_url)
            return logo_data
    except Exception as e:
        logger.error(f"Erreur récupération logo: {str(e)}")
    return None


def upload_company_logo(supabase, user_id, uploaded_file):
    """Upload le logo de l'entreprise dans Supabase Storage.
    
    Args:
        uploaded_file: StreamlitUploadedFile
    Returns:
        str ou None: Le chemin du logo stocké.
    """
    try:
        # Vérification du format
        allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/svg+xml"]
        if uploaded_file.type not in allowed_types:
            st.error("Format non supporté. Utilisez PNG, JPG ou SVG.")
            return None
        
        # Vérification de la taille (max 2 MB)
        if uploaded_file.size > 2 * 1024 * 1024:
            st.error("Le logo ne doit pas dépasser 2 Mo.")
            return None
        
        # Nom du fichier
        ext = uploaded_file.name.split(".")[-1].lower()
        file_path = f"{user_id}/logo.{ext}"
        
        # Upload dans Supabase Storage
        supabase.storage.from_("logos").upload(
            file_path,
            uploaded_file.getvalue(),
            {"content-type": uploaded_file.type, "upsert": "true"}
        )
        
        # Mettre à jour le profil
        supabase.table("profiles").update(
            {"logo_url": file_path}
        ).eq("id", user_id).execute()
        
        return file_path
    except Exception as e:
        logger.error(f"Erreur upload logo: {str(e)}")
        st.error("Impossible d'envoyer le logo. Veuillez réessayer.")
        return None


def add_logo_to_pdf(pdf, supabase, user_id, x=10, y=8, max_width=50, max_height=20):
    """Ajoute le logo de l'entreprise à un PDF FPDF2.
    
    Args:
        pdf: Instance FPDF
        supabase: Client Supabase
        user_id: ID de l'utilisateur
        x, y: Position du logo
        max_width, max_height: Taille max en mm
    """
    try:
        logo_data = get_company_logo(supabase, user_id)
        if logo_data:
            # Créer un fichier temporaire en mémoire
            logo_io = io.BytesIO(logo_data)
            pdf.image(logo_io, x=x, y=y, w=max_width, h=0)  # h=0 = ratio auto
            return True
    except Exception as e:
        logger.error(f"Erreur ajout logo PDF: {str(e)}")
    return False


def render_logo_upload_section(supabase, user_id):
    """Affiche la section d'upload du logo dans Mon Compte."""
    st.subheader("\U0001f3a8 Logo de votre entreprise")
    st.caption("Ce logo apparaîtra sur vos devis et factures PDF.")
    
    # Afficher le logo actuel
    current_logo = get_company_logo(supabase, user_id)
    if current_logo:
        st.image(current_logo, width=150, caption="Logo actuel")
    else:
        st.info("Aucun logo configuré. Vos documents utiliseront le logo ConducteurPro par défaut.")
    
    # Upload
    uploaded = st.file_uploader(
        "Choisir un nouveau logo",
        type=["png", "jpg", "jpeg", "svg"],
        key="logo_upload",
        help="Format PNG, JPG ou SVG. Taille max : 2 Mo. Recommandé : fond transparent, 500x200px."
    )
    
    if uploaded:
        st.image(uploaded, width=150, caption="Aperçu")
        if st.button("\u2705 Enregistrer le logo", key="save_logo", type="primary"):
            with st.spinner("Enregistrement..."):
                path = upload_company_logo(supabase, user_id, uploaded)
                if path:
                    st.success("Logo enregistré ! Il apparaîtra sur vos prochains documents.")
                    st.rerun()


def get_company_info(supabase, user_id):
    """Récupère les informations de l'entreprise pour les PDF."""
    try:
        profile = supabase.table("profiles").select(
            "nom, entreprise, email, telephone, adresse, siret, tva_intra"
        ).eq("id", user_id).single().execute()
        
        if profile.data:
            return {
                "nom": profile.data.get("nom", ""),
                "entreprise": profile.data.get("entreprise", ""),
                "email": profile.data.get("email", ""),
                "telephone": profile.data.get("telephone", ""),
                "adresse": profile.data.get("adresse", ""),
                "siret": profile.data.get("siret", ""),
                "tva_intra": profile.data.get("tva_intra", ""),
            }
    except Exception as e:
        logger.error(f"Erreur récupération infos entreprise: {str(e)}")
    
    return {}
