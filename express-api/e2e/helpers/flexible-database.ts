import { faker } from '@faker-js/faker';
import type { Offers } from '../../generated/kysely';

// Test data store - allows test-specific overrides
interface TestDataStore {
  offers: Map<string, Partial<Offers>>;
  dealers: Map<string, any>;
  products: Map<string, any>;
  productMarketInfos: Map<string, any>;
  denormalizedProducts: Map<string, any>;
  ingredients: Map<string, any>;
  gtins: Map<string, string[]>;
}

// Norwegian grocery stores for realistic data
const NORWEGIAN_DEALERS = [
  { key: 'rema1000', title: 'REMA 1000', url: 'https://rema.no', logo_url: 'https://rema.no/logo.png' },
  { key: 'coop', title: 'Coop', url: 'https://coop.no', logo_url: 'https://coop.no/logo.png' },
  { key: 'ica', title: 'ICA', url: 'https://ica.no', logo_url: 'https://ica.no/logo.png' },
  { key: 'kiwi', title: 'KIWI', url: 'https://kiwi.no', logo_url: 'https://kiwi.no/logo.png' },
  { key: 'meny', title: 'Meny', url: 'https://meny.no', logo_url: 'https://meny.no/logo.png' }
];

const GROCERY_PRODUCTS = [
  { name: 'Milk', brands: ['Tine', 'Q-meieriene'], sizes: ['1L', '0.5L'] },
  { name: 'Bread', brands: ['Bakehuset', 'Brødservice'], sizes: ['500g', '750g'] },
  { name: 'Cheese', brands: ['Tine', 'Synnøve'], sizes: ['250g', '500g'] },
  { name: 'Yogurt', brands: ['Tine', 'Q-meieriene'], sizes: ['500g', '1kg'] }
];

export class FlexibleMockDatabase {
  private dataStore: TestDataStore;

  constructor() {
    this.dataStore = {
      offers: new Map(),
      dealers: new Map(),
      products: new Map(),
      productMarketInfos: new Map(),
      denormalizedProducts: new Map(),
      ingredients: new Map(),
      gtins: new Map()
    };
    this.seedBasicData();
  }

  // Seed some basic realistic data
  private seedBasicData() {
    // Seed dealers
    NORWEGIAN_DEALERS.forEach(dealer => {
      this.dataStore.dealers.set(dealer.key, {
        key: dealer.key,
        title: dealer.title,
        url: dealer.url,
        logo_url: dealer.logo_url,
        market: 'no',
        description: `${dealer.title} - Leading Norwegian grocery retailer`,
        is_partner: faker.datatype.boolean(0.8)
      });
    });

    // Seed some basic ingredients
    const ingredients = ['Water', 'Milk', 'Sugar', 'Salt', 'Wheat flour'];
    ingredients.forEach((ingredient, index) => {
      const id = `ingredient_${index + 1}`;
      this.dataStore.ingredients.set(id, {
        id,
        title: ingredient,
        short_description: `${ingredient} ingredient`,
        processed_value: faker.number.int({ min: 0, max: 10 })
      });
    });
  }

  // Public API: Seed specific test data
  seedOffer(uri: string, overrides: Partial<Offers> = {}) {
    this.dataStore.offers.set(uri, overrides);
    return this;
  }

  seedDealer(key: string, data: any) {
    this.dataStore.dealers.set(key, data);
    return this;
  }

  seedProduct(productId: string, data: any) {
    this.dataStore.products.set(productId, data);
    return this;
  }

