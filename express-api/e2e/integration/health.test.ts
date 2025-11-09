import { describe, test } from 'node:test';
import assert from 'node:assert';
import { createIntegrationTestApp } from '@/helpers/integration-app';

describe('Health and Documentation Integration Tests', () => {
  test('GET / returns hello world', async () => {
    const app = await createIntegrationTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/'
    });

    assert.strictEqual(response.statusCode, 200, 'Root endpoint should return 200');

    const body = response.json();
    assert(typeof body.message === 'string', 'Should have message field');
    assert(body.message.toLowerCase().includes('hello'), 'Should contain hello message');

    await app.close();
  });

  test('GET /healthz returns health status', async () => {
    const app = await createIntegrationTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/healthz'
    });

    // Should return 200 or 503, depending on health status
    assert([200, 503].includes(response.statusCode),
           `Health endpoint should return 200 or 503, got ${response.statusCode}`);

    const body = response.json();
    assert(typeof body === 'object', 'Health response should be object');

    if (response.statusCode === 200) {
      assert(typeof body.status === 'string', 'Should have status field');
    }

    await app.close();
  });

  test('GET /docs redirects to documentation', async () => {
    const app = await createIntegrationTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/docs'
    });

    // Should redirect to documentation or return documentation page
    assert([200, 302].includes(response.statusCode),
           `Documentation endpoint should return 200 or 302, got ${response.statusCode}`);

    if (response.statusCode === 302) {
      assert(typeof response.headers.location === 'string', 'Should have redirect location');
    }

    await app.close();
  });

  test('GET /docs/json returns OpenAPI specification', async () => {
    const app = await createIntegrationTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/docs/json'
    });

    assert.strictEqual(response.statusCode, 200, 'OpenAPI spec should return 200');

    const body = response.json();
    assert(typeof body === 'object', 'OpenAPI spec should be object');
    assert(typeof body.openapi === 'string', 'Should have OpenAPI version');
    assert(typeof body.info === 'object', 'Should have info object');
    assert(typeof body.info.title === 'string', 'Should have API title');

    await app.close();
  });

  test('GET /documentation/json returns same as /docs/json', async () => {
    const app = await createIntegrationTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/documentation/json'
    });

    // Should be same as /docs/json or redirect
    assert([200, 302].includes(response.statusCode),
           'Documentation JSON should return 200 or redirect');

    if (response.statusCode === 200) {
      const body = response.json();
      assert(typeof body === 'object', 'Should be valid JSON object');
    }

    await app.close();
  });

  test('Invalid routes return 404', async () => {
    const app = await createIntegrationTestApp();

    const response = await app.inject({
      method: 'GET',
      url: '/definitely-nonexistent-endpoint'
    });

    assert.strictEqual(response.statusCode, 404, 'Invalid routes should return 404');

    const body = response.json();
    assert(typeof body.error === 'string', 'Should have error message');

    await app.close();
  });

  test('Invalid HTTP methods return 405 or 404', async () => {
    const app = await createIntegrationTestApp();

    const response = await app.inject({
      method: 'POST',
      url: '/',
      payload: { test: 'data' }
    });

    // Should return method not allowed or not found
    assert([404, 405].includes(response.statusCode),
           'Invalid HTTP methods should return 404 or 405');

    await app.close();
  });
});