import { faker } from '@faker-js/faker';
import type { Offers } from '../../generated/kysely';

// Norwegian grocery stores for realistic dealer keys
const NORWEGIAN_DEALERS = [
  'rema1000', 'coop', 'ica', 'kiwi', 'meny', 'joker', 'narvesen'
];

// Norwegian markets and contexts
const MARKETS = ['no', 'se', 'dk'];
const CONTEXTS = ['amp-no', 'amp-se', 'amp-dk'];

// Create a realistic offer using faker
function createRealisticOffer(overrides: Partial<Offers> = {}): Offers {
  const dealerKey = faker.helpers.arrayElement(NORWEGIAN_DEALERS);
  const market = faker.helpers.arrayElement(MARKETS);
  const context = faker.helpers.arrayElement(CONTEXTS);

  // Generate a realistic product SKU
  const sku = faker.number.int({ min: 10000, max: 999999 });
  const uri = `${dealerKey}:${sku}`;

  // Generate realistic grocery product names
  const productTypes = ['Milk', 'Bread', 'Cheese', 'Yogurt', 'Butter', 'Eggs', 'Chicken', 'Salmon', 'Pasta', 'Rice'];
  const brands = ['Tine', 'Q-meieriene', 'Synnøve', 'Kavli', 'Prior', 'Gilde', 'Nortura'];
  const sizes = ['500g', '1L', '250g', '1kg', '2L', '400g'];

  const productType = faker.helpers.arrayElement(productTypes);
  const brand = faker.helpers.arrayElement(brands);
  const size = faker.helpers.arrayElement(sizes);

  const title = `${brand} ${productType} ${size}`;

  // Generate realistic Norwegian store URLs
  const baseUrls = {
    rema1000: 'https://rema.no',
    coop: 'https://coop.no',
    ica: 'https://ica.no',
    kiwi: 'https://kiwi.no',
    meny: 'https://meny.no',
    joker: 'https://joker.no',
    narvesen: 'https://narvesen.no'
  };

  const baseUrl = baseUrls[dealerKey] || 'https://store.no';
  const href = `${baseUrl}/product/${sku}`;
  const ahref = faker.datatype.boolean(0.7) ? `${baseUrl}/aff/product/${sku}` : null;

  // Generate realistic prices in NOK
  const price = faker.number.float({ min: 15.90, max: 299.90, fractionDigits: 2 });
  const prePrice = faker.datatype.boolean(0.3) ?
    faker.number.float({ min: price + 5, max: price + 50, fractionDigits: 2 }) : null;

  const now = new Date();
  const validFrom = faker.date.recent({ days: 30 });
  const validThrough = faker.date.future({ years: 1 });

  return {
    uri,
    title,
    href,
    ahref,
    price: price.toString(),
    pre_price: prePrice?.toString() || null,
    currency: 'NOK',
    dealer_key: dealerKey,
    market,
    context,
    brand,
    brand_key: brand.toLowerCase().replace(' ', ''),
    description: `${title} - Premium quality ${productType.toLowerCase()}`,
    short_description: title,
    subtitle: `${size} - ${brand}`,
    image: faker.image.urlLoremFlickr({ category: 'food' }),
    product_id: faker.string.uuid(),
    provenance: 'scraper',
    provenance_id: faker.string.uuid(),
    valid_from: validFrom,
    valid_through: validThrough,
    created_at: faker.date.recent({ days: 7 }),
    updated_at: faker.date.recent({ days: 1 }),
    quantity_amount: faker.number.float({ min: 0.1, max: 2.0, fractionDigits: 1 }).toString(),
    quantity_unit: faker.helpers.arrayElement(['kg', 'l', 'g', 'ml', 'pcs']),
    quantity_standard_amount: null,
    value_amount: faker.number.float({ min: 10, max: 150, fractionDigits: 2 }).toString(),
    value_standard_amount: null,
    value_unit: 'NOK/kg',
    price_unit: null,
    mpn: null,
    mpn_stock: faker.helpers.arrayElement(['in_stock', 'out_of_stock', 'limited']),
    upc: faker.number.int({ min: 1000000000000, max: 9999999999999 }).toString(),
    item_condition: 'new',
    is_promotion_restricted: faker.datatype.boolean(0.1),
    is_partner: faker.datatype.boolean(0.8),
    vendor_key: dealerKey,
    mongo_id: null,
    scrape_batch_id: faker.string.uuid(),
    prices_migrated_at: null,
    difference_7_days_mean: faker.datatype.boolean(0.6) ?
      faker.number.float({ min: -10, max: 15, fractionDigits: 2 }).toString() : null,
    difference_7_days_mean_percentage: faker.datatype.boolean(0.6) ?
      faker.number.float({ min: -15, max: 25, fractionDigits: 1 }).toString() : null,
    difference_30_days_mean: faker.datatype.boolean(0.5) ?
      faker.number.float({ min: -20, max: 30, fractionDigits: 2 }).toString() : null,
    difference_30_days_mean_percentage: faker.datatype.boolean(0.5) ?
      faker.number.float({ min: -20, max: 40, fractionDigits: 1 }).toString() : null,
    difference_90_days_mean: faker.datatype.boolean(0.4) ?
      faker.number.float({ min: -30, max: 50, fractionDigits: 2 }).toString() : null,
    difference_90_days_mean_percentage: faker.datatype.boolean(0.4) ?
      faker.number.float({ min: -25, max: 60, fractionDigits: 1 }).toString() : null,
    difference_180_days_mean: faker.datatype.boolean(0.3) ?
      faker.number.float({ min: -40, max: 80, fractionDigits: 2 }).toString() : null,
    difference_180_days_mean_percentage: faker.datatype.boolean(0.3) ?
      faker.number.float({ min: -30, max: 100, fractionDigits: 1 }).toString() : null,
    difference_365_days_mean: faker.datatype.boolean(0.2) ?
      faker.number.float({ min: -50, max: 120, fractionDigits: 2 }).toString() : null,
    difference_365_days_mean_percentage: faker.datatype.boolean(0.2) ?
      faker.number.float({ min: -40, max: 150, fractionDigits: 1 }).toString() : null,
    ...overrides
  };
}

