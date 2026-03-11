"""
Module de cache et optimisation des performances pour ConducteurPro.
Utilise st.cache_data et st.cache_resource pour réduire les appels base de données.
"""
import streamlit as st
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('conducteurpro.cache')


# Durées de cache par type de données
CACHE_TTL = {
    "profile": 300,        # 5 minutes
    "chantiers": 120,      # 2 minutes
    "devis": 120,          # 2 minutes
    "factures": 120,       # 2 minutes
    "documents": 60,       # 1 minute
    "stats": 180,          # 3 minutes
    "plan_limits": 600,    # 10 minutes
}


def get_cached(key, fetch_func, ttl_seconds=120, force_refresh=False):
    """Cache intelligent avec TTL pour les données Supabase.
    
    Usage:
        chantiers = get_cached(
            f"chantiers_{user_id}",
            lambda: supabase.table("chantiers").select("*").eq("user_id", user_id).execute().data,
            ttl_seconds=120
        )
    """
    cache_key = f"_cache_{key}"
    cache_time_key = f"_cache_time_{key}"
    
    # Vérifier si le cache est valide
    if not force_refresh:
        cached_data = st.session_state.get(cache_key)
        cached_time = st.session_state.get(cache_time_key)
        
        if cached_data is not None and cached_time is not None:
            age = (datetime.now() - cached_time).total_seconds()
            if age < ttl_seconds:
                return cached_data
    
    # Rafraîchir le cache
    try:
        data = fetch_func()
        st.session_state[cache_key] = data
        st.session_state[cache_time_key] = datetime.now()
        return data
    except Exception as e:
        logger.error(f"Erreur cache {key}: {str(e)}")
        # Retourner les données en cache même expirées plutôt que rien
        return st.session_state.get(cache_key)


def invalidate_cache(key=None):
    """Invalide le cache pour une clé spécifique ou tout le cache.
    
    Usage:
        invalidate_cache("chantiers_xxx")  # Invalide un cache spécifique
        invalidate_cache()  # Invalide tout
    """
    if key:
        st.session_state.pop(f"_cache_{key}", None)
        st.session_state.pop(f"_cache_time_{key}", None)
    else:
        keys_to_remove = [k for k in st.session_state.keys() if k.startswith("_cache_")]
        for k in keys_to_remove:
            del st.session_state[k]


def cached_query(supabase, table, user_id, select="*", filters=None, ttl=None):
    """Raccourci pour les requêtes Supabase cachées.
    
    Usage:
        chantiers = cached_query(supabase, "chantiers", user_id)
        factures = cached_query(supabase, "factures", user_id, 
                                filters={"statut": "envoyée"}, ttl=60)
    """
    cache_key = f"{table}_{user_id}"
    if filters:
        cache_key += "_" + "_".join(f"{k}_{v}" for k, v in filters.items())
    
    ttl_seconds = ttl or CACHE_TTL.get(table, 120)
    
    def fetch():
        query = supabase.table(table).select(select).eq("user_id", user_id)
        if filters:
            for k, v in filters.items():
                query = query.eq(k, v)
        result = query.execute()
        return result.data or []
    
    return get_cached(cache_key, fetch, ttl_seconds)


@st.cache_resource(ttl=3600)
def get_stripe_client():
    """Cache le client Stripe (ressource lourde)."""
    import stripe
    stripe.api_key = st.secrets.get("STRIPE_SECRET_KEY", "")
    return stripe


def render_performance_metrics():
    """Affiche les métriques de performance (debug/admin)."""
    cache_keys = [k for k in st.session_state.keys() if k.startswith("_cache_time_")]
    
    if not cache_keys:
        st.info("Aucune donnée en cache.")
        return
    
    st.markdown("**\U0001f4ca Cache actif :**")
    for time_key in cache_keys:
        key = time_key.replace("_cache_time_", "")
        cached_time = st.session_state[time_key]
        age = (datetime.now() - cached_time).total_seconds()
        st.text(f"  {key}: {age:.0f}s")
