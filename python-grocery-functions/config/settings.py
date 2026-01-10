"""
Centralized configuration management using pydantic-settings.

This module provides a single source of truth for all environment variables
used across the project, with type safety, validation, and sensible defaults.
"""

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Main settings class for the Python Grocery Functions project.

    Automatically loads environment variables from .env files based on STAGE,
    with fallback order: .env.local -> .env.{stage} -> .env.dev
    """

    model_config = SettingsConfigDict(
        env_file=(".env.dev", ".env.prod", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="",
        extra="ignore",
    )

    # === Core Environment Settings ===
    stage: str = Field(default="dev", description="Environment stage (dev/prod)")

    is_local: bool = Field(default=False, description="Whether running in local development mode")

    # === Database Configuration ===
    postgres_url: str = Field(..., description="PostgreSQL database connection URL")

    # === Redis/Dramatiq Configuration ===
    redis_host: str | None = Field(default=None, description="Redis server hostname")

    redis_password: str | None = Field(default=None, description="Redis server password")

    dramatiq_namespace: str | None = Field(
        default=None,
        description="Dramatiq queue namespace (auto-generated if not provided)",
    )

    # Lambda-specific Redis settings (used in some contexts)
    lambda_redis_host: str | None = Field(
        default=None,
        description="Lambda-specific Redis host (falls back to redis_host)",
    )

    lambda_redis_password: str | None = Field(
        default=None,
        description="Lambda-specific Redis password (falls back to redis_password)",
    )

    # === AWS/S3 Configuration ===
    scraper_feed_bucket: str | None = Field(default=None, description="S3 bucket containing scraper feed data")

    aws_execution_env: str | None = Field(default=None, description="AWS execution environment (set by Lambda runtime)")

    # Local AWS credentials (for development)
    offline_aws_access_key_id: str | None = Field(default=None, description="AWS access key for local development")

    offline_aws_secret_access_key: str | None = Field(default=None, description="AWS secret key for local development")

    # === Lambda Function Configuration ===
    handle_scraper_feed_function_name: str | None = Field(
        default=None,
        description="Name of the Lambda function that handles scraper feeds",
    )

    # === Legacy/Deprecated Settings ===
    # These are kept for backward compatibility but not actively used
    scraper_feed_handled_topic_arn: str = Field(
        default="",
        description="Legacy SNS topic ARN (deprecated, using PostgreSQL now)",
    )

    pricing_feed_handled_topic_arn: str = Field(
        default="",
        description="Legacy SNS topic ARN (deprecated, using PostgreSQL now)",
    )

    book_feed_handled_topic_arn: str = Field(
        default="",
        description="Legacy SNS topic ARN (deprecated, using PostgreSQL now)",
    )

    # === Computed Properties ===

    @computed_field
    @property
    def is_production(self) -> bool:
        """True if running in production environment."""
        return self.stage == "prod"

    @computed_field
    @property
    def is_in_aws(self) -> bool:
        """True if running inside AWS Lambda environment."""
        return self.aws_execution_env is not None

    @computed_field
    @property
    def computed_dramatiq_namespace(self) -> str:
        """
        Computed Dramatiq namespace.

        Uses explicit dramatiq_namespace if set, otherwise generates
        one based on the stage: dramatiq_mpn_{stage}
        """
        return self.dramatiq_namespace or f"dramatiq_mpn_{self.stage}"

    @computed_field
    @property
    def effective_redis_host(self) -> str | None:
        """
        Effective Redis host to use.

        Prefers lambda_redis_host if set, falls back to redis_host.
        """
        return self.lambda_redis_host or self.redis_host

    @computed_field
    @property
    def effective_redis_password(self) -> str | None:
        """
        Effective Redis password to use.

        Prefers lambda_redis_password if set, falls back to redis_password.
        """
        return self.lambda_redis_password or self.redis_password


# Global settings instance
# This will be imported and used throughout the application
settings = Settings()