// Mock database that generates realistic data on the fly
export function createRealisticMockDatabase() {
  // In-memory store for consistent data across queries
  const offerStore = new Map<string, Offers>();

  // Helper to get or create an offer by URI
  const getOrCreateOffer = (uri: string): Offers => {
    if (offerStore.has(uri)) {
      return offerStore.get(uri)!;
    }

    // Create a new realistic offer for this URI
    const offer = createRealisticOffer({ uri });
    offerStore.set(uri, offer);
    return offer;
  };

  return {
    selectFrom: (table: string) => {
      if (table === 'offers') {
        return {
          select: (columns: string[] | ((eb: any) => any)) => ({
            where: (column: string, operator: string, value: any) => ({
              executeTakeFirst: async () => {
                if (column === 'uri') {
                  const offer = getOrCreateOffer(value);

                  // Return only the selected columns
                  if (Array.isArray(columns)) {
                    const result: any = {};
                    for (const col of columns) {
                      result[col] = offer[col as keyof Offers];
                    }
                    return result;
                  }

                  return offer;
                }
                return null;
              },
              limit: (count: number) => ({
                execute: async () => {
                  // Generate multiple offers for list queries
                  const offers = Array.from({ length: Math.min(count, 5) }, (_, i) => {
                    const uri = `${faker.helpers.arrayElement(NORWEGIAN_DEALERS)}:${faker.number.int({ min: 10000, max: 999999 })}`;
                    return getOrCreateOffer(uri);
                  });

                  // Return only selected columns
                  if (Array.isArray(columns)) {
                    return offers.map(offer => {
                      const result: any = {};
                      for (const col of columns) {
                        result[col] = offer[col as keyof Offers];
                      }
                      return result;
                    });
                  }

                  return offers;
                }
              })
            }),
            limit: (count: number) => ({
              execute: async () => {
                // Generate sample offers for health check etc.
                const offers = Array.from({ length: Math.min(count, 3) }, () => {
                  const uri = `${faker.helpers.arrayElement(NORWEGIAN_DEALERS)}:${faker.number.int({ min: 10000, max: 999999 })}`;
                  return getOrCreateOffer(uri);
                });

                // Return only selected columns
                if (Array.isArray(columns)) {
                  return offers.map(offer => {
                    const result: any = {};
                    for (const col of columns) {
                      result[col] = offer[col as keyof Offers];
                    }
                    return result;
                  });
                }

                return offers;
              }
            })
          })
        };
      }

      // For other tables, return empty results
      return {
        select: () => ({
          execute: async () => [],
          executeTakeFirst: async () => null,
          limit: () => ({
            execute: async () => []
          })
        })
      };
    },

    destroy: async () => {
      // Clean up the in-memory store
      offerStore.clear();
    }
  };
}