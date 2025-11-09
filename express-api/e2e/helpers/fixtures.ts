// Test data fixtures for consistent testing across different test files

export const testOffers = {
  validOffer: {
    uri: 'rema:product:12345',
    title: 'Test Milk 1L',
    subtitle: 'Organic whole milk',
    href: 'https://rema.no/product/12345',
    ahref: 'https://affiliate.rema.no/product/12345',
    pricing: {
      price: 25.90,
      currency: 'NOK',
      priceUnit: 'kr'
    },
    dealerKey: 'rema1000',
    market: 'no',
    validThrough: new Date('2025-12-31').toISOString()
  },

  expiredOffer: {
    uri: 'coop:product:99999',
    title: 'Expired Product',
    pricing: { price: 10.00, currency: 'NOK' },
    validThrough: new Date('2020-01-01').toISOString()
  }
};

export const testCategories = [
  { key: 'dairy', name: 'Dairy Products', level: 1 },
  { key: 'bread', name: 'Bread & Bakery', level: 1 },
  { key: 'meat', name: 'Meat & Fish', level: 1 }
];

export const testProducts = [
  {
    id: 'product:12345',
    title: 'Test Product',
    description: 'A test product for e2e testing',
    price_min: 25.90,
    price_max: 35.90
  }
];

export const testReviews = [
  {
    uri: 'rema:product:12345',
    rating: 5,
    body: 'Great product!',
    author: 'test_user'
  }
];