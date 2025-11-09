import Fastify from "fastify";
import fastifySwagger from "@fastify/swagger";
import fastifySwaggerUi from "@fastify/swagger-ui";
import { TypeBoxTypeProvider } from "@fastify/type-provider-typebox";
import fastifyCors from "@fastify/cors";
import { offerRoutes } from "@_fastify/modules/offers/routes";
import { categoryRoutes } from "@_fastify/modules/categories/routes";
import { reviewRoutes } from "@_fastify/modules/reviews/routes";
import { productRoutes } from "@_fastify/modules/products/routes";
import { registerEnv } from "@_fastify/plugins/env";
import kyselyPlugin from "@_fastify/plugins/kysely";

import dotenv from "dotenv";
import path from "path";

// Load test environment variables
dotenv.config({ path: path.resolve(process.cwd(), ".env.test") });

export async function createIntegrationTestApp() {
  // Ensure we're in test mode for proper environment loading
  process.env.NODE_ENV = "test";
  process.env.STAGE = "test";

  // Create a fresh Fastify instance for integration tests
  const app = Fastify({
    logger: false, // Disable logging in tests unless debugging
  }).withTypeProvider<TypeBoxTypeProvider>();

  // Register environment configuration first
  await registerEnv(app);

  // Register CORS
  app.register(fastifyCors, {
    origin: true,
    credentials: true,
  });

  // Register Swagger (optional for tests, but keeps consistency)
  app.register(fastifySwagger, {
    openapi: {
      openapi: "3.0.0",
      info: {
        title: "Express API - Integration Tests",
        description: "Testing the Express API with real database",
        version: "0.1.0",
      },
    },
  });

  app.register(fastifySwaggerUi, {
    routePrefix: "/documentation",
    uiConfig: {
      docExpansion: "full",
      deepLinking: false,
    },
  });

  // Register the real Kysely plugin (connects to test database)
  await app.register(kyselyPlugin);

  // Register route modules
  app.register(offerRoutes, { prefix: "/api/v1/offers" });
  app.register(categoryRoutes, { prefix: "/api/v1/categories" });
  app.register(reviewRoutes, { prefix: "/api/v1/reviews" });
  app.register(productRoutes, { prefix: "/api/v1/products" });

  await app.ready();
  return app;
}
