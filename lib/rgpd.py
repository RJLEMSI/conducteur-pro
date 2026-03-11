"""
Module de conformité RGPD pour ConducteurPro.
Gère le consentement cookies, l'export et la suppression des données.
"""
import streamlit as st
import json
from datetime import datetime


def render_cookie_banner():
    """Affiche le bandeau de consentement cookies si pas encore accepté."""
    if st.session_state.get("cookie_consent") is not None:
        return
    
    st.markdown("""
    <style>
    .cookie-banner {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #1B3A5C;
        color: white;
        padding: 20px 30px;
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 15px;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.2);
        font-family: 'Segoe UI', sans-serif;
    }
    .cookie-banner p {
        margin: 0;
        font-size: 14px;
        flex: 1;
        min-width: 300px;
    }
    .cookie-banner a {
        color: #7BB3E0;
        text-decoration: underline;
    }
    </style>
    <div class="cookie-banner" id="cookieBanner">
        <p>
            \U0001f36a Ce site utilise des cookies essentiels au fonctionnement de l'application 
            et des cookies d'analyse pour améliorer votre expérience. 
            <a href="/Legal" target="_self">En savoir plus</a>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([6, 1, 1])
    with col2:
        if st.button("\u2705 Accepter", key="cookie_accept", use_container_width=True):
            st.session_state["cookie_consent"] = "accepted"
            st.session_state["cookie_consent_date"] = datetime.now().isoformat()
            st.rerun()
    with col3:
        if st.button("\u274c Refuser", key="cookie_refuse", use_container_width=True):
            st.session_state["cookie_consent"] = "refused"
            st.session_state["cookie_consent_date"] = datetime.now().isoformat()
            st.rerun()


def get_privacy_policy_text():
    """Retourne le texte complet de la politique de confidentialité."""
    return """
## Politique de Confidentialité - ConducteurPro

**Dernière mise à jour : Mars 2026**

### 1. Responsable du traitement
ConducteurPro, édité par Riyad Jamal.
Contact : contact@conducteurpro.fr

### 2. Données collectées
Nous collectons les données suivantes :
- **Données d'identification** : nom, prénom, email, téléphone, entreprise
- **Données professionnelles** : chantiers, métrés, devis, factures, documents
- **Données de connexion** : adresse IP, navigateur, horodatage des connexions
- **Données de paiement** : traitées exclusivement par Stripe (certifié PCI-DSS)

### 3. Finalités du traitement
Vos données sont utilisées pour :
- Fournir et améliorer nos services de gestion de chantier
- Gérer votre compte et votre abonnement
- Assurer la facturation et le suivi financier
- Communiquer avec vous sur votre utilisation du service
- Respecter nos obligations légales et comptables

### 4. Base juridique
- **Exécution du contrat** : gestion de votre compte et fourniture du service
- **Consentement** : cookies d'analyse et communications marketing
- **Intérêt légitime** : amélioration du service et sécurité
- **Obligation légale** : conservation des données comptables

### 5. Durée de conservation
- **Données de compte** : durée de l'abonnement + 3 ans
- **Données comptables** : 10 ans (obligation légale)
- **Logs de connexion** : 12 mois
- **Cookies** : 13 mois maximum

### 6. Vos droits (RGPD)
Conformément au Règlement Général sur la Protection des Données, vous disposez des droits suivants :
- **Droit d'accès** : obtenir une copie de vos données personnelles
- **Droit de rectification** : corriger vos données inexactes
- **Droit à l'effacement** : demander la suppression de vos données
- **Droit à la portabilité** : recevoir vos données dans un format structuré
- **Droit d'opposition** : vous opposer au traitement de vos données
- **Droit à la limitation** : limiter le traitement de vos données

Pour exercer vos droits, contactez-nous à : contact@conducteurpro.fr
Vous pouvez également exporter ou supprimer vos données depuis la page "Mon Compte".

### 7. Sécurité des données
- Chiffrement AES-256 des données au repos
- Chiffrement SSL/TLS pour les transmissions
- Données hébergées en Europe (Supabase EU)
- Paiements sécurisés via Stripe (certifié PCI-DSS)
- Isolation des données par utilisateur

### 8. Sous-traitants
- **Supabase** (base de données) - Hébergement EU
- **Stripe** (paiements) - Certifié PCI-DSS
- **Streamlit Cloud** (hébergement application)
- **Anthropic** (IA) - Données non conservées après analyse

### 9. Transferts hors UE
Aucun transfert systématique hors UE. Les appels à l'API Anthropic (IA) sont ponctuels et les données ne sont pas conservées.

### 10. Réclamation
Vous pouvez adresser une réclamation à la CNIL : www.cnil.fr
"""


def export_user_data(supabase, user_id):
    """Exporte toutes les données d'un utilisateur au format JSON (droit à la portabilité)."""
    try:
        data = {}
        
        # Profil utilisateur
        profile = supabase.table("profiles").select("*").eq("id", user_id).execute()
        if profile.data:
            data["profil"] = profile.data[0]
        
        # Chantiers
        chantiers = supabase.table("chantiers").select("*").eq("user_id", user_id).execute()
        data["chantiers"] = chantiers.data or []
        
        # Devis
        devis = supabase.table("devis").select("*").eq("user_id", user_id).execute()
        data["devis"] = devis.data or []
        
        # Factures
        factures = supabase.table("factures").select("*").eq("user_id", user_id).execute()
        data["factures"] = factures.data or []
        
        # Documents
        documents = supabase.table("documents").select("*").eq("user_id", user_id).execute()
        data["documents"] = documents.data or []
        
        data["export_date"] = datetime.now().isoformat()
        data["export_format"] = "JSON - RGPD Article 20 (Droit à la portabilité)"
        
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)
    except Exception as e:
        st.error("Impossible d'exporter vos données. Veuillez contacter le support.")
        return None


