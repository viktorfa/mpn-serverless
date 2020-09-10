from typing_extensions import TypedDict
from typing import Dict, Any, TypeVar, List, Mapping, Any
from datetime import datetime
from enum import Enum

from amp_types.quantity_types import QuantityField, ValueField, ItemsField, Quantity


class PricingField(TypedDict):
    price: float
    priceText: str
    currency: str
    prePrice: float
    validFrom: datetime
    validThrough: datetime


class LocationField(TypedDict):
    pass


class AdditionalProperty(TypedDict):
    key: str
    type: str
    extraType: str
    value: Any


class AmpProduct(TypedDict):
    title: str
    pricing: PricingField
    description: str
    image: list
    image_url: str
    quantity: QuantityField
    value: ValueField
    items: ItemsField
    location: LocationField
    likes: list
    reports: list
    run_from: datetime
    run_till: datetime
    href: str
    provenance: str
    brand: str
    uri: str
    provenanceId: str
    dealer: str
    type: str
    is_discounted: bool
    creator_id: str
    select_method: str
    is_promoted: bool
    stock_status: str
    is_active: bool
    additionalProperties: List[AdditionalProperty]
    # Whether to show before the offer starts (useful for one day offers etc)
    showBeforeValid: bool
    categories: List[str]
    categories2: List[str]
    gtin: str


class MpnOffer(TypedDict):
    title: str
    pricing: PricingField
    description: str
    image: list
    imageUrl: str
    pieces: Quantity
    size: Quantity
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
    categories: List[str]
    categories2: List[str]
    gtin: str
    gtins: List[Mapping[str, str]]


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
    replace_type: ReplaceType
    replace_value: Any
    source: str
    destination: str
    text: str
    force_replace: bool


class ScraperConfig(TypedDict):
    provenance: str


class HandleConfig(TypedDict):
    fieldMapping: List[MappingConfigField]
    extractQuantityFields: List[str]
    categoriesLimits: List[int]
    provenance: str
    collection_name: str
