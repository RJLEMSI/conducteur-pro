"""
Tests automatisés pour ConducteurPro.
Exécuter avec : pytest tests/ -v
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


# ═══════════════════════════════════════════
# Tests du module error_handler
# ═══════════════════════════════════════════

class TestErrorHandler:
    """Tests pour lib/error_handler.py"""
    
    def test_get_error_message_known_category(self):
        from lib.error_handler import get_error_message
        msg = get_error_message("database")
        assert "données" in msg.lower() or "réessayer" in msg.lower()
    
    def test_get_error_message_unknown_category(self):
        from lib.error_handler import get_error_message
        msg = get_error_message("nonexistent")
        assert "inattendue" in msg.lower()
    
    def test_get_error_message_with_detail(self):
        from lib.error_handler import get_error_message
        msg = get_error_message("database", detail="DB001")
        assert "DB001" in msg
    
    def test_safe_execute_success(self):
        from lib.error_handler import safe_execute
        result = safe_execute(lambda: 42, category="generic", default=0)
        assert result == 42
    
    def test_safe_execute_failure(self):
        from lib.error_handler import safe_execute
        with patch('lib.error_handler.st') as mock_st:
            result = safe_execute(
                lambda: 1/0,
                category="generic",
                default=-1,
                show_error=True
            )
            assert result == -1


# ═══════════════════════════════════════════
# Tests du module cache
# ═══════════════════════════════════════════

class TestCache:
    """Tests pour lib/cache.py"""
    
    def test_get_cached_fresh(self):
        from lib.cache import get_cached
        with patch('lib.cache.st') as mock_st:
            mock_st.session_state = {}
            result = get_cached("test_key", lambda: [1, 2, 3], ttl_seconds=60)
            assert result == [1, 2, 3]
    
    def test_get_cached_returns_cached(self):
        from lib.cache import get_cached
        call_count = 0
        def fetch():
            nonlocal call_count
            call_count += 1
            return [1, 2, 3]
        
        with patch('lib.cache.st') as mock_st:
            mock_st.session_state = {}
            get_cached("test2", fetch, ttl_seconds=300)
            # Le 2e appel devrait utiliser le cache
            mock_st.session_state["_cache_test2"] = [1, 2, 3]
            mock_st.session_state["_cache_time_test2"] = datetime.now()
            get_cached("test2", fetch, ttl_seconds=300)
            assert call_count == 1  # Appelé une seule fois
    
    def test_invalidate_cache(self):
        from lib.cache import invalidate_cache
        with patch('lib.cache.st') as mock_st:
            mock_st.session_state = {
                "_cache_test": [1],
                "_cache_time_test": datetime.now(),
                "other_key": "keep"
            }
            invalidate_cache("test")
            assert "_cache_test" not in mock_st.session_state
            assert "other_key" in mock_st.session_state


# ═══════════════════════════════════════════
# Tests du module RGPD
# ═══════════════════════════════════════════

class TestRGPD:
    """Tests pour lib/rgpd.py"""
    
    def test_privacy_policy_content(self):
        from lib.rgpd import get_privacy_policy_text
        policy = get_privacy_policy_text()
        assert "RGPD" in policy
        assert "données" in policy.lower()
        assert "CNIL" in policy
        assert "Supabase" in policy
        assert "Stripe" in policy
    
    def test_export_user_data_structure(self):
        from lib.rgpd import export_user_data
        
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        with patch('lib.rgpd.st'):
            result = export_user_data(mock_supabase, "test-user-id")
        
        if result:
            data = json.loads(result)
            assert "profil" in data or "chantiers" in data
            assert "export_date" in data
            assert "export_format" in data
    
    def test_delete_user_data_calls_all_tables(self):
        from lib.rgpd import delete_user_data
        
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()
        
        with patch('lib.rgpd.st'):
            result = delete_user_data(mock_supabase, "test-user-id")
        
        # Vérifie que toutes les tables ont été nettoyées
        called_tables = [call[0][0] for call in mock_supabase.table.call_args_list]
        assert "documents" in called_tables
        assert "factures" in called_tables
        assert "devis" in called_tables
        assert "chantiers" in called_tables
        assert "profiles" in called_tables


# ═══════════════════════════════════════════
# Tests du module notifications
# ═══════════════════════════════════════════

class TestNotifications:
    """Tests pour lib/notifications.py"""
    
    def test_email_templates_exist(self):
        from lib.notifications import EMAIL_TEMPLATES
        assert "echeance_proche" in EMAIL_TEMPLATES
        assert "facture_impayee" in EMAIL_TEMPLATES
        assert "bienvenue" in EMAIL_TEMPLATES
    
    def test_template_has_required_fields(self):
        from lib.notifications import EMAIL_TEMPLATES
        for name, template in EMAIL_TEMPLATES.items():
            assert "subject" in template, f"Template {name} manque 'subject'"
            assert "body" in template, f"Template {name} manque 'body'"


# ═══════════════════════════════════════════
# Tests du module onboarding
# ═══════════════════════════════════════════

class TestOnboarding:
    """Tests pour lib/onboarding.py"""
    
    def test_onboarding_steps_defined(self):
        from lib.onboarding import ONBOARDING_STEPS
        assert len(ONBOARDING_STEPS) >= 3
        for step in ONBOARDING_STEPS:
            assert "title" in step
            assert "content" in step
            assert "icon" in step
    
    def test_should_show_onboarding_not_authenticated(self):
        from lib.onboarding import should_show_onboarding
        with patch('lib.onboarding.st') as mock_st:
            mock_st.session_state = {"authenticated": False}
            assert not should_show_onboarding()
    
    def test_should_show_onboarding_completed(self):
        from lib.onboarding import should_show_onboarding
        with patch('lib.onboarding.st') as mock_st:
            mock_st.session_state = {
                "authenticated": True,
                "onboarding_completed": True,
                "is_first_login": True
            }
            assert not should_show_onboarding()


# ═══════════════════════════════════════════
# Tests utilitaires
# ═══════════════════════════════════════════

class TestPlanLimits:
    """Tests pour les limites de plan."""
    
    def test_plan_limits_exist(self):
        from lib.auth import PLAN_LIMITS
        assert "free" in PLAN_LIMITS
        assert "pro" in PLAN_LIMITS
        assert "team" in PLAN_LIMITS
    
    def test_plan_limits_values(self):
        from lib.auth import PLAN_LIMITS
        assert PLAN_LIMITS["free"]["chantiers"] == 3
        assert PLAN_LIMITS["pro"]["chantiers"] == 50
        assert PLAN_LIMITS["team"]["chantiers"] == 500
    
    def test_free_plan_storage(self):
        from lib.auth import PLAN_LIMITS
        # Free plan: 500MB = 500 * 1024 * 1024 bytes
        assert PLAN_LIMITS["free"]["storage"] == 500 * 1024 * 1024


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
