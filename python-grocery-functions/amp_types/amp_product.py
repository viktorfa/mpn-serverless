from typing import Any, List, Literal, Mapping, Any, TypedDict, Optional
from datetime import datetime
from enum import Enum

from amp_types.quantity_types import ItemsField, Quantity, QuantityField


class PricingField(TypedDict):
    price: float
    priceText: str
    currency: str
    prePrice: float
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
    description: str
    image: list
    imageUrl: str
    pieces: Quantity
    size: Quantity
    value: QuantityField
    quantity: QuantityField
    items: ItemsField
    likes: list
    reports: list
    validFrom: datetime
    validThrough: datetime
    href: str
    provenance: str
    brand: str
    uri: str
    provenanceId: str
    dealer: str
    selectMethod: str
    isPromoted: bool
    availability: str
    additionalProperties: Mapping[str, AdditionalProperty]
    mpnProperties: Mapping[str, AdditionalProperty]
    categories: List[str]
    categories2: List[str]
    gtin: str
    gtins: List[Mapping[str, str]]
    market: str
    isPartner: bool


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
    additionalProperties: List[AdditionalProperty]
    additionalPropertyDict: Mapping[str, AdditionalProperty]
    categories: List[str]
    categories2: List[str]
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


class MappingConfigField(TypedDict):
    value_type: str
    replace_type: Literal["fixed", "key", "ignore"]
    replace_value: Any
    source: str
    destination: str
    text: str
    force_replace: bool


class ScraperConfig(TypedDict):
    provenance: str


class OfferFilterConfig(TypedDict):
    source: str
    operator: Literal["in", "has", "eq", "neq", "gt", "lt"]
    target: str


class DbHandleConfig(TypedDict):
    fieldMapping: List[MappingConfigField]
    filters: List[OfferFilterConfig]
    extractQuantityFields: List[str]
    extractPropertiesFields: List[str]
    extractIngredientsFields: List[str]
    categoriesLimits: List[int]
    ignore_none: bool
    provenance: str
    namespace: str
    collection_name: str
    market: str
    is_partner: bool


class EventHandleConfig(DbHandleConfig):
    feed_key: str


class HandleConfig(EventHandleConfig):
    scrape_time: datetime
    scrapeBatchId: str


class PriceHistoryRecord(TypedDict):
    date: str
    price: float


class PriceHistoryForOffer(TypedDict):
    uri: str
    history: List[PriceHistoryRecord]


class IngredientType(TypedDict):
    key: str
    eNumber: Optional[str]
    name: Optional[str]
    shortDescription: Optional[str]
    processedValue: Optional[int]
    patterns: Optional[list[str]]
