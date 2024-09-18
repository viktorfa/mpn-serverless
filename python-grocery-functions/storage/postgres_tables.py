from sqlalchemy import (
    UUID,
    ForeignKey,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    Text,
    TIMESTAMP,
)
from sqlalchemy.schema import PrimaryKeyConstraint, UniqueConstraint

metadata = MetaData()

scrape_batches_table = Table(
    "scrape_batches",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("scrape_time", TIMESTAMP, nullable=False),
    Column("status", Text, nullable=False, default="INITIAL"),
    Column("scrape_batch_id", Text, nullable=False),
    Column("config_id", UUID, nullable=True),
    Column("categories_v", Integer, nullable=False),
    Column("ingredients_v", Integer, nullable=False),
    Column("nutrition_v", Integer, nullable=False),
    Column("properties_v", Integer, nullable=False),
    Column("stock_v", Integer, nullable=False),
    Column("quantity_v", Integer, nullable=False),
)

# Define the offers table using SQLAlchemy Core
offers_table = Table(
    "offers",
    metadata,
    Column("uri", Text, primary_key=True),
    Column("dealer_key", String),
    Column("href", Text, nullable=False),
    Column("image", Text),
    Column("mpn_stock", String),
    Column("price", Numeric),
    Column("currency", String, nullable=False),
    Column("pre_price", Numeric),
    Column("price_unit", String),
    Column("provenance", String, nullable=False),
    Column("provenance_id", String, nullable=False),
    Column("quantity_unit", String),
    Column("quantity_amount", Numeric),
    Column("quantity_standard_amount", Numeric),
    Column("site_collection", String, nullable=False),
    Column("subtitle", Text),
    Column("title", Text, nullable=False),
    Column("valid_from", TIMESTAMP, nullable=False),
    Column("valid_through", TIMESTAMP, nullable=False),
    Column("value_unit", String),
    Column("value_amount", Numeric),
    Column("value_standard_amount", Numeric),
    Column("brand", String),
    Column("description", Text),
    Column("short_description", Text),
    Column("item_condition", String),
    Column("mpn", String),
    Column("upc", String),
    Column("ahref", Text),
    Column("is_partner", Boolean, default=False),
    Column("market", String, nullable=False),
    Column("is_promotion_restricted", Boolean),
    Column("scrape_batch_id", String),
    Column("brand_key", String),
    Column("vendor_key", String),
    Column("product_id", UUID, ForeignKey("products.id"), nullable=False),
    keep_existing=True,
)


offer_prices_table = Table(
    "offer_prices",
    metadata,
    Column("uri", String, ForeignKey("offers.uri"), nullable=False),
    Column("price", Numeric, nullable=False),
    Column("recorded_at", TIMESTAMP, nullable=False),
    keep_existing=True,
)

gtins_table = Table(
    "gtins",
    metadata,
    Column("gtin", Text, primary_key=True),
    Column("product_id", UUID, ForeignKey("products.id"), nullable=False),
)

offer_has_gtin_table = Table(
    "offer_has_gtin",
    metadata,
    Column("offer_uri", Text, ForeignKey("offers.uri"), nullable=False),
    Column("gtin", Text, ForeignKey("gtins.gtin"), nullable=False),
    Column("match_type", Text, nullable=False),
    # Composite primary key for this table
    PrimaryKeyConstraint("offer_uri", "gtin"),
)

products_table = Table(
    "products",
    metadata,
    Column("id", UUID, primary_key=True),
)

product_market_info_table = Table(
    "product_market_infos",
    metadata,
    Column("product_id", Integer, ForeignKey("products.id"), nullable=False),
    Column("market", Text, nullable=False),  # Locale or market, e.g., 'NO', 'SE', 'US'
    Column("title", Text, nullable=False),
    Column("description", Text),
    PrimaryKeyConstraint(
        "product_id", "market", name="product_market_infos_pkey"
    ),  # One entry per product per market
)


brands_table = Table(
    "brands",
    metadata,
    Column("key", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("market", Text, nullable=False),
    # Define composite primary key
    PrimaryKeyConstraint("key", "market", name="brands_pkey"),
    UniqueConstraint("key", "market", name="brands_key_market_key"),
    keep_existing=True,
)

dealers_table = Table(
    "dealers",
    metadata,
    Column("key", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("market", Text, nullable=False),
    Column("is_partner", Boolean, default=False),
    # Define composite primary key
    PrimaryKeyConstraint("key", "market", name="dealers_pkey"),
    UniqueConstraint("key", "market", name="dealers_key_market_key"),
    keep_existing=True,
)

vendors_table = Table(
    "vendors",
    metadata,
    Column("key", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("market", Text, nullable=False),
    # Define composite primary key
    PrimaryKeyConstraint("key", "market", name="vendors_pkey"),
    UniqueConstraint("key", "market", name="vendors_key_market_key"),
    keep_existing=True,
)
