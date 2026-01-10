"""
Pydantic models for the offer transformation pipeline.

These models provide runtime validation and better IDE support for the transformation stages.
"""

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ValidationError

# Removed the problematic imports that conflict with Pydantic


class NutritionalEntry(BaseModel):
    """Single nutritional data entry."""

    key: str
    value: float
    unit: str


class PricingData(BaseModel):
    """Pricing information for an offer."""

    price: float | None = None
    priceText: str = ""
    currency: str = "NOK"
    prePrice: float | None = None
    priceUnit: str = "pcs"
    validFrom: datetime
    validThrough: datetime


class TransformedOffer(BaseModel):
    """
    Represents an offer after initial field mapping but before enrichment.
    This is the input to transform_regular_product.
    """

    # Required fields
    title: str
    url: str
    provenanceId: str

    # Optional basic fields
    subtitle: str = ""
    description: str = ""
    shortDescription: str = ""
    imageUrl: str = ""
    trackingUrl: str | None = None

    # Temporal fields
    validFrom: str | datetime | None = None
    validThrough: str | datetime | None = None

    # Product identification
    dealer: str | None = None
    brand: str | None = None
    vendor: str | None = None

    # Categories and classification
    categories: list[str] = Field(default_factory=list)

    # Raw quantity and pricing data
    price: float | None = None
    prePrice: float | None = None
    priceCurrency: str = "NOK"
    priceUnit: str = "pcs"

    # Additional data
    additionalProperties: list[dict[str, Any]] = Field(default_factory=list)

    model_config = {"extra": "allow"}  # Allow additional fields


class EnrichedOffer(BaseModel):
    """
    Represents an offer after core transformation (output of transform_regular_product).
    Contains all the enriched data before finalization.
    """

    # Core identification
    provenanceId: str
    uri: str
    href: str
    ahref: str | None = None

    # Basic content
    title: str
    subtitle: str = ""
    description: str = ""
    shortDescription: str = ""
    imageUrl: str = ""
    provenance: str

    # Business data
    dealer: str
    pricing: PricingData

    # Temporal
    validFrom: datetime
    validThrough: datetime

    # Product data
    categories: list[str] = Field(default_factory=list)
    gtins: dict[str, str] = Field(default_factory=dict)

    # Quantity data (simplified for validation)
    quantity: dict[str, Any] | None = None
    value: dict[str, Any] | None = None
    items: dict[str, Any] | None = None

    # Enriched data
    dimensions: dict[str, Any] = Field(default_factory=dict)
    properties: dict[str, Any] = Field(default_factory=dict)
    mpnStock: str | None = None
    mpnProperties: dict[str, Any] = Field(default_factory=dict)
    mpnNutrition: dict[str, NutritionalEntry] = Field(default_factory=dict)
    rawIngredients: list[str] = Field(default_factory=list)


class FinalizedOffer(BaseModel):
    """
    Represents the final offer after all processing and field selection.
    This should match what goes to the database.
    """

    # All the fields from EnrichedOffer plus:

    # Market and context
    market: str
    isPartner: bool
    isRecent: bool

    # Generated keys
    dealerKey: str
    brandKey: str | None = None
    vendorKey: str | None = None

    # Version metadata
    mpnCategoriesV: int
    mpnIngredientsV: int
    mpnNutritionV: int
    mpnPropertiesV: int
    mpnStockV: int
    mpnQuantityV: int

    # All the core fields from EnrichedOffer
    provenanceId: str
    uri: str
    href: str
    ahref: str | None = None
    title: str
    subtitle: str = ""
    description: str = ""
    shortDescription: str = ""
    imageUrl: str = ""
    provenance: str
    dealer: str
    pricing: PricingData
    validFrom: datetime
    validThrough: datetime
    categories: list[str] = Field(default_factory=list)
    gtins: dict[str, str] = Field(default_factory=dict)
    quantity: dict[str, Any] | None = None
    value: dict[str, Any] | None = None
    items: dict[str, Any] | None = None
    dimensions: dict[str, Any] = Field(default_factory=dict)
    properties: dict[str, Any] = Field(default_factory=dict)
    mpnStock: str | None = None
    mpnProperties: dict[str, Any] = Field(default_factory=dict)
    mpnNutrition: dict[str, NutritionalEntry] = Field(default_factory=dict)
    rawIngredients: list[str] = Field(default_factory=list)

    # Optional book fields
    book_uri: str | None = None
    book_type: str | None = None
    isbn: str | None = None
    isbn10: str | None = None
    isbn13: str | None = None

    model_config = {"extra": "allow"}  # Allow additional fields for flexibility


def validate_offer_data(data: dict[str, Any], stage: str = "unknown") -> bool:
    """
    Optional validation function that can catch type issues early.

    Args:
        data: The offer data dictionary to validate
        stage: The transformation stage (for logging)

    Returns:
        True if validation passes, False otherwise
    """
    try:
        # Try to validate key fields that commonly cause issues
        if "pricing" in data and isinstance(data["pricing"], dict):
            PricingData(**data["pricing"])

        # Check for required fields
        required_fields = ["provenanceId", "uri", "dealer", "title"]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            logging.warning(f"Validation failed at {stage}: Missing required fields: {missing_fields}")
            return False

        # Check data types for common fields
        type_checks = {
            "categories": list,
            "gtins": dict,
            "title": str,
            "dealer": str,
        }

        for field, expected_type in type_checks.items():
            if field in data and data[field] is not None and not isinstance(data[field], expected_type):
                actual_type = type(data[field]).__name__
                expected_type_name = expected_type.__name__
                logging.warning(
                    f"Validation failed at {stage}: Field '{field}' expected {expected_type_name}, got {actual_type}"
                )
                return False

        return True

    except ValidationError as e:
        logging.warning(f"Pydantic validation failed at {stage}: {e}")
        return False
    except Exception as e:
        logging.warning(f"Unexpected validation error at {stage}: {e}")
        return False
