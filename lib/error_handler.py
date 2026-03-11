"""
Gestion centralisée des erreurs pour ConducteurPro.
Fournit des messages d'erreur conviviaux en français.
"""
import streamlit as st
import logging
import traceback
from functools import wraps

# Configuration du logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('conducteurpro')

# Messages d'erreur par catégorie
ERROR_MESSAGES = {
    "database": "Une erreur est survenue lors de l'accès aux données. Veuillez réessayer dans quelques instants.",
    "auth": "Erreur d'authentification. Veuillez vous reconnecter.",
    "payment": "Une erreur est survenue lors du paiement. Veuillez réessayer ou contacter le support.",
    "upload": "Impossible d'envoyer le fichier. Vérifiez sa taille et son format, puis réessayez.",
    "download": "Impossible de télécharger le fichier. Veuillez réessayer.",
    "api": "Le service est temporairement indisponible. Veuillez réessayer dans quelques instants.",
    "ai": "L'analyse IA a rencontré un problème. Veuillez réessayer.",
    "pdf": "Erreur lors du traitement du PDF. Vérifiez que le fichier n'est pas corrompu.",
    "export": "Erreur lors de l'export. Veuillez réessayer.",
    "permission": "Vous n'avez pas les droits nécessaires pour cette action.",
    "limit": "Vous avez atteint la limite de votre forfait. Passez à un plan supérieur pour continuer.",
    "validation": "Les données saisies ne sont pas valides. Veuillez vérifier et réessayer.",
    "network": "Problème de connexion réseau. Vérifiez votre connexion internet.",
    "generic": "Une erreur inattendue est survenue. Veuillez réessayer.",
}


def get_error_message(category="generic", detail=None):
    """Retourne un message d'erreur convivial par catégorie."""
    msg = ERROR_MESSAGES.get(category, ERROR_MESSAGES["generic"])
    if detail:
        msg += f" (Réf: {detail})"
    return msg


def handle_error(category="generic", show_user=True):
    """Décorateur pour gérer les erreurs de manière uniforme.
    
    Usage:
        @handle_error("database")
        def load_chantiers():
            return supabase.table("chantiers").select("*").execute()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log l'erreur technique complète
                logger.error(
                    f"[{category.upper()}] {func.__name__}: {str(e)}\n"
                    f"{traceback.format_exc()}"
                )
                # Afficher un message convivial à l'utilisateur
                if show_user:
                    st.error(get_error_message(category))
                return None
        return wrapper
    return decorator


def safe_execute(func, category="generic", default=None, show_error=True):
    """Exécute une fonction de manière sûre avec gestion d'erreur.
    
    Usage:
        result = safe_execute(
            lambda: supabase.table("chantiers").select("*").execute(),
            category="database",
            default=[]
        )
    """
    try:
        return func()
    except Exception as e:
        logger.error(f"[{category.upper()}] {str(e)}\n{traceback.format_exc()}")
        if show_error:
            st.error(get_error_message(category))
        return default


def log_error(category, message, exception=None):
    """Log une erreur sans l'afficher à l'utilisateur."""
    if exception:
        logger.error(f"[{category.upper()}] {message}: {str(exception)}\n{traceback.format_exc()}")
    else:
        logger.error(f"[{category.upper()}] {message}")
