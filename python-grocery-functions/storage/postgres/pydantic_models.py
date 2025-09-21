from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from scraper_feed.scraper_configs import DEFAULT_EXTRACT_CATEGORIES_FIELD


class NutritionType(BaseModel):
    fats: float | None = None
    carbohydrates: float | None = None
    proteins: float | None = None
    satFats: float | None = None
    monoFats: float | None = None
    polyFats: float | None = None
    salt: float | None = None
    polyols: float | None = None
    fibers: float | None = None
    starch: float | None = None
    sugars: float | None = None
    kcals: float | None = None


class QuantityFieldsMixin(BaseModel):
    quantity_unit: str | None
    quantity_amount: float | None
    quantity_standard_amount: float | None


class MarketInfoFieldsMixin(BaseModel):
    market: str
    title: str
    description: str | None
    subtitle: str | None
    short_description: str | None
    brand_key: str | None
    vendor_key: str | None


class ProductInfo(QuantityFieldsMixin):
    nutrition: NutritionType | None
    merged_to: UUID | None

    model_config = ConfigDict(from_attributes=True)


class DbProductInfo(ProductInfo):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class MarketInfo(MarketInfoFieldsMixin):
    context: str
    category_key: str | None
    category_keys: list[str] | None

    model_config = ConfigDict(from_attributes=True)


class DbMarketInfo(MarketInfo):
    product_id: UUID

    model_config = ConfigDict(from_attributes=True)


class MpnGtin(BaseModel):
    gtin: str
    product_id: UUID

    model_config = ConfigDict(from_attributes=True)


class MpnBrand(BaseModel):
    key: str
    title: str
    market: str

    model_config = ConfigDict(from_attributes=True)


class ProductHasIngredient(BaseModel):
    product_id: UUID
    ingredient_id: UUID

    model_config = ConfigDict(from_attributes=True)


class PreparedData(BaseModel):
    offer_gtins: set[str]
    offer_has_gtin_list: list[dict[str, str]]
    gtin_offer_map: dict[str, set[str]]
    gtin_market_info_map: dict[str, MarketInfo]
    gtin_product_map: dict[str, ProductInfo]
    offer_to_gtins: dict[str, list[str]]
    gtin_offer_object_map: dict[str, Any]


class PgOffer(BaseModel):
    uri: str
    dealer_key: str | None
    href: str
    image: str | None
    mpn_stock: str | None
    price: float | None
    currency: str | None
    pre_price: float | None
    price_unit: str | None
    provenance: str
    provenance_id: str
    quantity_unit: str | None
    quantity_amount: float | None
    quantity_standard_amount: float | None
    context: str
    subtitle: str | None
    title: str
    valid_from: datetime
    valid_through: datetime
    value_unit: str | None
    value_amount: float | None
    value_standard_amount: float | None
    brand: str | None
    description: str | None
    short_description: str | None
    item_condition: str | None
    mpn: str | None
    upc: str | None
    ahref: str | None
    is_partner: bool | None
    market: str
    is_promotion_restricted: bool | None
    scrape_batch_id: str
    brand_key: str | None
    vendor_key: str | None

    model_config = ConfigDict(from_attributes=True)


class PydanticHandleConfig(BaseModel):
    id: str
    provenance: str
    namespace: str
    context: str
    market: str
    is_partner: bool = False
    categoriesLimits: list[int] = Field(default_factory=list)
    filters: list[Any] = Field(default_factory=list)
    fieldMapping: list[Any] = Field(default_factory=list)
    extractQuantityFields: list[str] = Field(default_factory=list)
    categoriesField: str = DEFAULT_EXTRACT_CATEGORIES_FIELD
    extractPropertiesFields: list[str] = Field(default_factory=list)
    extractIngredientsFields: list[str] = Field(default_factory=list)
    ignore_none: bool = False

    model_config = ConfigDict(from_attributes=True)


class HandleFeedConfig(PydanticHandleConfig):
    scrape_time: datetime
    scrapeBatchId: str
    model_config = ConfigDict(
        frozen=True,  # Immutable
        from_attributes=True,  # Keep existing behavior
    )