def delete_user_data(supabase, user_id):
    """Supprime toutes les données d'un utilisateur (droit à l'effacement)."""
    try:
        # Ordre de suppression pour respecter les contraintes de clé étrangère
        tables = ["documents", "factures", "devis", "chantiers"]
        
        for table in tables:
            supabase.table(table).delete().eq("user_id", user_id).execute()
        
        # Supprimer le profil en dernier
        supabase.table("profiles").delete().eq("id", user_id).execute()
        
        return True
    except Exception as e:
        st.error("Impossible de supprimer vos données. Veuillez contacter le support.")
        return False


def render_rgpd_section(supabase, user_id):
    """Affiche la section RGPD dans la page Mon Compte."""
    st.markdown("---")
    st.subheader("\U0001f6e1\ufe0f Vos droits RGPD")
    
    st.markdown(
        "Conformément au RGPD, vous pouvez exporter ou supprimer "
        "l'ensemble de vos données personnelles à tout moment."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**\U0001f4e6 Exporter mes données**")
        st.caption("Téléchargez toutes vos données au format JSON.")
        if st.button("Exporter mes données", key="rgpd_export", use_container_width=True):
            with st.spinner("Export en cours..."):
                data_json = export_user_data(supabase, user_id)
                if data_json:
                    st.download_button(
                        label="\u2b07\ufe0f Télécharger le fichier",
                        data=data_json,
                        file_name=f"conducteurpro_export_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json",
                        key="rgpd_download"
                    )
                    st.success("Export prêt ! Cliquez pour télécharger.")
    
    with col2:
        st.markdown("**\U0001f5d1\ufe0f Supprimer mon compte**")
        st.caption("Supprime définitivement toutes vos données.")
        
        confirm = st.text_input(
            "Tapez SUPPRIMER pour confirmer",
            key="rgpd_delete_confirm",
            placeholder="SUPPRIMER"
        )
        
        if st.button("Supprimer mon compte", key="rgpd_delete", 
                      type="primary", use_container_width=True,
                      disabled=(confirm != "SUPPRIMER")):
            with st.spinner("Suppression en cours..."):
                if delete_user_data(supabase, user_id):
                    st.success("Votre compte et toutes vos données ont été supprimés.")
                    st.session_state.clear()
                    st.rerun()
