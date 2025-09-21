"""
Shared fixtures and utilities for scraper feed integration tests.
"""

import io
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from botocore.response import StreamingBody

from storage.postgres.pydantic_models import HandleFeedConfig


@pytest.fixture
def fixtures_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent.parent.parent / "fixtures"


@pytest.fixture
def gottebiten_feed_data(fixtures_dir):
    """Load gottebiten scraper feed data (small, fast test data)."""
    with open(fixtures_dir / "feeds" / "gottebiten-scraper-feed.json") as f:
        return json.load(f)


@pytest.fixture
def europris_feed_data(fixtures_dir):
    """Load europris scraper feed data (small, fast test data)."""
    with open(fixtures_dir / "feeds" / "europris-scraper-feed.json") as f:
        return json.load(f)


@pytest.fixture
def meny_feed_data(fixtures_dir):
    """Load meny scraper feed data (medium size, realistic test data)."""
    with open(fixtures_dir / "feeds" / "meny-scraper-feed.json") as f:
        return json.load(f)


@pytest.fixture
def swecandy_feed_data(fixtures_dir):
    """Load swecandy scraper feed data (small Swedish candy feed)."""
    with open(fixtures_dir / "feeds" / "swecandy-scraper-feed.json") as f:
        return json.load(f)


@pytest.fixture
def monter_feed_data(fixtures_dir):
    """Load monter scraper feed data (medium building supplies feed)."""
    with open(fixtures_dir / "feeds" / "monter-scraper-feed.json") as f:
        return json.load(f)


@pytest.fixture
def obsbygg_feed_data(fixtures_dir):
    """Load obsbygg scraper feed data (larger building supplies feed)."""
    with open(fixtures_dir / "feeds" / "obsbygg-scraper-feed.json") as f:
        return json.load(f)


@pytest.fixture
def byggmax_feed_data(fixtures_dir):
    """Load byggmax scraper feed data (large building supplies feed - use carefully)."""
    with open(fixtures_dir / "feeds" / "byggmax-scraper-feed.json") as f:
        return json.load(f)


def create_mock_stream(feed_data: list) -> StreamingBody:
    """
    Convert test feed data to mock StreamingBody for testing.

    Args:
        feed_data: List of offer dictionaries

    Returns:
        Mock StreamingBody that behaves like boto3 S3 object stream
    """
    feed_json = json.dumps(feed_data)
    mock_stream = Mock(spec=StreamingBody)
    mock_stream.read = Mock(return_value=feed_json.encode())
    mock_stream.close = Mock()

    # Create a file-like object for ijson to read from
    json_bytes = feed_json.encode("utf-8")
    mock_stream._raw_stream = io.BytesIO(json_bytes)

    # Make it work with ijson by making it file-like
    def mock_read(size=-1):
        return mock_stream._raw_stream.read(size)

    mock_stream.read = mock_read

    return mock_stream


@pytest.fixture
def create_test_config():
    """Factory for creating test HandleFeedConfig objects."""

    def _create_config(
        provenance: str = "test", namespace: str = None, context: str = "amp-no", market: str = "no", **overrides
    ) -> HandleFeedConfig:
        """Create a realistic test configuration."""
        config_data = {
            "id": "test-config-id",
            "provenance": provenance,
            "namespace": namespace or f"{provenance}_test",
            "context": context,
            "market": market,
            "is_partner": False,
            "categoriesLimits": [],
            "filters": [],
            "fieldMapping": [],
            "extractQuantityFields": [],
            "categoriesField": "categories",
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "ignore_none": False,
            "scrape_time": datetime(2024, 1, 15, 10, 30, 0),
            "scrapeBatchId": "test-batch-123",
            **overrides,
        }
        return HandleFeedConfig(**config_data)

    return _create_config


@pytest.fixture
def gottebiten_config(create_test_config):
    """Pre-configured HandleFeedConfig for gottebiten testing."""
    return create_test_config(provenance="gottebiten.se", namespace="gottebiten", context="amp-se", market="se")


@pytest.fixture
def europris_config(create_test_config):
    """Pre-configured HandleFeedConfig for europris testing."""
    return create_test_config(provenance="europris.no", namespace="europris", context="amp-no", market="no")


@pytest.fixture
def meny_config(create_test_config):
    """Pre-configured HandleFeedConfig for meny testing."""
    return create_test_config(provenance="meny.no", namespace="meny", context="amp-no", market="no")


@pytest.fixture
def swecandy_config(create_test_config):
    """Pre-configured HandleFeedConfig for swecandy testing (Swedish candy)."""
    return create_test_config(provenance="swecandy.se", namespace="swecandy", context="amp-se", market="se")


@pytest.fixture
def monter_config(create_test_config):
    """Pre-configured HandleFeedConfig for monter testing (building supplies)."""
    return create_test_config(
        provenance="monter.no",
        namespace="monter",
        context="bygg-no",
        market="no",
        extractQuantityFields=["title", "description"],  # Test quantity extraction
        extractPropertiesFields=["description"],  # Test properties extraction
    )


@pytest.fixture
def obsbygg_config(create_test_config):
    """Pre-configured HandleFeedConfig for obsbygg testing (building supplies with filtering)."""
    return create_test_config(
        provenance="obsbygg.no",
        namespace="obsbygg",
        context="bygg-no",
        market="no",
        categoriesLimits=[1, 2, 3],  # Test category limits
        filters=[  # Test with filtering enabled
            {
                "source": "pricing.price",
                "operator": "gte",
                "target": 1,  # Only products >= 1 NOK
            }
        ],
    )


@pytest.fixture
def byggmax_config(create_test_config):
    """Pre-configured HandleFeedConfig for byggmax testing (large feed, comprehensive extraction)."""
    return create_test_config(
        provenance="byggmax.se",
        namespace="byggmax",
        context="bygg-se",
        market="se",
        extractQuantityFields=["title", "description"],
        extractPropertiesFields=["description"],
        extractIngredientsFields=["description"],
        categoriesLimits=[1, 2, 3, 4],
    )
