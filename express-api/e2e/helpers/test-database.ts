import { Pool } from "pg";
import { Kysely, PostgresDialect } from "kysely";
import type { DB } from "../../generated/kysely";

export class TestDatabase {
  private db: Kysely<DB>;
  private pool: Pool;

  constructor() {
    this.pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      max: 5, // Smaller pool for tests
      min: 0,
      idleTimeoutMillis: 5000,
    });

    this.db = new Kysely<DB>({
      dialect: new PostgresDialect({
        pool: () => this.pool,
      }),
    });
  }

  getDb(): Kysely<DB> {
    return this.db;
  }

  async connect(): Promise<void> {
    // Test the connection
    try {
      await this.db.selectFrom("offers").select("uri").limit(1).execute();
    } catch (error) {
      throw new Error(`Test database connection failed: ${error.message}`);
    }
  }

  async cleanup(): Promise<void> {
    // Clean up test data in reverse dependency order
    // This will be expanded as the team adds more tables

    try {
      await this.db.deleteFrom("offer_has_gtin").execute();
      await this.db.deleteFrom("product_has_ingredient").execute();
      await this.db.deleteFrom("offer_prices").execute();
      await this.db.deleteFrom("offers").execute();
      await this.db.deleteFrom("denormalized_products").execute();
      await this.db.deleteFrom("product_market_infos").execute();
      await this.db.deleteFrom("products").execute();
      await this.db.deleteFrom("dealers").execute();
      await this.db.deleteFrom("brands").execute();
      await this.db.deleteFrom("vendors").execute();
      await this.db.deleteFrom("categories").execute();
      await this.db.deleteFrom("ingredients").execute();
    } catch (error) {
      // Some tables might not exist yet, that's OK
      console.warn("Cleanup warning (this is usually OK):", error.message);
    }
  }

  async seedTestData(): Promise<void> {
    // Basic seed data that tests can build upon

    // Seed Norwegian dealers
    await this.db
      .insertInto("dealers")
      .values([
        {
          key: "rema1000",
          title: "REMA 1000",
          url: "https://rema.no",
          logo_url: "https://rema.no/logo.png",
          market: "no",
          description: "REMA 1000 - Leading Norwegian grocery retailer",
          is_partner: true,
        },
        {
          key: "coop",
          title: "Coop",
          url: "https://coop.no",
          logo_url: "https://coop.no/logo.png",
          market: "no",
          description: "Coop - Norwegian cooperative retailer",
          is_partner: true,
        },
      ])
      .onConflict((oc) =>
        oc.column("key").doUpdateSet({
          title: (eb) => eb.ref("excluded.title"),
        }),
      )
      .execute();

    // Seed basic ingredients
    await this.db
      .insertInto("ingredients")
      .values([
        {
          id: "ingredient_1",
          title: "Water",
          short_description: "Water ingredient",
          processed_value: 0,
        },
        {
          id: "ingredient_2",
          title: "Milk",
          short_description: "Milk ingredient",
          processed_value: 1,
        },
      ])
      .onConflict((oc) =>
        oc.column("id").doUpdateSet({
          title: (eb) => eb.ref("excluded.title"),
        }),
      )
      .execute();
  }

  async insertTestOffer(offerData: Partial<DB["offers"]>): Promise<void> {
    const defaultOffer = {
      uri: "test:12345",
      title: "Test Product",
      href: "https://test.no/product/12345",
      price: "25.90",
      currency: "NOK",
      dealer_key: "rema1000",
      market: "no",
      context: "amp-no",
      brand: "Test Brand",
      brand_key: "testbrand",
      product_id: "test-product-123",
      provenance: "test",
      provenance_id: "test-provenance-123",
      valid_from: new Date(),
      valid_through: new Date(Date.now() + 86400000), // 24 hours
      created_at: new Date(),
      updated_at: new Date(),
      quantity_amount: "1.0",
      quantity_unit: "kg",
      value_amount: "25.90",
      value_unit: "NOK/kg",
      mpn_stock: "in_stock",
      is_promotion_restricted: false,
      is_partner: true,
      vendor_key: "rema1000",
      item_condition: "new",
      ...offerData,
    };

    await this.db.insertInto("offers").values(defaultOffer).execute();
  }

  async close(): Promise<void> {
    await this.db.destroy();
  }
}

export async function createTestDatabase(): Promise<TestDatabase> {
  const testDb = new TestDatabase();
  await testDb.connect();
  await testDb.cleanup(); // Clean slate for each test
  await testDb.seedTestData();
  return testDb;
}