  // Generate realistic offer with overrides
  private generateOffer(uri: string, overrides: Partial<Offers> = {}): Offers {
    const dealerKey = uri.split(':')[0] || faker.helpers.arrayElement(NORWEGIAN_DEALERS).key;
    const sku = uri.split(':')[1] || faker.number.int({ min: 10000, max: 999999 }).toString();

    const product = faker.helpers.arrayElement(GROCERY_PRODUCTS);
    const brand = faker.helpers.arrayElement(product.brands);
    const size = faker.helpers.arrayElement(product.sizes);
    const title = `${brand} ${product.name} ${size}`;

    const dealer = this.dataStore.dealers.get(dealerKey) || NORWEGIAN_DEALERS.find(d => d.key === dealerKey) || NORWEGIAN_DEALERS[0];
    const price = faker.number.float({ min: 15.90, max: 199.90, fractionDigits: 2 });

    return {
      uri,
      title,
      product_id: overrides.product_id || faker.string.uuid(),
      dealer_key: dealerKey,
      market: 'no',
      context: 'amp-no',
      href: `${dealer.url}/product/${sku}`,
      ahref: faker.datatype.boolean(0.7) ? `${dealer.url}/aff/product/${sku}` : null,
      price: price.toString() as any,
      pre_price: faker.datatype.boolean(0.3) ? (price + faker.number.float({ min: 5, max: 50 })).toFixed(2) as any : null,
      currency: 'NOK',
      brand,
      brand_key: brand.toLowerCase(),
      description: `Premium ${product.name.toLowerCase()} from ${brand}`,
      short_description: title,
      subtitle: `${size} - ${brand}`,
      image: faker.image.urlLoremFlickr({ category: 'food' }),
      mpn_stock: faker.helpers.arrayElement(['in_stock', 'low_stock', 'out_of_stock']),
      provenance: 'scraper',
      provenance_id: faker.string.uuid(),
      valid_from: faker.date.recent({ days: 7 }) as any,
      valid_through: faker.date.future({ years: 1 }) as any,
      created_at: faker.date.recent({ days: 7 }) as any,
      updated_at: faker.date.recent({ days: 1 }) as any,
      quantity_amount: faker.number.float({ min: 0.5, max: 2.0 }).toString() as any,
      quantity_unit: 'kg',
      value_amount: faker.number.float({ min: 25, max: 150 }).toString() as any,
      value_unit: 'NOK/kg',
      // Set other fields to null/default for simplicity
      quantity_standard_amount: null,
      value_standard_amount: null,
      price_unit: null,
      mpn: null,
      upc: null,
      item_condition: 'new',
      is_promotion_restricted: false,
      is_partner: true as any,
      vendor_key: dealerKey,
      mongo_id: null,
      scrape_batch_id: null,
      prices_migrated_at: null,
      difference_7_days_mean: null,
      difference_7_days_mean_percentage: null,
      difference_30_days_mean: null,
      difference_30_days_mean_percentage: null,
      difference_90_days_mean: null,
      difference_90_days_mean_percentage: null,
      difference_180_days_mean: null,
      difference_180_days_mean_percentage: null,
      difference_365_days_mean: null,
      difference_365_days_mean_percentage: null,
      ...overrides
    };
  }

  // Generate related data for an offer
  private generateRelatedData(offer: Offers) {
    const productId = offer.product_id;

    // Generate product
    if (!this.dataStore.products.has(productId)) {
      this.dataStore.products.set(productId, {
        id: productId,
        quantity_unit: offer.quantity_unit || 'kg',
        quantity_amount: offer.quantity_amount || '1.0',
        nutrition: {
          kcals: faker.number.int({ min: 50, max: 500 }),
          protein: faker.number.float({ min: 0, max: 30 }),
          fat: faker.number.float({ min: 0, max: 20 })
        }
      });
    }

    // Generate product market info
    const marketInfoKey = `${productId}_${offer.market}`;
    if (!this.dataStore.productMarketInfos.has(marketInfoKey)) {
      this.dataStore.productMarketInfos.set(marketInfoKey, {
        product_id: productId,
        market: offer.market,
        brand_key: offer.brand_key,
        vendor_key: offer.dealer_key,
        category_key: 'dairy',  // simplified
        context: offer.context
      });
    }

    // Generate denormalized product
    if (!this.dataStore.denormalizedProducts.has(productId)) {
      this.dataStore.denormalizedProducts.set(productId, {
        product_id: productId,
        market: offer.market,
        offers: [offer], // This offer plus maybe some others
        quantity_unit: offer.quantity_unit,
        quantity_amount: offer.quantity_amount
      });
    }

    // Generate some GTINs
    if (!this.dataStore.gtins.has(offer.uri)) {
      this.dataStore.gtins.set(offer.uri, [
        `ean:${faker.number.int({ min: 1000000000000, max: 9999999999999 })}`,
        `upc:${faker.number.int({ min: 100000000000, max: 999999999999 })}`
      ]);
    }
  }

  // Get or create offer with all related data
  private getCompleteOffer(uri: string): Offers {
    const overrides = this.dataStore.offers.get(uri) || {};
    const offer = this.generateOffer(uri, overrides);
    this.generateRelatedData(offer);
    return offer;
  }

