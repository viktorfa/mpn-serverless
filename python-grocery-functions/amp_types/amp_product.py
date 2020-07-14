from typing_extensions import TypedDict
from typing import Dict, Any, TypeVar, List, Mapping, Any
from datetime import datetime

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
    additionalProperty: List[AdditionalProperty]
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
    additionalProperty: List[AdditionalProperty]
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


class MappingConfig(TypedDict):
    additionalProperties: Mapping[str, str]
    fields: Mapping[str, str]
    extractQuantityFields: List[str]


class ScraperConfig(TypedDict):
    source: str

