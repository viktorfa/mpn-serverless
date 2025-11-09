import { test, describe } from 'node:test';
import assert from 'node:assert';
import { createTestApp } from '@/helpers/test-app';

describe('Categories API endpoints', () => {
  test('GET /api/v1/categories returns categories data', async () => {
    const app = await createTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/api/v1/categories'
    });

    assert.strictEqual(response.statusCode, 200);

    await app.close();
  });

  test('Categories endpoint handles query parameters', async () => {
    const app = await createTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/api/v1/categories?market=no&productCollection=groceryoffers'
    });

    assert.strictEqual(response.statusCode, 200);

    await app.close();
  });
});