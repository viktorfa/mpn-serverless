// Simple database mock for testing
// This replaces the Kysely database instance with predictable mock responses

export function createMockDatabase() {
  return {
    // Mock for health check query: SELECT uri FROM offers LIMIT 1
    selectFrom: (table: string) => ({
      select: (columns: string[]) => ({
        limit: (count: number) => ({
          execute: async () => {
            // Return mock data based on the table being queried
            if (table === 'offers') {
              return [{ uri: 'test:product:12345' }];
            }
            return [];
          }
        }),
        where: (column: string, operator: string, value: any) => ({
          executeTakeFirst: async () => {
            // Mock for single offer queries
            if (table === 'offers' && column === 'uri') {
              return {
                uri: value,
                href: 'https://example.com/product',
                ahref: 'https://affiliate.example.com/product',
                title: 'Test Product',
                price: 99.99,
                currency: 'NOK'
              };
            }
            return null;
          },
          limit: (count: number) => ({
            execute: async () => {
              // Mock for filtered offer queries
              if (table === 'offers') {
                return [{
                  uri: value,
                  title: 'Test Product',
                  href: 'https://example.com/product',
                  price: 99.99
                }];
              }
              return [];
            }
          })
        })
      }),
      // Direct limit without select (for simple queries)
      limit: (count: number) => ({
        execute: async () => {
          if (table === 'offers') {
            return [{ uri: 'test:product:12345' }];
          }
          return [];
        }
      })
    }),

    // Mock for database connection close
    destroy: async () => {
      // No-op for mock
    }
  };
}

// Test data fixtures for consistent testing
export const fixtures = {
  validOffer: {
    uri: 'rema:product:12345',
    title: 'Test Milk 1L',
    href: 'https://rema.no/product/12345',
    ahref: 'https://affiliate.rema.no/product/12345',
    price: 25.90,
    currency: 'NOK',
    dealerKey: 'rema1000'
  },

  multipleOffers: [
    {
      uri: 'rema:product:12345',
      title: 'Test Milk 1L',
      price: 25.90
    },
    {
      uri: 'coop:product:67890',
      title: 'Test Bread 500g',
      price: 35.50
    }
  ],

  categories: [
    { key: 'dairy', name: 'Dairy Products' },
    { key: 'bread', name: 'Bread & Bakery' }
  ]
};