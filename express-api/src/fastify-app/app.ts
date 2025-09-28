import Fastify, { FastifyReply } from "fastify";
import fastifySwagger from "@fastify/swagger";
import fastifySwaggerUi from "@fastify/swagger-ui";
import { TypeBoxTypeProvider } from "@fastify/type-provider-typebox";
import { registerEnv } from "./plugins/env";
import kyselyPlugin from "./plugins/kysely";
import { offerRoutes } from "./modules/offers/routes";
import fastifyCors from "@fastify/cors";
import { categoryRoutes } from "./modules/categories/routes";
import { reviewRoutes } from "./modules/reviews/routes";
import { productRoutes } from "./modules/products/routes";

const fastifyApp = Fastify({
  logger: {
    level: "info", // Will be overridden by env config
  },
}).withTypeProvider<TypeBoxTypeProvider>();

// Register environment configuration first
registerEnv(fastifyApp);

// Register CORS plugin
fastifyApp.register(fastifyCors, {
  origin: true, // Allow all origins
  credentials: true,
  methods: ["GET", "POST", "PUT", "DELETE"],
  allowedHeaders: ["Content-Type", "Authorization"],
});

// Register Swagger (conditional based on environment)
fastifyApp.register(async function (fastify) {
  // Only register Swagger in development and test environments
  if (process.env.NODE_ENV !== "production") {
    await fastify.register(fastifySwagger, {
      openapi: {
        openapi: "3.0.0",
        info: {
          title: "Express API",
          description: "Price comparison API documentation",
          version: "1.0.0",
        },
        servers: [
          {
            url: `http://${fastify.config?.HOST || "localhost"}:${
              fastify.config?.PORT || 3000
            }`,
            description: `${
              fastify.config?.NODE_ENV || process.env.NODE_ENV
            } server`,
          },
        ],
      },
    });

    await fastify.register(fastifySwaggerUi, {
      routePrefix: "/docs",
      uiConfig: {
        docExpansion: "full",
        deepLinking: false,
      },
    });
  }
});

fastifyApp.register(kyselyPlugin);

fastifyApp.register(offerRoutes, { prefix: "/api/v1/offers" });
fastifyApp.register(categoryRoutes, { prefix: "/api/v1/categories" });
fastifyApp.register(reviewRoutes, { prefix: "/api/v1/reviews" });
fastifyApp.register(productRoutes, { prefix: "/api/v1/products" });

// Declare a route
fastifyApp.get("/", function (request, reply): FastifyReply {
  request.log.info(
    {
      event: "root_endpoint_access",
      userAgent: request.headers["user-agent"],
      remoteAddress: request.ip,
    },
    "Root endpoint accessed",
  );

  return reply.send({
    message: "Hello world from Express API",
    timestamp: new Date().toISOString(),
    version: "1.0.0",
  });
});
fastifyApp.get(
  "/healthz",
  async function (request, reply): Promise<FastifyReply> {
    const startTime = Date.now();

    try {
      // Log health check start
      request.log.info("Health check requested");

      // Example query to check if the DB is up
      const dbStartTime = Date.now();
      const result = await fastifyApp.db
        .selectFrom("offers")
        .select(["uri"])
        .limit(1)
        .execute();
      const dbDuration = Date.now() - dbStartTime;

      const healthData = {
        status: "ok",
        dbStatus: result.length > 0 ? "connected" : "no data",
        dbQueryDuration: dbDuration,
        timestamp: new Date().toISOString(),
      };

      // Log successful health check with metrics
      request.log.info(
        {
          event: "health_check_success",
          dbQueryDuration: dbDuration,
          totalDuration: Date.now() - startTime,
        },
        "Health check completed successfully",
      );

      return reply.send(healthData);
    } catch (error) {
      const errorDuration = Date.now() - startTime;

      // Log health check failure
      request.log.error(
        {
          event: "health_check_failure",
          error: error instanceof Error ? error.message : String(error),
          duration: errorDuration,
        },
        "Health check failed",
      );

      return reply.status(500).send({
        status: "error",
        message: String(error),
        timestamp: new Date().toISOString(),
      });
    }
  },
);

export { fastifyApp };
