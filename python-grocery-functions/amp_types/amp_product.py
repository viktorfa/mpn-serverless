from typing_extensions import TypedDict
from datetime import datetime

from amp_types.quantity_types import QuantityField, ValueField, ItemsField


class PricingField(TypedDict):
    price: float
    price_text: str
    currency: str
    pre_price: float


class LocationField(TypedDict):
    pass


class AmpProduct(TypedDict):
    heading: str
    pricing: PricingField
    description: str
    images: list
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
    provenance_id: str
    dealer: str
    type: str
    is_discounted: bool
    creator_id: str
    select_method: str
    is_promoted: bool
    stock_status: str
    is_active: bool


