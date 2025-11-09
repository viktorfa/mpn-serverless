import { test, describe } from 'node:test';
import assert from 'node:assert';
import { createTestApp } from '@/helpers/test-app';

describe('Products API endpoints', () => {
  test('GET /api/v1/products returns products data', async () => {
    const app = await createTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/api/v1/products'
    });

    assert.strictEqual(response.statusCode, 200);

    await app.close();
  });

  test('Products endpoint handles search parameters', async () => {
    const app = await createTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/api/v1/products?query=milk&market=no'
    });

    assert.strictEqual(response.statusCode, 200);

    await app.close();
  });
});