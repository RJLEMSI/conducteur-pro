"""
Système de notifications email pour ConducteurPro.
Gère les alertes d'échéances, relances de factures et notifications.
"""
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('conducteurpro.notifications')


# Templates d'emails en HTML
EMAIL_TEMPLATES = {
    "echeance_proche": {
        "subject": "\u23f0 ConducteurPro - Échéance proche : {chantier}",
        "body": """
<div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #1B3A5C; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">\U0001f3d7\ufe0f ConducteurPro</h1>
    </div>
    <div style="background: #f8f9fa; padding: 30px; border: 1px solid #dee2e6;">
        <h2 style="color: #1B3A5C;">Échéance à venir</h2>
        <p>Bonjour <strong>{nom}</strong>,</p>
        <p>Le chantier <strong>{chantier}</strong> a une échéance dans <strong>{jours} jours</strong> ({date_echeance}).</p>
        <p>Pensez à vérifier l'avancement et à prendre les mesures nécessaires.</p>
        <a href="https://conducteurpro.fr" style="display: inline-block; background: #2E75B6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 15px;">
            Voir le chantier
        </a>
    </div>
    <div style="background: #1B3A5C; padding: 15px; text-align: center; border-radius: 0 0 8px 8px;">
        <p style="color: #aaa; font-size: 12px; margin: 0;">ConducteurPro - La plateforme tout-en-un pour les conducteurs de travaux</p>
    </div>
</div>
""",
    },
    "facture_impayee": {
        "subject": "\U0001f4cb ConducteurPro - Facture en attente : {reference}",
        "body": """
<div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #1B3A5C; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">\U0001f3d7\ufe0f ConducteurPro</h1>
    </div>
    <div style="background: #f8f9fa; padding: 30px; border: 1px solid #dee2e6;">
        <h2 style="color: #c0392b;">Facture impayée</h2>
        <p>Bonjour <strong>{nom}</strong>,</p>
        <p>La facture <strong>{reference}</strong> d'un montant de <strong>{montant} \u20ac</strong> est en attente de paiement depuis le <strong>{date_emission}</strong>.</p>
        <p>Échéance de paiement : <strong>{date_echeance}</strong></p>
        <a href="https://conducteurpro.fr" style="display: inline-block; background: #c0392b; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 15px;">
            Voir la facture
        </a>
    </div>
    <div style="background: #1B3A5C; padding: 15px; text-align: center; border-radius: 0 0 8px 8px;">
        <p style="color: #aaa; font-size: 12px; margin: 0;">ConducteurPro - La plateforme tout-en-un pour les conducteurs de travaux</p>
    </div>
</div>
""",
    },
    "bienvenue": {
        "subject": "\U0001f44b Bienvenue sur ConducteurPro !",
        "body": """
<div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #1B3A5C; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">\U0001f3d7\ufe0f ConducteurPro</h1>
    </div>
    <div style="background: #f8f9fa; padding: 30px; border: 1px solid #dee2e6;">
        <h2 style="color: #1B3A5C;">Bienvenue {nom} !</h2>
        <p>Merci d'avoir créé votre compte sur ConducteurPro.</p>
        <p>Votre plateforme de gestion de chantier est prête. Voici comment démarrer :</p>
        <ol style="line-height: 2;">
            <li><strong>Créez votre premier chantier</strong> depuis le Tableau de bord</li>
            <li><strong>Importez vos données</strong> (plans, métrés, documents)</li>
            <li><strong>Laissez l'IA analyser</strong> vos documents automatiquement</li>
            <li><strong>Générez vos devis</strong> et factures en quelques clics</li>
        </ol>
        <a href="https://conducteurpro.fr" style="display: inline-block; background: #2E75B6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 15px;">
            Accéder à mon espace
        </a>
    </div>
    <div style="background: #1B3A5C; padding: 15px; text-align: center; border-radius: 0 0 8px 8px;">
        <p style="color: #aaa; font-size: 12px; margin: 0;">ConducteurPro - La plateforme tout-en-un pour les conducteurs de travaux</p>
    </div>
</div>
""",
    },
}


class EmailNotifier:
    """Gestionnaire d'envoi d'emails via SMTP."""
    
    def __init__(self, smtp_host=None, smtp_port=None, smtp_user=None, smtp_pass=None):
        """Initialise avec les paramètres SMTP depuis les secrets Streamlit."""
        self.smtp_host = smtp_host or st.secrets.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(st.secrets.get("SMTP_PORT", 587))
        self.smtp_user = smtp_user or st.secrets.get("SMTP_USER", "")
        self.smtp_pass = smtp_pass or st.secrets.get("SMTP_PASS", "")
        self.from_name = "ConducteurPro"
        self.from_email = st.secrets.get("SMTP_FROM", self.smtp_user)
    
    def send_email(self, to_email, template_name, variables):
        """Envoie un email basé sur un template."""
        if not self.smtp_user or not self.smtp_pass:
            logger.warning("SMTP non configuré - email non envoyé")
            return False
        
        template = EMAIL_TEMPLATES.get(template_name)
        if not template:
            logger.error(f"Template email inconnu: {template_name}")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = template["subject"].format(**variables)
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            
            html_body = template["body"].format(**variables)
            msg.attach(MIMEText(html_body, "html"))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            
            logger.info(f"Email envoyé: {template_name} -> {to_email}")
            return True
        except Exception as e:
            logger.error(f"Erreur envoi email: {str(e)}")
            return False
    
    def check_and_send_reminders(self, supabase, user_id):
        """Vérifie et envoie les rappels d'échéances et factures impayées."""
        try:
            # Profil utilisateur
            profile = supabase.table("profiles").select("nom, email").eq("id", user_id).single().execute()
            if not profile.data:
                return
            
            nom = profile.data.get("nom", "")
            email = profile.data.get("email", "")
            if not email:
                return
            
            today = datetime.now().date()
            
            # Vérifier les échéances de chantiers (7 jours avant)
            chantiers = supabase.table("chantiers").select(
                "nom, date_fin"
            ).eq("user_id", user_id).eq("statut", "En cours").execute()
            
            for chantier in (chantiers.data or []):
                if chantier.get("date_fin"):
                    try:
                        date_fin = datetime.strptime(chantier["date_fin"], "%Y-%m-%d").date()
                        jours_restants = (date_fin - today).days
                        if 0 < jours_restants <= 7:
                            self.send_email(email, "echeance_proche", {
                                "nom": nom,
                                "chantier": chantier["nom"],
                                "jours": jours_restants,
                                "date_echeance": date_fin.strftime("%d/%m/%Y"),
                            })
                    except (ValueError, TypeError):
                        pass
            
            # Vérifier les factures impayées (plus de 30 jours)
            factures = supabase.table("factures").select(
                "reference, montant_ttc, date_emission, date_echeance"
            ).eq("user_id", user_id).eq("statut", "envoyée").execute()
            
            for facture in (factures.data or []):
                if facture.get("date_echeance"):
                    try:
                        date_ech = datetime.strptime(facture["date_echeance"], "%Y-%m-%d").date()
                        if date_ech < today:
                            self.send_email(email, "facture_impayee", {
                                "nom": nom,
                                "reference": facture.get("reference", ""),
                                "montant": facture.get("montant_ttc", ""),
                                "date_emission": facture.get("date_emission", ""),
                                "date_echeance": date_ech.strftime("%d/%m/%Y"),
                            })
                    except (ValueError, TypeError):
                        pass
        except Exception as e:
            logger.error(f"Erreur vérification rappels: {str(e)}")
