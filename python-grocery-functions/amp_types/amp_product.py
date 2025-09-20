from collections.abc import Mapping
from datetime import datetime
from enum import Enum
from typing import Any, Literal, TypedDict

from amp_types.quantity_types import ItemsField, Quantity, QuantityField
from scraper_feed.scraper_configs import MappingConfigField


class NutritionalData(TypedDict):
    value: float


class PricingField(TypedDict):
    price: float | None
    priceText: str
    currency: str
    prePrice: float | None
    priceUnit: str
    validFrom: datetime
    validThrough: datetime


class LocationField(TypedDict):
    pass


class AdditionalProperty(TypedDict):
    key: str
    type: str
    extraType: str
    value: Any


class MpnOffer(TypedDict):
    title: str
    pricing: PricingField
    subtitle: str
    shortDescription: str
    description: str
    imageUrl: str
    pieces: Quantity
    value: QuantityField
    quantity: QuantityField
    items: ItemsField
    validFrom: datetime
    validThrough: datetime
    href: str
    provenance: str
    brand: str | None
    brandKey: str | None
    vendor: str | None
    vendorKey: str | None
    dealer: str
    uri: str
    provenanceId: str
    availability: str
    additionalProperties: Mapping[str, AdditionalProperty]
    mpnProperties: Mapping[str, AdditionalProperty]
    mpnNutrition: Mapping[str, NutritionalData]
    rawIngredients: list[str]
    categories: list[str]
    gtins: Mapping[str, str]
    market: str
    isPartner: bool


class ProcessedMpnOffer(MpnOffer):
    siteCollection: str
    scrapeBatchId: str
    namespace: str
    context: str


class ScraperOffer(TypedDict):
    title: str
    price: float
    prePrice: float
    priceCurrency: str
    priceUnit: str
    description: str
    shortDescription: str
    image: str
    url: str
    provenance: str
    brand: str
    vendor: str
    variant: str
    model: str
    provenanceId: str
    dealer: str
    availability: str
    itemCondition: str
    additionalProperties: list[AdditionalProperty]
    additionalPropertyDict: Mapping[str, AdditionalProperty]
    categories: list[str]
    gtin: str
    gtin8: str
    gtin12: str
    gtin13: str
    ean: str
    upc: str
    sku: str
    mpn: str


class ReplaceType(Enum):
    fixed = 1
    key = 2
    ignore = 3


class ScraperConfig(TypedDict):
    provenance: str


class OfferFilterConfig(TypedDict):
    source: str
    operator: Literal["in", "has", "eq", "neq", "gt", "lt"]
    target: str


class DbHandleConfig(TypedDict):
    id: str
    fieldMapping: list[MappingConfigField]
    filters: list[OfferFilterConfig]
    extractQuantityFields: list[str]
    extractPropertiesFields: list[str]
    extractIngredientsFields: list[str]
    categoriesLimits: list[int]
    ignore_none: bool
    provenance: str
    namespace: str
    collection_name: str
    market: str
    is_partner: bool


class EventHandleConfig(DbHandleConfig):
    feed_key: str
    use_postgres: bool


class HandleConfig(EventHandleConfig):
    scrape_time: datetime
    scrapeBatchId: str


class HandleConfigNew(EventHandleConfig):
    scrape_time: datetime
    scrapeBatchId: str
    context: str


class PriceHistoryRecord(TypedDict):
    date: str
    price: float


class PriceHistoryForOffer(TypedDict):
    uri: str
    history: list[PriceHistoryRecord]


class IngredientType(TypedDict):
    key: str
    eNumber: str | None
    name: str | None
    shortDescription: str | None
    processedValue: int | None
    patterns: list[str] | None
