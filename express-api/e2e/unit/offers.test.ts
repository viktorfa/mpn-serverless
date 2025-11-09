import { test, describe } from 'node:test';
import assert from 'node:assert';
import { createTestApp } from '@/helpers/test-app';

describe('Offers API endpoints', () => {
  test('GET /api/v1/offers/:uri/redirect returns offer redirect data', async () => {
    const app = await createTestApp();
    const testUri = 'rema1000:12345';

    const response = await app.inject({
      method: 'GET',
      url: `/api/v1/offers/${testUri}/redirect`
    });

    assert.strictEqual(response.statusCode, 200);
    const body = response.json();

    // Verify the response structure matches our schema
    assert(typeof body.href === 'string');
    assert(typeof body.title === 'string');

    // Verify we get realistic Norwegian store URLs
    assert(body.href.startsWith('https://'), `Expected https URL, got: ${body.href}`);

    // Check for any of the Norwegian store domains
    const norwegianStores = ['rema.no', 'coop.no', 'ica.no', 'kiwi.no', 'meny.no', 'joker.no', 'narvesen.no', 'store.no'];
    const hasNorwegianStore = norwegianStores.some(store => body.href.includes(store));
    assert(hasNorwegianStore, `Expected Norwegian store URL (${norwegianStores.join(', ')}), got: ${body.href}`);

    // Verify realistic product title (should contain brand and product info)
    assert(body.title.length > 5, `Title too short: ${body.title}`);
    assert(/^[A-Za-z0-9\s]+/.test(body.title), `Title should contain realistic product name: ${body.title}`);

    // Optional ahref should be string or null
    if (body.ahref !== undefined) {
      assert(body.ahref === null || typeof body.ahref === 'string');
      if (body.ahref) {
        assert(body.ahref.startsWith('https://'));
      }
    }

    await app.close();
  });

  test('GET /api/v1/offers/nonexistent/redirect returns 404', async () => {
    const app = await createTestApp();

    // Mock the database to return null for this specific query
    app.db.selectFrom = () => ({
      select: () => ({
        where: () => ({
          executeTakeFirst: async () => null
        })
      })
    });

    const response = await app.inject({
      method: 'GET',
      url: '/api/v1/offers/nonexistent:999/redirect'
    });

    assert.strictEqual(response.statusCode, 404);
    const body = response.json();
    assert.strictEqual(body.error, 'Not found');

    await app.close();
  });

  test('GET /api/v1/offers/:uri returns single offer data', async () => {
    const app = await createTestApp();
    const testUri = 'rema:12345';

    const response = await app.inject({
      method: 'GET',
      url: `/api/v1/offers/${testUri}?market=no`
    });

    // Debug output
    if (response.statusCode !== 200) {
      console.log('Error response body:', response.body);
    }

    // This should return offer data based on the mock
    assert.strictEqual(response.statusCode, 200);

    // The exact response will depend on your getSingleHandler implementation
    // For now, we're just testing that the endpoint is reachable

    await app.close();
  });

  test('GET /api/v1/offers/:uri/pricing returns pricing history', async () => {
    const app = await createTestApp();
    const testUri = 'rema:12345';

    const response = await app.inject({
      method: 'GET',
      url: `/api/v1/offers/${testUri}/pricing`
    });

    // This endpoint should return pricing data
    assert.strictEqual(response.statusCode, 200);

    await app.close();
  });

  test('GET /api/v1/offers/searchrelations returns search results', async () => {
    const app = await createTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/api/v1/offers/searchrelations?query=milk&market=no&limit=5&page=1'
    });

    // Test that the search endpoint is accessible
    assert.strictEqual(response.statusCode, 200);

    await app.close();
  });

  test('GET /api/v1/offers/pricedifferences returns price difference data', async () => {
    const app = await createTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/api/v1/offers/pricedifferences?market=no&productCollection=groceryoffers'
    });

    // Test that the price differences endpoint is accessible
    assert.strictEqual(response.statusCode, 200);

    await app.close();
  });

  test('GET /api/v1/offers/extrarelations/:uri returns extra relations', async () => {
    const app = await createTestApp();
    const testUri = 'rema:12345';

    const response = await app.inject({
      method: 'GET',
      url: `/api/v1/offers/extrarelations/${testUri}?market=no&limit=5`
    });

    // Test that the extra relations endpoint is accessible
    assert.strictEqual(response.statusCode, 200);

    await app.close();
  });

  test('GET /api/v1/offers/:uri returns complete single offer with customized data', async () => {
    const app = await createTestApp();
    const testUri = 'rema1000:98765';

    // Customize specific test data while letting other fields be generated realistically
    app.mockDb
      .seedOffer(testUri, {
        title: 'Tine Melk 1L - Test Customized',
        price: '25.90' as any,
        pre_price: '29.90' as any,
        brand: 'Tine',
        brand_key: 'tine'
      })
      .seedDealer('rema1000', {
        key: 'rema1000',
        title: 'REMA 1000',
        url: 'https://rema.no',
        logo_url: 'https://rema.no/logo.png',
        market: 'no'
      });

    const response = await app.inject({
      method: 'GET',
      url: `/api/v1/offers/${testUri}?market=no`
    });

    assert.strictEqual(response.statusCode, 200);
    const body = response.json();

    // Verify response structure
    assert(body.offer, 'Response should have offer object');
    assert(Array.isArray(body.identical), 'Response should have identical array');
    assert(Array.isArray(body.interchangeable), 'Response should have interchangeable array');

    // Verify our customized data is present
    assert.strictEqual(body.offer.title, 'Tine Melk 1L - Test Customized', 'Custom title should be preserved');
    assert.strictEqual(body.offer.pricing.price, '25.90', 'Custom price should be preserved');
    assert.strictEqual(body.offer.pricing.prePrice, '29.90', 'Custom pre-price should be preserved');
    assert.strictEqual(body.offer.brand, 'Tine', 'Custom brand should be preserved');
    assert.strictEqual(body.offer.brandKey, 'tine', 'Custom brand key should be preserved');

    // Verify dealer info is present and correct
    assert(body.offer.dealerObject, 'Dealer object should be present');
    assert.strictEqual(body.offer.dealerObject.title, 'REMA 1000', 'Dealer title should match');
    assert.strictEqual(body.offer.dealerObject.key, 'rema1000', 'Dealer key should match');

    // Verify realistic generated data is present where not customized
    assert(typeof body.offer.description === 'string', 'Description should be generated');
    assert(body.offer.description.length > 10, 'Description should be realistic length');

    // Verify Norwegian context
    assert(body.offer.href.includes('rema.no'), 'Should use Norwegian store URL');
    assert.strictEqual(body.offer.market, 'no', 'Market should be Norwegian');

    // Verify complex data structures are present
    assert(body.offer.quantity, 'Quantity info should be present');
    assert(body.offer.value, 'Value info should be present');
    assert(body.offer.mpnIngredients, 'Ingredients should be present');
    assert(body.offer.mpnNutrition, 'Nutrition should be present');
    assert(Array.isArray(body.offer.mpnCategories), 'Categories should be present');

    // Verify ingredients have realistic structure
    const ingredients = body.offer.mpnIngredients.ingredients;
    assert(typeof ingredients === 'object', 'Ingredients should be object');
    const ingredientKeys = Object.keys(ingredients);
    if (ingredientKeys.length > 0) {
      const firstIngredient = ingredients[ingredientKeys[0]];
      assert(typeof firstIngredient.name === 'string', 'Ingredient should have name');
      assert(typeof firstIngredient.shortDescription === 'string', 'Ingredient should have description');
    }

    // Verify nutrition has realistic structure
    const nutrition = body.offer.mpnNutrition;
    assert(typeof nutrition === 'object', 'Nutrition should be object');
    if (nutrition.kcals) {
      assert(typeof nutrition.kcals.value === 'number', 'Nutrition values should be numbers');
      assert(typeof nutrition.kcals.name === 'string', 'Nutrition should have names');
    }

    // Verify legacy URI format transformation
    assert(body.offer.uri.includes(':product:'), 'Should transform to legacy URI format');

    // Verify pricing calculations work
    assert(typeof body.offer.pricing.price === 'string', 'Price should be string');
    assert(!isNaN(parseFloat(body.offer.pricing.price)), 'Price should be parseable number');

    await app.close();
  });

  test('GET /api/v1/offers/:uri returns 404 for non-existent offer', async () => {
    const app = await createTestApp();

    // Use the mockDb to ensure this specific URI returns null
    // (Don't seed this URI, so it will return null by default)

    const response = await app.inject({
      method: 'GET',
      url: '/api/v1/offers/definitely-nonexistent:999?market=no'
    });

    assert.strictEqual(response.statusCode, 404);
    const body = response.json();
    assert.strictEqual(body.error, 'Offer not found');

    await app.close();
  });
});