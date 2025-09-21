"""
Tests for the new pydantic-settings configuration system.
"""

import os
from unittest.mock import patch

import pytest

from config.settings import Settings


class TestSettings:
    """Test the Settings class configuration loading and validation."""

    def test_settings_loads_with_defaults(self):
        """Test that settings can load with minimal configuration."""
        with patch.dict(os.environ, {
            'POSTGRES_URL': 'postgresql://test:test@localhost:5432/test'
        }, clear=True):
            # Create settings with no env file loading for clean test
            settings = Settings(_env_file=None)

            assert settings.stage == "dev"  # default
            assert settings.postgres_url == 'postgresql://test:test@localhost:5432/test'
            assert settings.is_production is False
            assert settings.is_in_aws is False
            assert settings.computed_dramatiq_namespace == "dramatiq_mpn_dev"

    def test_settings_production_mode(self):
        """Test settings in production mode."""
        with patch.dict(os.environ, {
            'STAGE': 'prod',
            'POSTGRES_URL': 'postgresql://prod:prod@prod:5432/prod'
        }, clear=True):
            settings = Settings(_env_file=None)

            assert settings.stage == "prod"
            assert settings.is_production is True
            assert settings.computed_dramatiq_namespace == "dramatiq_mpn_prod"

    def test_redis_fallback_logic(self):
        """Test that Redis settings fall back correctly."""
        with patch.dict(os.environ, {
            'POSTGRES_URL': 'postgresql://test:test@localhost:5432/test',
            'LAMBDA_REDIS_HOST': 'lambda-redis',
            'LAMBDA_REDIS_PASSWORD': 'lambda-pass',
        }, clear=True):
            settings = Settings(_env_file=None)

            # Should use lambda redis settings when available
            assert settings.effective_redis_host == 'lambda-redis'
            assert settings.effective_redis_password == 'lambda-pass'
            assert settings.redis_host is None
            assert settings.redis_password is None

    def test_redis_with_both_settings(self):
        """Test Redis settings when both regular and lambda versions are set."""
        with patch.dict(os.environ, {
            'POSTGRES_URL': 'postgresql://test:test@localhost:5432/test',
            'REDIS_HOST': 'regular-redis',
            'REDIS_PASSWORD': 'regular-pass',
            'LAMBDA_REDIS_HOST': 'lambda-redis',
            'LAMBDA_REDIS_PASSWORD': 'lambda-pass',
        }, clear=True):
            settings = Settings(_env_file=None)

            # Should prefer lambda settings over regular ones
            assert settings.effective_redis_host == 'lambda-redis'
            assert settings.effective_redis_password == 'lambda-pass'
            assert settings.redis_host == 'regular-redis'
            assert settings.redis_password == 'regular-pass'

    def test_aws_detection(self):
        """Test AWS environment detection."""
        with patch.dict(os.environ, {
            'POSTGRES_URL': 'postgresql://test:test@localhost:5432/test',
            'AWS_EXECUTION_ENV': 'AWS_Lambda_python3.11'
        }, clear=True):
            settings = Settings(_env_file=None)

            assert settings.is_in_aws is True
            assert settings.aws_execution_env == 'AWS_Lambda_python3.11'

    def test_explicit_dramatiq_namespace(self):
        """Test that explicit dramatiq namespace overrides computed one."""
        with patch.dict(os.environ, {
            'POSTGRES_URL': 'postgresql://test:test@localhost:5432/test',
            'STAGE': 'dev',
            'DRAMATIQ_NAMESPACE': 'custom_namespace'
        }, clear=True):
            settings = Settings(_env_file=None)

            assert settings.dramatiq_namespace == 'custom_namespace'
            assert settings.computed_dramatiq_namespace == 'custom_namespace'

    def test_missing_required_field_raises_error(self):
        """Test that missing required fields raise validation errors."""
        from pydantic import ValidationError

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):
                Settings(_env_file=None)

    def test_settings_with_all_fields(self):
        """Test settings with all fields populated."""
        env_vars = {
            'STAGE': 'test',
            'IS_LOCAL': 'true',
            'POSTGRES_URL': 'postgresql://test:test@localhost:5432/test',
            'REDIS_HOST': 'redis-host',
            'REDIS_PASSWORD': 'redis-pass',
            'DRAMATIQ_NAMESPACE': 'test_namespace',
            'LAMBDA_REDIS_HOST': 'lambda-redis',
            'LAMBDA_REDIS_PASSWORD': 'lambda-pass',
            'SCRAPER_FEED_BUCKET': 'test-bucket',
            'AWS_EXECUTION_ENV': 'AWS_Lambda_python3.11',
            'OFFLINE_AWS_ACCESS_KEY_ID': 'test-key',
            'OFFLINE_AWS_SECRET_ACCESS_KEY': 'test-secret',
            'HANDLE_SCRAPER_FEED_FUNCTION_NAME': 'test-function'
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings(_env_file=None)

            assert settings.stage == 'test'
            assert settings.is_local is True
            assert settings.postgres_url == 'postgresql://test:test@localhost:5432/test'
            assert settings.redis_host == 'redis-host'
            assert settings.redis_password == 'redis-pass'
            assert settings.dramatiq_namespace == 'test_namespace'
            assert settings.lambda_redis_host == 'lambda-redis'
            assert settings.lambda_redis_password == 'lambda-pass'
            assert settings.scraper_feed_bucket == 'test-bucket'
            assert settings.aws_execution_env == 'AWS_Lambda_python3.11'
            assert settings.offline_aws_access_key_id == 'test-key'
            assert settings.offline_aws_secret_access_key == 'test-secret'
            assert settings.handle_scraper_feed_function_name == 'test-function'

            # Test computed properties
            assert settings.is_production is False
            assert settings.is_in_aws is True
            assert settings.computed_dramatiq_namespace == 'test_namespace'
            assert settings.effective_redis_host == 'lambda-redis'  # lambda takes precedence
            assert settings.effective_redis_password == 'lambda-pass'