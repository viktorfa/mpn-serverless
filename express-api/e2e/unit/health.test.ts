import { test, describe } from 'node:test';
import assert from 'node:assert';
import { createTestApp } from '@/helpers/test-app';

describe('Health endpoints', () => {
  test('GET / returns hello world', async () => {
    const app = await createTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/'
    });

    assert.strictEqual(response.statusCode, 200);
    assert.deepStrictEqual(response.json(), { hello: 'world' });

    await app.close();
  });

  test('GET /healthz returns ok status with mock database', async () => {
    const app = await createTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/healthz'
    });

    assert.strictEqual(response.statusCode, 200);
    const body = response.json();
    assert.strictEqual(body.status, 'ok');
    assert.strictEqual(body.dbStatus, 'connected');

    await app.close();
  });

  test('GET /docs returns Swagger UI', async () => {
    const app = await createTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/docs'
    });

    // Swagger UI returns HTML content
    assert.strictEqual(response.statusCode, 200);
    assert(response.headers['content-type'].includes('text/html'));

    await app.close();
  });

  test('GET /docs/json returns OpenAPI spec', async () => {
    const app = await createTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/docs/json'
    });

    assert.strictEqual(response.statusCode, 200);
    const spec = response.json();
    assert.strictEqual(spec.swagger, '2.0');
    assert.strictEqual(spec.info.title, 'My Fastify API');

    await app.close();
  });
});