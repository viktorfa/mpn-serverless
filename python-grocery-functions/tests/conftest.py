"""
Pytest configuration and shared fixtures for all tests.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add project root to Python path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set test environment variables
os.environ.setdefault("STAGE", "test")
os.environ.setdefault("IS_LOCAL", "true")
os.environ.setdefault("AWS_DEFAULT_REGION", "eu-central-1")


# Shared Fixtures
@pytest.fixture
def fixtures_path():
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def load_feed_fixture(fixtures_path):
    """Factory fixture to load test feed data."""

    def _load_feed(filename):
        with open(fixtures_path / "feeds" / filename) as f:
            return json.load(f)

    return _load_feed


@pytest.fixture
def mock_s3_client():
    """Mock S3 client for tests."""
    mock = MagicMock()
    mock.get_object.return_value = {
        "Body": MagicMock(),
        "LastModified": "2024-01-01T00:00:00Z",
        "VersionId": "test-version-id",
    }
    return mock


@pytest.fixture
def sample_offer():
    """Create a sample offer for testing."""
    return {
        "title": "Test Product",
        "price": 100.0,
        "priceCurrency": "NOK",
        "url": "https://example.com/product",
        "image": "https://example.com/image.jpg",
        "provenance": "test_store",
        "provenanceId": "test-123",
        "dealer": "Test Dealer",
        "availability": "InStock",
        "categories": ["Test Category"],
        "gtin": "1234567890123",
    }


@pytest.fixture
def sample_config():
    """Create a sample handle configuration."""
    return {
        "provenance": "test_spider",
        "namespace": "test",
        "market": "no",
        "context": "amp-no",
        "fieldMapping": {},
        "categoriesLimits": [],
        "extractQuantityFields": ["title"],
        "extractPropertiesFields": [],
        "extractIngredientsFields": [],
        "extractNutritionFields": [],
        "ignore_none": False,
        "collection_name": "testoffers",
    }
