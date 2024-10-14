from sqlalchemy import (
    Column,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
    Numeric,
    Boolean,
    Text,
    TIMESTAMP,
    ForeignKey,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INTEGER, BOOLEAN, ARRAY, TEXT
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, relationship


Base = declarative_base()


class ProductsTable(Base):
    __tablename__ = "products"

    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid_v7()"))
    quantity_unit = Column(Text)
    quantity_amount = Column(Numeric)
    quantity_standard_amount = Column(Numeric)
    nutrition = Column(JSONB, server_default=text("jsonb_build_object()"))
    merged_to = Column(UUID, ForeignKey("products.id"), nullable=True)


class SpiderConfigsTable(Base):
    __tablename__ = "spider_configs"
    __table_args__ = {"schema": "scraping"}

    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid_v7()"))
    created_at = Column(TIMESTAMP, server_default=text("now()"))
    updated_at = Column(TIMESTAMP, server_default=text("now()"))
    mongo_id = Column(String)
    use_fargate = Column(Boolean, nullable=True)
    settings = Column(JSONB)
    crawl_kwargs = Column(JSONB, nullable=True)
    other_kwargs = Column(JSONB, nullable=True)
    spider_name = Column(String)
    cron = Column(String, nullable=True)
    rate = Column(String, nullable=True)
    region = Column(String, nullable=True)
    enabled = Column(Boolean)


class HandleConfigsTable(Base):
    __tablename__ = "handle_configs"
    __table_args__ = {"schema": "scraping"}

    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid_v7()"))
    created_at = Column(TIMESTAMP, server_default=text("now()"))
    updated_at = Column(TIMESTAMP, server_default=text("now()"))
    mongo_id = Column(String)
    provenance = Column(String)
    additional_config = Column(JSONB)
    field_mapping = Column(JSONB, nullable=True)
    extract_quantity_fields = Column(JSONB, nullable=True)
    context = Column(String)
    namespace = Column(String)
    is_partner = Column(Boolean, default=False)
    market = Column(String)


class HandleRunBatchesTable(Base):
    __tablename__ = "handle_run_batches"
    __table_args__ = {"schema": "scraping"}

    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid_v7()"))
    scrape_time = Column(TIMESTAMP, nullable=False)
    status = Column(Text, nullable=False, default="INITIAL")
    scrape_batch_id = Column(Text, nullable=False)
    handle_config_id = Column(UUID, ForeignKey("scraping.handle_configs.id"))
    categories_v = Column(Integer, nullable=False)
    ingredients_v = Column(Integer, nullable=False)
    nutrition_v = Column(Integer, nullable=False)
    properties_v = Column(Integer, nullable=False)
    stock_v = Column(Integer, nullable=False)
    quantity_v = Column(Integer, nullable=False)


class OffersTable(Base):
    __tablename__ = "offers"

    uri = Column(Text, primary_key=True)
    dealer_key = Column(String)
    href = Column(Text, nullable=False)
    image = Column(Text)
    mpn_stock = Column(String)
    price = Column(Numeric)
    currency = Column(String, nullable=False)
    pre_price = Column(Numeric)
    price_unit = Column(String)
    provenance = Column(String, nullable=False)
    provenance_id = Column(String, nullable=False)
    quantity_unit = Column(String)
    quantity_amount = Column(Numeric)
    quantity_standard_amount = Column(Numeric)
    context = Column(String, nullable=False)
    subtitle = Column(Text)
    title = Column(Text, nullable=False)
    valid_from = Column(TIMESTAMP, nullable=False)
    valid_through = Column(TIMESTAMP, nullable=False)
    value_unit = Column(String)
    value_amount = Column(Numeric)
    value_standard_amount = Column(Numeric)
    brand = Column(String)
    description = Column(Text)
    short_description = Column(Text)
    item_condition = Column(String)
    mpn = Column(String)
    upc = Column(String)
    ahref = Column(Text)
    is_partner = Column(Boolean, default=False)
    market = Column(String, nullable=False)
    is_promotion_restricted = Column(Boolean)
    scrape_batch_id = Column(String)
    brand_key = Column(String)
    vendor_key = Column(String)
    product_id = Column(UUID, ForeignKey("products.id"), nullable=False)

    product = relationship("ProductsTable", backref="offers")

    # New fields for price differences
    difference_7_days_mean = Column(Numeric)
    difference_7_days_mean_percentage = Column(Numeric)
    difference_30_days_mean = Column(Numeric)
    difference_30_days_mean_percentage = Column(Numeric)
    difference_90_days_mean = Column(Numeric)
    difference_90_days_mean_percentage = Column(Numeric)
    difference_180_days_mean = Column(Numeric)
    difference_180_days_mean_percentage = Column(Numeric)
    difference_365_days_mean = Column(Numeric)
    difference_365_days_mean_percentage = Column(Numeric)

    prices_migrated_at = Column(TIMESTAMP)


class OfferPricesTable(Base):
    __tablename__ = "offer_prices"

    uri = Column(String, ForeignKey("offers.uri"), primary_key=True)
    price = Column(Numeric, nullable=False)
    recorded_at = Column(TIMESTAMP, nullable=False)


class GtinsTable(Base):
    __tablename__ = "gtins"

    gtin: Mapped[str] = mapped_column(Text, primary_key=True)
    product_id = Column(UUID, ForeignKey("products.id"), nullable=False)


class OfferHasGtinTable(Base):
    __tablename__ = "offer_has_gtin"

    offer_uri = Column(Text, ForeignKey("offers.uri"), primary_key=True)
    gtin = Column(Text, ForeignKey("gtins.gtin"), primary_key=True)
    match_type = Column(Text, nullable=False)


class ProductMarketInfoTable(Base):
    __tablename__ = "product_market_infos"

    product_id = Column(UUID, ForeignKey("products.id"), primary_key=True)
    market = Column(Text, primary_key=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    subtitle = Column(Text)
    short_description = Column(Text)
    brand_key = Column(Text)
    vendor_key = Column(Text)
    context = Column(Text, nullable=False)
    category_key = Column(Text)
    category_keys = Column(ARRAY(TEXT))


class BrandsTable(Base):
    __tablename__ = "brands"

    key = Column(Text, primary_key=True)
    market = Column(Text, primary_key=True)
    title = Column(Text, nullable=False)


class DealersTable(Base):
    __tablename__ = "dealers"

    key = Column(Text, primary_key=True)
    market = Column(Text, primary_key=True)
    title = Column(Text, nullable=False)
    is_partner = Column(Boolean, default=False)


class VendorsTable(Base):
    __tablename__ = "vendors"

    key = Column(Text, primary_key=True)
    market = Column(Text, primary_key=True)
    title = Column(Text, nullable=False)


class CategoryMappingsTable(Base):
    __tablename__ = "category_mappings"

    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid_v7()"))
    created_at = Column(TIMESTAMP, server_default=text("now()"))
    updated_at = Column(TIMESTAMP, server_default=text("now()"))
    context = Column(TEXT, primary_key=True)
    dealer_key = Column(TEXT, primary_key=True)
    source = Column(ARRAY(TEXT))
    target = Column(TEXT)

    # __table_args__ = (
    #    ForeignKeyConstraint(
    #        ["context", "target"],
    #        ["public.categories.context", "public.categories.target"],
    #        name="category_mappings_context_target_fkey",
    #    ),
    # )


class CategoriesTable(Base):
    __tablename__ = "categories"

    created_at = Column(TIMESTAMP, server_default=text("now()"))
    updated_at = Column(TIMESTAMP, server_default=text("now()"))
    key = Column(TEXT, primary_key=True)
    context = Column(TEXT, primary_key=True)
    level = Column(INTEGER)
    title = Column(TEXT)
    description = Column(TEXT, nullable=True)
    active = Column(BOOLEAN)
    parent = Column(TEXT, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint("key", "context"),
        ForeignKeyConstraint(
            ["context", "parent"],
            ["categories.context", "categories.key"],
            name="categories_parent_context_fkey",
        ),
    )


class IngredientsTable(Base):
    __tablename__ = "ingredients"

    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid_v7()"))
    created_at = Column(TIMESTAMP, server_default=text("now()"))
    updated_at = Column(TIMESTAMP, server_default=text("now()"))
    title = Column(TEXT, nullable=False)
    patterns = Column(ARRAY(TEXT), nullable=False, default=[])
    processed_value = Column(INTEGER, default=0)
    e_number = Column(TEXT)
    short_description = Column(TEXT)


class ProductHasIngredientTable(Base):
    __tablename__ = "product_has_ingredient"

    product_id = Column(UUID, ForeignKey("products.id"), primary_key=True)
    ingredient_id = Column(UUID, ForeignKey("ingredients.id"), primary_key=True)


class DenormalizedProductsTable(Base):
    __tablename__ = "denormalized_products"
    product_id = Column(UUID, primary_key=True)
    market = Column(String, primary_key=True)
    image_url = Column(Text)
    title = Column(Text, nullable=False)
    subtitle = Column(Text)
    description = Column(Text)
    short_description = Column(Text)
    brand_key = Column(String)
    vendor_key = Column(String)
    gtins = Column(ARRAY(String))
    ingredients = Column(JSONB)
    nutrition = Column(JSONB)
    quantity_unit = Column(String)
    quantity_amount = Column(Numeric)
    offers = Column(ARRAY(JSONB))
    price_min = Column(Numeric)
    price_max = Column(Numeric)
    value_min = Column(Numeric)
    value_max = Column(Numeric)
    valid_through = Column(TIMESTAMP, nullable=False)
    context = Column(String, nullable=False)
    category_key = Column(String)
    dealer_keys = Column(ARRAY(String))
    created_at = Column(TIMESTAMP, server_default=text("now()"))
    updated_at = Column(TIMESTAMP, server_default=text("now()"))
    category_keys = Column(ARRAY(TEXT))
    page_views = Column(INTEGER)
