import Fastify from "fastify";
import fastifySwagger from "@fastify/swagger";
import fastifySwaggerUi from "@fastify/swagger-ui";
import { TypeBoxTypeProvider } from "@fastify/type-provider-typebox";
import fastifyCors from "@fastify/cors";
import { offerRoutes } from "@_fastify/modules/offers/routes";
import { categoryRoutes } from "@_fastify/modules/categories/routes";
import { reviewRoutes } from "@_fastify/modules/reviews/routes";
import { productRoutes } from "@_fastify/modules/products/routes";
import { createFlexibleMockDatabase, FlexibleMockDatabase } from './flexible-database';

declare module 'fastify' {
  interface FastifyInstance {
    mockDb: FlexibleMockDatabase;
  }
}

export async function createTestApp() {
  // Create a fresh Fastify instance for each test
  const app = Fastify({
    logger: false, // Disable logging in tests
  }).withTypeProvider<TypeBoxTypeProvider>();

  // Register CORS plugin
  app.register(fastifyCors, {
    origin: true,
    credentials: true,
    methods: ["GET", "POST", "PUT", "DELETE"],
    allowedHeaders: ["Content-Type", "Authorization"],
  });

  // Register Swagger (optional for tests, but keeps it consistent)
  app.register(fastifySwagger, {
    swagger: {
      info: {
        title: "Test API",
        description: "API for testing",
        version: "1.0.0",
      },
      host: "localhost:3000",
      schemes: ["http"],
      consumes: ["application/json"],
      produces: ["application/json"],
    },
  });

  app.register(fastifySwaggerUi, {
    routePrefix: "/docs",
    uiConfig: {
      docExpansion: "full",
      deepLinking: false,
    },
  });

  // Add the flexible mock database that supports test customization
  const mockDb = createFlexibleMockDatabase();
  app.decorate('db', mockDb.createMockDatabase());
  app.decorate('mockDb', mockDb); // Give access to the mock for test customization

  // Register route modules
  app.register(offerRoutes, { prefix: "/api/v1/offers" });
  app.register(categoryRoutes, { prefix: "/api/v1/categories" });
  app.register(reviewRoutes, { prefix: "/api/v1/reviews" });
  app.register(productRoutes, { prefix: "/api/v1/products" });

  // Register basic routes
  app.get("/", function (request, reply) {
    return reply.send({ hello: "world" });
  });

  app.get("/healthz", async function (request, reply) {
    try {
      const result = await app.db
        .selectFrom("offers")
        .select(["uri"])
        .limit(1)
        .execute();

      return reply.send({
        status: "ok",
        dbStatus: result.length > 0 ? "connected" : "no data",
      });
    } catch (error) {
      return reply
        .status(500)
        .send({ status: "error", message: error.message });
    }
  });

  // Wait for the app to be ready
  await app.ready();

  return app;
}