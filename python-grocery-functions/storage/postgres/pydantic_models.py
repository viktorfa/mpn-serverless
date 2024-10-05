from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Set, List, Dict, Any
from datetime import datetime

from amp_types.amp_product import ProcessedMpnOffer
from scraper_feed.scraper_configs import DEFAULT_EXTRACT_CATEGORIES_FIELD


class NutritionType(BaseModel):
    fats: Optional[float] = None
    carbohydrates: Optional[float] = None
    proteins: Optional[float] = None
    satFats: Optional[float] = None
    monoFats: Optional[float] = None
    polyFats: Optional[float] = None
    salt: Optional[float] = None
    polyols: Optional[float] = None
    fibers: Optional[float] = None
    starch: Optional[float] = None
    sugars: Optional[float] = None
    kcals: Optional[float] = None


class QuantityFieldsMixin(BaseModel):
    quantity_unit: Optional[str]
    quantity_amount: Optional[float]
    quantity_standard_amount: Optional[float]


class MarketInfoFieldsMixin(BaseModel):
    market: str
    title: str
    description: Optional[str]
    subtitle: Optional[str]
    short_description: Optional[str]
    brand_key: Optional[str]
    vendor_key: Optional[str]


class ProductInfo(QuantityFieldsMixin):
    nutrition: Optional[NutritionType]
    merged_to: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class DbProductInfo(ProductInfo):
    id: str

    model_config = ConfigDict(from_attributes=True)


class MarketInfo(MarketInfoFieldsMixin):
    context: str
    category_key: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class DbMarketInfo(MarketInfo):
    product_id: str

    model_config = ConfigDict(from_attributes=True)


class PreparedData(BaseModel):
    offer_gtins: Set[str]
    offer_has_gtin_list: List[Dict[str, str]]
    gtin_offer_map: Dict[str, Set[str]]
    gtin_market_info_map: Dict[str, MarketInfo]
    gtin_product_map: Dict[str, ProductInfo]
    offer_to_gtins: Dict[str, List[str]]
    gtin_offer_object_map: Dict[str, Any]


class PgOffer(BaseModel):
    uri: str
    dealer_key: Optional[str]
    href: str
    image: Optional[str]
    mpn_stock: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    pre_price: Optional[float]
    price_unit: Optional[str]
    provenance: str
    provenance_id: str
    quantity_unit: Optional[str]
    quantity_amount: Optional[float]
    quantity_standard_amount: Optional[float]
    site_collection: str
    subtitle: Optional[str]
    title: str
    valid_from: datetime
    valid_through: datetime
    value_unit: Optional[str]
    value_amount: Optional[float]
    value_standard_amount: Optional[float]
    brand: Optional[str]
    description: Optional[str]
    item_condition: Optional[str]
    mpn: Optional[str]
    upc: Optional[str]
    ahref: Optional[str]
    is_partner: Optional[bool]
    market: str
    is_promotion_restricted: Optional[bool]
    scrape_batch_id: str
    brand_key: Optional[str]
    vendor_key: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class PydanticHandleConfig(BaseModel):
    id: str
    provenance: str
    namespace: str
    collection_name: str
    market: str
    is_partner: bool = False
    categoriesLimits: List[int] = Field(default_factory=list)
    filters: List[Any] = Field(default_factory=list)
    fieldMapping: List[Any] = Field(default_factory=list)
    extractQuantityFields: List[str] = Field(default_factory=list)
    categoriesField: str = DEFAULT_EXTRACT_CATEGORIES_FIELD
    extractPropertiesFields: List[str] = Field(default_factory=list)
    extractIngredientsFields: List[str] = Field(default_factory=list)
    ignore_none: bool = False

    model_config = ConfigDict(from_attributes=True)
