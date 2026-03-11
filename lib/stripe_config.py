"""
Configuration Stripe pour ConducteurPro.
Gère le basculement test/production et la vérification des webhooks.
"""
import streamlit as st
import stripe
import hmac
import hashlib
import logging

logger = logging.getLogger('conducteurpro.stripe')


def get_stripe_mode():
    """Retourne le mode Stripe actuel (test ou live)."""
    key = st.secrets.get("STRIPE_SECRET_KEY", "")
    if key.startswith("sk_live_"):
        return "live"
    elif key.startswith("sk_test_"):
        return "test"
    return "unknown"


def init_stripe():
    """Initialise Stripe avec la bonne clé API."""
    stripe.api_key = st.secrets.get("STRIPE_SECRET_KEY", "")
    mode = get_stripe_mode()
    if mode == "test":
        logger.info("Stripe initialisé en mode TEST")
    elif mode == "live":
        logger.info("Stripe initialisé en mode PRODUCTION")
    else:
        logger.warning("Clé Stripe non reconnue")
    return stripe


def get_price_ids():
    """Retourne les Price IDs selon le mode (test ou live)."""
    mode = get_stripe_mode()
    
    if mode == "live":
        return {
            "pro": st.secrets.get("STRIPE_PRICE_PRO_LIVE", ""),
            "team": st.secrets.get("STRIPE_PRICE_TEAM_LIVE", ""),
        }
    else:
        return {
            "pro": st.secrets.get("STRIPE_PRICE_PRO_TEST", "price_1T98y2ItXZDdzKQiDk2hzpVt"),
            "team": st.secrets.get("STRIPE_PRICE_TEAM_TEST", "price_1T98zFItXZDdzKQi4HXuc9LQ"),
        }


def verify_webhook_signature(payload, sig_header, webhook_secret=None):
    """Vérifie la signature d'un webhook Stripe.
    
    IMPORTANT pour la production : empêche les attaques par injection.
    """
    secret = webhook_secret or st.secrets.get("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        logger.warning("Webhook secret non configuré - signature non vérifiée")
        return None
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
        return event
    except stripe.error.SignatureVerificationError:
        logger.error("Signature webhook invalide")
        return None
    except Exception as e:
        logger.error(f"Erreur vérification webhook: {str(e)}")
        return None


def create_checkout_session(customer_email, price_id, user_id, success_url=None, cancel_url=None):
    """Crée une session de paiement Stripe Checkout."""
    try:
        base_url = st.secrets.get("APP_URL", "https://conducteurpro.fr")
        
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=customer_email,
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url or f"{base_url}/Abonnement?success=true",
            cancel_url=cancel_url or f"{base_url}/Abonnement?canceled=true",
            metadata={"user_id": user_id},
            allow_promotion_codes=True,  # Active les codes promo
            billing_address_collection="required",  # Requis pour la facturation
            tax_id_collection={"enabled": True},  # Collecte du numéro de TVA
        )
        return session
    except stripe.error.StripeError as e:
        logger.error(f"Erreur Stripe Checkout: {str(e)}")
        st.error("Une erreur est survenue lors du paiement. Veuillez réessayer.")
        return None


def create_customer_portal(customer_id, return_url=None):
    """Crée un lien vers le portail client Stripe (gestion abonnement)."""
    try:
        base_url = st.secrets.get("APP_URL", "https://conducteurpro.fr")
        
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url or f"{base_url}/Abonnement",
        )
        return session.url
    except Exception as e:
        logger.error(f"Erreur portail Stripe: {str(e)}")
        return None


# ═══════════════════════════════════════════
# CHECKLIST DE MISE EN PRODUCTION
# ═══════════════════════════════════════════
PRODUCTION_CHECKLIST = {
    "stripe_keys": "Remplacer sk_test_ par sk_live_ dans les secrets Streamlit",
    "price_ids": "Créer les Price IDs de production dans le dashboard Stripe",
    "webhook": "Configurer le webhook endpoint dans Stripe Dashboard",
    "webhook_secret": "Ajouter STRIPE_WEBHOOK_SECRET dans les secrets",
    "tax": "Configurer Stripe Tax pour la TVA française (20%)",
    "receipts": "Activer les reçus automatiques dans Stripe Dashboard",
    "branding": "Personnaliser la page de paiement Stripe avec le logo ConducteurPro",
    "3ds": "Vérifier que 3D Secure est activé (requis en Europe / SCA)",
    "test_payment": "Effectuer un paiement test de bout en bout",
    "refund_policy": "Configurer la politique de remboursement",
}


def check_production_readiness():
    """Vérifie si la configuration Stripe est prête pour la production."""
    issues = []
    
    mode = get_stripe_mode()
    if mode == "test":
        issues.append("\u26a0\ufe0f Stripe est en mode TEST - pas de vrais paiements")
    
    if not st.secrets.get("STRIPE_WEBHOOK_SECRET"):
        issues.append("\u274c Webhook secret non configuré")
    
    if not st.secrets.get("STRIPE_PRICE_PRO_LIVE"):
        issues.append("\u274c Price ID Pro (live) non configuré")
    
    if not st.secrets.get("STRIPE_PRICE_TEAM_LIVE"):
        issues.append("\u274c Price ID Équipe (live) non configuré")
    
    if not st.secrets.get("APP_URL"):
        issues.append("\u26a0\ufe0f APP_URL non défini (URLs de callback)")
    
    return issues
