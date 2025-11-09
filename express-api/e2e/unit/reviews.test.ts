import { test, describe } from 'node:test';
import assert from 'node:assert';
import { createTestApp } from '@/helpers/test-app';

describe('Reviews API endpoints', () => {
  test('GET /api/v1/reviews returns reviews data', async () => {
    const app = await createTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/api/v1/reviews'
    });

    assert.strictEqual(response.statusCode, 200);

    await app.close();
  });

  test('Reviews endpoint handles filtering parameters', async () => {
    const app = await createTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/api/v1/reviews?rating=5&limit=10'
    });

    assert.strictEqual(response.statusCode, 200);

    await app.close();
  });
});