  // Mock database interface with complete support for complex queries
  createMockDatabase() {
    return {
      selectFrom: (table: string) => {
        return {
          select: (columns: any) => {
            if (table === 'offers') {
              // Create a chainable select builder for offers
              const createSelectBuilder = (currentOffer?: any) => {
                const whereHandler = (column: string, operator: string, value: any) => ({
                  where: whereHandler, // Make where chainable
                  executeTakeFirst: async () => {
                    if (column === 'uri') {
                      const offer = this.getCompleteOffer(value);

                      // Handle all possible jsonArrayFrom selects
                      const result: any = { ...offer };

                      // Check if dealerObject is requested (across all select calls)
                      const allSelects = JSON.stringify(columns) + JSON.stringify(arguments);
                      if (allSelects.includes('dealerObject')) {
                        const dealer = this.dataStore.dealers.get(offer.dealer_key);
                        result.dealerObject = dealer ? [{
                          key: dealer.key,
                          title: dealer.title,
                          logo_url: dealer.logo_url,
                          url: dealer.url,
                          market: dealer.market
                        }] : [];
                      }

                      // Handle jsonArrayFrom for GTINs
                      if (allSelects.includes('dbGtins')) {
                        const gtins = this.dataStore.gtins.get(offer.uri) || [];
                        result.dbGtins = gtins.map(gtin => ({ gtin }));
                      }

                      return result;
                    }
                    return null;
                  }
                });

                return {
                  select: (moreColumns: any) => createSelectBuilder(currentOffer),
                  where: whereHandler
                };
              };

              return createSelectBuilder();
            }

            if (table === 'denormalized_products') {
              return {
                where: (column: string, operator: string, value: any) => ({
                  executeTakeFirst: async () => {
                    if (column === 'product_id') {
                      const denormProduct = this.dataStore.denormalizedProducts.get(value);
                      return denormProduct || null;
                    }
                    return this.dataStore.denormalizedProducts.get(value) || null;
                  }
                })
              };
            }

            if (table === 'product_market_infos') {
              return {
                select: (moreColumns: any) => ({
                  where: (column: string, operator: string, value: any) => ({
                    executeTakeFirst: async () => {
                      let info;
                      if (column === 'product_id') {
                        const key = `${value}_no`; // Default to 'no' market
                        info = this.dataStore.productMarketInfos.get(key);
                      } else {
                        info = this.dataStore.productMarketInfos.get(value);
                      }

                      if (info && JSON.stringify(moreColumns).includes('productObject')) {
                        const product = this.dataStore.products.get(info.product_id);
                        info.productObject = product;
                      }

                      if (info && JSON.stringify(moreColumns).includes('ingredients')) {
                        // Add some random ingredients with processed_value
                        const ingredientIds = Array.from(this.dataStore.ingredients.keys()).slice(0, 3);
                        info.ingredients = ingredientIds.map(id => {
                          const ingredient = this.dataStore.ingredients.get(id);
                          return {
                            ingredient_id: id,
                            title: ingredient.title,
                            short_description: ingredient.short_description,
                            processed_value: ingredient.processed_value
                          };
                        });
                      }

                      if (info && JSON.stringify(moreColumns).includes('brandObject')) {
                        info.brandObject = {
                          key: info.brand_key,
                          title: info.brand_key?.charAt(0).toUpperCase() + info.brand_key?.slice(1)
                        };
                      }

                      if (info && JSON.stringify(moreColumns).includes('vendorObject')) {
                        const dealer = this.dataStore.dealers.get(info.vendor_key);
                        info.vendorObject = dealer ? {
                          key: dealer.key,
                          title: dealer.title
                        } : null;
                      }

                      if (info && JSON.stringify(moreColumns).includes('categories')) {
                        info.categories = [
                          { key: 'dairy', title: 'Dairy Products' },
                          { key: 'fresh', title: 'Fresh Products' }
                        ];
                      }

                      return info || null;
                    }
                  })
                })
              };
            }

            // Add support for additional tables
            if (table === 'offer_prices') {
              return {
                select: () => ({
                  where: () => ({
                    orderBy: () => ({
                      executeTakeFirst: async () => null,
                      execute: async () => []
                    }),
                    execute: async () => []
                  })
                })
              };
            }

            if (table === 'products') {
              return {
                select: () => ({
                  where: () => ({ executeTakeFirst: async () => null }),
                  limit: () => ({ execute: async () => [] }),
                  execute: async () => []
                })
              };
            }

            if (table === 'brands') {
              return {
                select: () => ({
                  where: () => ({ executeTakeFirst: async () => null }),
                  execute: async () => []
                })
              };
            }

            if (table === 'vendors') {
              return {
                select: () => ({
                  where: () => ({ executeTakeFirst: async () => null }),
                  execute: async () => []
                })
              };
            }

            if (table === 'categories') {
              return {
                select: () => ({
                  where: () => ({ executeTakeFirst: async () => null }),
                  execute: async () => []
                })
              };
            }

            if (table === 'product_has_ingredient') {
              return {
                select: () => ({
                  where: () => ({
                    innerJoin: () => ({
                      distinctOn: () => ({ execute: async () => [] })
                    })
                  }),
                  execute: async () => []
                })
              };
            }

            if (table === 'offer_has_gtin') {
              return {
                select: () => ({
                  where: () => ({ execute: async () => [] })
                })
              };
            }

            // Handle complex queries for denormalized_products with joins
            if (table.includes('denormalized_products')) {
              return {
                select: () => ({
                  where: () => ({
                    execute: async () => [],
                    executeTakeFirst: async () => null
                  }),
                  innerJoin: () => ({
                    where: () => ({
                      offset: () => ({
                        limit: () => ({
                          execute: async () => []
                        })
                      }),
                      execute: async () => []
                    })
                  }),
                  offset: () => ({
                    limit: () => ({
                      execute: async () => []
                    })
                  }),
                  execute: async () => []
                })
              };
            }

            // Default empty results for other tables
            return {
              where: () => ({
                executeTakeFirst: async () => null,
                execute: async () => []
              }),
              limit: () => ({ execute: async () => [] }),
              execute: async () => []
            };
          }
        };
      },

      destroy: async () => {
        // Clear test data
        Object.values(this.dataStore).forEach(map => map.clear());
      }
    };
  }
}

// Export factory function
export function createFlexibleMockDatabase() {
  return new FlexibleMockDatabase();
}