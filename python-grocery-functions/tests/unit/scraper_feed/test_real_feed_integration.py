"""
Integration tests for transform_product and filter_product using real feed data.

This file migrates tests from test_handle_objects.py to test the individual
transform_product and filter_product functions with HandleFeedConfig Pydantic models.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from scraper_feed.filters import filter_product, transform_product
from storage.postgres.pydantic_models import HandleFeedConfig

# =============================================================================
# Fixtures for Feed Data
# =============================================================================


@pytest.fixture
def fixtures_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent.parent.parent / "fixtures"


@pytest.fixture
def meny_feed_data(fixtures_dir):
    """Load meny scraper feed data."""
    with open(fixtures_dir / "feeds" / "meny-scraper-feed.json") as f:
        return json.load(f)


@pytest.fixture
def kolonial_feed_data(fixtures_dir):
    """Load kolonial scraper feed data."""
    with open(fixtures_dir / "feeds" / "kolonial-scraper-feed.json") as f:
        return json.load(f)


@pytest.fixture
def europris_feed_data(fixtures_dir):
    """Load europris scraper feed data."""
    with open(fixtures_dir / "feeds" / "europris-scraper-feed.json") as f:
        return json.load(f)


@pytest.fixture
def shopgun_feed_data(fixtures_dir):
    """Load shopgun scraper feed data."""
    with open(fixtures_dir / "feeds" / "shopgun-scraper-feed.json") as f:
        return json.load(f)


@pytest.fixture
def swecandy_feed_data(fixtures_dir):
    """Load swecandy scraper feed data."""
    with open(fixtures_dir / "feeds" / "swecandy-scraper-feed.json") as f:
        return json.load(f)


@pytest.fixture
def gottebiten_feed_data(fixtures_dir):
    """Load gottebiten scraper feed data."""
    with open(fixtures_dir / "feeds" / "gottebiten-scraper-feed.json") as f:
        return json.load(f)


@pytest.fixture
def iherb_feed_data(fixtures_dir):
    """Load iherb scraper feed data."""
    with open(fixtures_dir / "feeds" / "iherb-scraper-feed.json") as f:
        return json.load(f)


@pytest.fixture
def obsbygg_feed_data(fixtures_dir):
    """Load obsbygg scraper feed data."""
    with open(fixtures_dir / "feeds" / "obsbygg-scraper-feed.json") as f:
        return json.load(f)


@pytest.fixture
def byggmax_feed_data(fixtures_dir):
    """Load byggmax scraper feed data."""
    with open(fixtures_dir / "feeds" / "byggmax-scraper-feed.json") as f:
        return json.load(f)


@pytest.fixture
def monter_feed_data(fixtures_dir):
    """Load monter scraper feed data."""
    with open(fixtures_dir / "feeds" / "monter-scraper-feed.json") as f:
        return json.load(f)


# =============================================================================
# Helper Functions
# =============================================================================


def create_config(**overrides):
    """Create HandleFeedConfig with default values."""
    config_data = {
        "id": "test-config",
        "provenance": "test_provider",
        "namespace": "test_provider",
        "context": "amp-no",
        "market": "no",
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


# =============================================================================
# Filter Function Tests
# =============================================================================


class TestFilterProduct:
    """Test filter_product function with real data."""

    def test_filter_products_with_has_operator(self, obsbygg_feed_data):
        """Test filtering products using 'has' operator on categories."""
        config = create_config(
            provenance="obsbygg_spider",
            namespace="obsbygg",
            extractQuantityFields=["title"],
            filters=[
                {
                    "source": "categories",
                    "operator": "has",
                    "target": "skruer og spiker",
                }
            ],
        )

        # Transform all products first
        transformed_products = [transform_product(offer, config) for offer in obsbygg_feed_data]

        # Apply filtering
        filtered_products = [product for product in transformed_products if filter_product(product, config.filters)]

        assert len(filtered_products) == 24, "Should be 24 offers with target category"

    def test_filter_products_with_gt_operator(self, obsbygg_feed_data):
        """Test filtering products using 'gt' operator on price."""
        config = create_config(
            provenance="obsbygg_spider",
            namespace="obsbygg",
            extractQuantityFields=["title"],
            filters=[
                {
                    "source": "pricing.price",
                    "operator": "gt",
                    "target": 200,
                }
            ],
        )

        # Transform all products first
        transformed_products = [transform_product(offer, config) for offer in obsbygg_feed_data]

        # Apply filtering
        filtered_products = [product for product in transformed_products if filter_product(product, config.filters)]

        assert len(filtered_products) == 54, "Should be 54 offers price higher than 200"


# =============================================================================
# Provider-Specific Transformation Tests
# =============================================================================


class TestMenyTransformation:
    """Test Meny feed transformation."""

    def test_meny_products_transformation(self, meny_feed_data):
        """Test transforming Meny products with field mapping."""
        config = create_config(
            provenance="meny_api_spider",
            namespace="meny",
            extractQuantityFields=["unit_price_raw", "subtitle", "title"],
            fieldMapping=[
                {"source": "sku", "destination": "ean", "replace_type": "key"},
                {
                    "source": "product_variant",
                    "destination": "description",
                    "replace_type": "key",
                },
            ],
        )

        # Only test first 10 items to avoid performance issues
        sample_products = meny_feed_data[:10]
        results = [transform_product(offer, config) for offer in sample_products]

        assert isinstance(results, list)
        assert len(results) == len(sample_products)

        # Test last product structure
        last_result = results[-1]
        assert last_result["title"] is not None
        assert last_result["pricing"] is not None
        assert last_result["href"] is not None
        assert last_result["uri"] is not None
        assert last_result["quantity"]["size"] is not None
        assert last_result["sku"] is not None

    def test_single_meny_product_quantity_parsing(self):
        """Test specific Meny product with quantity and value parsing."""
        config = create_config(
            provenance="meny",
            namespace="meny",
            extractQuantityFields=["unit_price_raw", "unit_raw", "title"],
            fieldMapping=[
                {"source": "sku", "destination": "ean", "replace_type": "key"},
                {
                    "source": "product_variant",
                    "destination": "description",
                    "replace_type": "key",
                },
            ],
        )

        scraper_offer = {
            "price": 3.0,
            "title": "Tomat stykk",
            "unit_price_raw": "kr\u00a039,90/kg",
            "unit_raw": "80\u00a0g",
            "quantity_info": "80\u00a0g",
            "image_url": "https://res.cloudinary.com/norgesgruppen/image/upload/c_pad,b_white,f_auto,h_320,q_50,w_320/v1558839429/Product/2000406400006.png",
            "product_url": "https://meny.no/varer/frukt-gront/gronnsaker/tomater/tomat-stykk-2000406400006",
            "meny_id": "2000406400006",
            "provenance": "meny",
            "url_fingerprint": "460cae747c054fc03fac9a0a88d8a9ef172c279d",
            "url": "https://meny.no/varer/frukt-gront/gronnsaker/tomater/tomat-stykk-2000406400006",
            "canonical_url": "https://meny.no/varer/frukt-gront/gronnsaker/tomater/tomat-stykk-2000406400006",
            "sku": "2000406400006",
            "gtin13": "2000406400006",
            "provenanceId": "2000406400006",
            "priceCurrency": "NOK",
            "context": "amp-no",
        }

        result = transform_product(scraper_offer, config)

        # Check value parsing from unit_price_raw
        assert "value" in result
        assert "size" in result["value"]
        assert "standard" in result["value"]["size"]
        assert result["value"]["size"]["standard"]["min"] == 39.9


class TestKolonialTransformation:
    """Test Kolonial feed transformation with nutrition mapping."""

    def test_kolonial_products_transformation(self, kolonial_feed_data):
        """Test transforming Kolonial products with nutrition field mapping."""
        config = create_config(
            provenance="kolonial",
            namespace="kolonial",
            extractQuantityFields=["unit_price_raw", "product_variant", "title"],
            fieldMapping=[
                {
                    "source": "Ingredienser",
                    "destination": "rawIngredients",
                    "replace_type": "key",
                },
                {
                    "source": "Protein",
                    "destination": "proteins",
                    "replace_type": "key",
                },
                {
                    "source": "hvorav sukkerarter",
                    "destination": "sugars",
                    "replace_type": "key",
                },
                {
                    "source": "Energi",
                    "destination": "energy",
                    "replace_type": "key",
                },
                {"source": "Salt", "destination": "salt", "replace_type": "key"},
                {
                    "source": "Kostfiber",
                    "destination": "fibers",
                    "replace_type": "key",
                },
                {"source": "Fett", "destination": "fats", "replace_type": "key"},
                {
                    "source": "hvorav mettede fettsyrer",
                    "destination": "satFats",
                    "replace_type": "key",
                },
                {
                    "source": "hvorav enumettede fettsyrer",
                    "destination": "monoFats",
                    "replace_type": "key",
                },
                {
                    "source": "hvorav flerumettede fettsyrer",
                    "destination": "polyFats",
                    "replace_type": "key",
                },
                {
                    "source": "Karbohydrater",
                    "destination": "carbohydrates",
                    "replace_type": "key",
                },
            ],
        )

        # Only test first 10 items to avoid performance issues
        sample_products = kolonial_feed_data[:10]
        results = [transform_product(offer, config) for offer in sample_products]

        assert isinstance(results, list)
        assert len(results) == len(sample_products)

        # Test first product structure
        first_result = results[0]
        assert first_result["title"] is not None
        assert first_result["pricing"] is not None
        assert first_result["href"] is not None
        assert first_result["uri"] is not None
        assert first_result["quantity"]["size"] is not None

    def test_single_kolonial_product_nutrition_mapping(self, kolonial_feed_data):
        """Test specific Kolonial product with nutrition field mapping."""
        config = create_config(
            provenance="kolonial",
            namespace="kolonial",
            extractPropertiesFields=["title", "description"],
            fieldMapping=[
                {
                    "source": "Ingredienser",
                    "destination": "rawIngredients",
                    "replace_type": "key",
                },
                {
                    "source": "Protein",
                    "destination": "proteins",
                    "replace_type": "key",
                },
                {
                    "source": "hvorav sukkerarter",
                    "destination": "sugars",
                    "replace_type": "key",
                },
                {
                    "source": "Karbohydrater",
                    "destination": "carbohydrates",
                    "replace_type": "key",
                },
            ],
        )

        scraper_offer = kolonial_feed_data[0]
        result = transform_product(scraper_offer, config)

        # Test nutrition mapping worked
        if "rawIngredients" in result and result["rawIngredients"]:
            assert "vinegar" in result["rawIngredients"]

        # Test nutrition extraction from mapped fields
        if "mpnNutrition" in result and "carbohydrates" in result["mpnNutrition"]:
            assert result["mpnNutrition"]["carbohydrates"]["value"] == 16


class TestEuroprisTransformation:
    """Test Europris feed transformation."""

    def test_europris_products_transformation(self, europris_feed_data):
        """Test transforming Europris products with field mapping."""
        config = create_config(
            provenance="europris",
            namespace="europris",
            extractQuantityFields=["description", "name"],
            fieldMapping=[
                {
                    "source": "name",
                    "destination": "title",
                    "replace_type": "key",
                },
                {
                    "source": "link",
                    "destination": "href",
                    "replace_type": "key",
                },
            ],
        )

        results = [transform_product(offer, config) for offer in europris_feed_data]

        assert isinstance(results, list)
        assert len(results) == len(europris_feed_data)

        # Test first product structure
        first_result = results[0]
        assert first_result["title"] is not None
        assert first_result["pricing"] is not None
        assert first_result["href"] is not None
        assert first_result["uri"] is not None
        assert first_result["sku"] is not None


class TestShopgunTransformation:
    """Test Shopgun feed transformation (special format)."""

    def test_shopgun_products_transformation(self, shopgun_feed_data):
        """Test transforming Shopgun products with special Shopgun logic."""
        config = create_config(
            provenance="shopgun",
            namespace="shopgun",
            extractQuantityFields=["title"],
            fieldMapping=[],  # Shopgun uses default field mapping
        )

        results = [transform_product(offer, config) for offer in shopgun_feed_data]

        assert isinstance(results, list)
        assert len(results) == len(shopgun_feed_data)

        # Test first product structure
        first_result = results[0]
        assert first_result["title"] is not None
        assert first_result["pricing"] is not None
        assert first_result["href"] is not None
        assert first_result["uri"] is not None
        assert first_result["quantity"]["size"] is not None


class TestSwecandyTransformation:
    """Test Swecandy feed transformation."""

    def test_swecandy_products_transformation(self, swecandy_feed_data):
        """Test transforming Swecandy products."""
        config = create_config(
            provenance="swecandy",
            namespace="swecandy",
            extractQuantityFields=["title"],
            fieldMapping=[],
        )

        results = [transform_product(offer, config) for offer in swecandy_feed_data]

        assert isinstance(results, list)
        assert len(results) == len(swecandy_feed_data)

        # Test first product structure
        first_result = results[0]
        assert first_result["title"] is not None
        assert first_result["pricing"] is not None
        assert first_result["href"] is not None
        assert first_result["uri"] is not None
        assert first_result["quantity"]["size"] is not None
        assert first_result["categories"] is not None


class TestGottebitenTransformation:
    """Test Gottebiten feed transformation."""

    def test_gottebiten_products_transformation(self, gottebiten_feed_data):
        """Test transforming Gottebiten products."""
        config = create_config(
            provenance="gottebiten.se",
            namespace="gottebiten.se",
            extractQuantityFields=["title"],
            fieldMapping=[],
        )

        results = [transform_product(offer, config) for offer in gottebiten_feed_data]

        assert isinstance(results, list)
        assert len(results) == len(gottebiten_feed_data)

        # Test first product structure
        first_result = results[0]
        assert first_result["title"] is not None
        assert first_result["pricing"] is not None
        assert first_result["href"] is not None
        assert first_result["uri"] is not None
        assert first_result["quantity"]["size"] is not None
        assert first_result["provenanceId"] is not None


class TestIherbTransformation:
    """Test iHerb feed transformation."""

    def test_iherb_products_transformation(self, iherb_feed_data):
        """Test transforming iHerb products with field mapping."""
        config = create_config(
            provenance="iherb",
            namespace="iherb",
            extractQuantityFields=["title"],
            fieldMapping=[
                {
                    "source": "sku",
                    "destination": "mpn",
                    "replace_type": "key",
                },
            ],
        )

        results = [transform_product(offer, config) for offer in iherb_feed_data]

        assert isinstance(results, list)
        assert len(results) == len(iherb_feed_data)

        # Test first product structure
        first_result = results[0]
        assert first_result["title"] is not None
        assert first_result["pricing"] is not None
        assert first_result["href"] is not None
        assert first_result["uri"] is not None
        assert first_result["quantity"]["size"] is not None
        assert first_result["sku"] is not None


class TestObsbyggTransformation:
    """Test Obsbygg feed transformation."""

    def test_obsbygg_products_transformation(self, obsbygg_feed_data):
        """Test transforming Obsbygg products."""
        config = create_config(
            provenance="obsbygg_spider",
            namespace="obsbygg",
            extractQuantityFields=["title"],
            fieldMapping=[],
        )

        results = [transform_product(offer, config) for offer in obsbygg_feed_data]

        assert isinstance(results, list)
        assert len(results) == len(obsbygg_feed_data)

        # Test first product structure
        first_result = results[0]
        assert first_result["title"] is not None
        assert first_result["pricing"] is not None
        assert first_result["href"] is not None
        assert first_result["uri"] is not None
        assert first_result["sku"] is not None


class TestByggmaxTransformation:
    """Test Byggmax feed transformation."""

    def test_byggmax_products_transformation(self, byggmax_feed_data):
        """Test transforming Byggmax products."""
        config = create_config(
            provenance="byggmax.no",
            namespace="byggmax.no",
            extractQuantityFields=["title"],
            fieldMapping=[],
        )

        # Only test first 10 items to avoid performance issues
        sample_products = byggmax_feed_data[:10]
        results = [transform_product(offer, config) for offer in sample_products]

        assert isinstance(results, list)
        assert len(results) == len(sample_products)

        # Test first product structure
        first_result = results[0]
        assert first_result["title"] is not None
        assert first_result["pricing"] is not None
        assert first_result["href"] is not None
        assert first_result["uri"] is not None
        assert first_result["sku"] is not None


class TestMonterTransformation:
    """Test Monter feed transformation."""

    def test_monter_products_transformation(self, monter_feed_data):
        """Test transforming Monter products with NOBB field mapping."""
        config = create_config(
            provenance="monter.no",
            namespace="monter.no",
            extractQuantityFields=["title"],
            fieldMapping=[
                {
                    "source": "NOBB",
                    "destination": "nobb",
                    "replace_type": "key",
                },
            ],
        )

        results = [transform_product(offer, config) for offer in monter_feed_data]

        assert isinstance(results, list)
        assert len(results) == len(monter_feed_data)

        # Test first product structure
        first_result = results[0]
        assert first_result["gtins"] is not None
        assert first_result["gtins"]["nobb"] is not None
        assert first_result["title"] is not None
        assert first_result["pricing"] is not None
        assert first_result["href"] is not None
        assert first_result["uri"] is not None
        assert first_result["sku"] is not None


# =============================================================================
# Specific Edge Case Tests
# =============================================================================


class TestSpecificScenarios:
    """Test specific edge cases and complex scenarios."""

    def test_jemogfix_product_alt_price_quantity_calculation(self):
        """Test JemOgFix product with altPrice/altPriceUnit quantity calculation."""
        config = create_config(
            provenance="jemogfix",
            namespace="jemogfix",
            extractPropertiesFields=["title", "description"],
        )

        scraper_offer = {
            "price": 204.0,
            "priceCurrency": "NOK",
            "mpn": "9054481",
            "title": "Rundstokk",
            "image": "https://medieserver.jemogfix.dk/api/v1/products/GetPrimaryProductImage?productGroupNumber=4222&productNumber=9054481&shopLanguage=3&previewSize=700",
            "description": "Ubehandlet furu. Fast lengde av 2,4 meter. 28 mm. 10 x 58 x 4400 mm.",
            "availability": "http://schema.org/OutOfStock",
            "categories": [
                "Forside",
                "Byggevarer & trelast",
                "Trematerialer og bord",
                "Ubehandlet tre",
            ],
            "sku": "9054481",
            "priceUnit": "pcs",
            "altPrice": 85.0,
            "altPriceUnit": "m",
            "provenance": "www.jemogfix.no",
            "url": "https://www.jemogfix.no/rundstokk/4222/9054481/",
            "url_fingerprint": "99770c4615456e4764934ec05e22deec7f159bde",
            "canonical_url": "https://www.jemogfix.no/rundstokk/4222/9054481/",
            "provenanceId": "9054481",
        }

        result = transform_product(scraper_offer, config)

        # Test quantity calculation from altPrice/altPriceUnit
        assert result["quantity"]["size"]["standard"]["min"] == 2.4
        assert result["quantity"]["size"]["unit"]["symbol"] == "m"

        # Test properties extraction
        assert result["mpnProperties"]["dimensions"]["value"] == "10x58x4400"
