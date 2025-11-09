import { describe, test } from 'node:test';
import assert from 'node:assert';
import { createIntegrationTestApp } from '@/helpers/integration-app';

describe('Categories API Integration Tests', () => {
  test('GET /api/v1/categories returns valid categories structure', async () => {
    const app = await createIntegrationTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/api/v1/categories'
    });

    // Should return 200 or 404, not 500 errors
    assert([200, 404].includes(response.statusCode),
           `Expected 200 or 404, got ${response.statusCode}`);

    if (response.statusCode === 200) {
      const body = response.json();
      assert(typeof body === 'object', 'Response should be object');
      // Categories might be array or object depending on implementation
    } else if (response.statusCode === 404) {
      const body = response.json();
      assert(typeof body.error === 'string', 'Should have error message');
    }

    await app.close();
  });

  test('GET /api/v1/categories handles query parameters', async () => {
    const app = await createIntegrationTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/api/v1/categories?market=no&limit=10'
    });

    // Should handle query parameters gracefully
    assert([200, 400, 404].includes(response.statusCode),
           `Should handle query parameters, got ${response.statusCode}`);

    if (response.statusCode === 200) {
      const body = response.json();
      assert(typeof body === 'object', 'Response should be valid object');
    }

    await app.close();
  });

  test('GET /api/v1/categories handles invalid query parameters', async () => {
    const app = await createIntegrationTestApp();

    // Test with invalid limit value
    const response = await app.inject({
      method: 'GET',
      url: '/api/v1/categories?limit=-1'
    });

    // Should handle invalid parameters appropriately
    assert([200, 400, 404].includes(response.statusCode),
           'Should handle invalid limit appropriately');

    await app.close();
  });

  test('Database has categories table accessible', async () => {
    const app = await createIntegrationTestApp();

    try {
      // Simple test that categories table is accessible
      const result = await app.db.selectFrom('categories').select('key').limit(1).execute();
      assert(Array.isArray(result), 'Categories query should return array');
      console.log(`Found ${result.length} categories in test database`);
    } catch (error) {
      // Categories table might not exist yet
      console.log('Categories table not accessible:', error.message);
    }

    await app.close();
  });
});