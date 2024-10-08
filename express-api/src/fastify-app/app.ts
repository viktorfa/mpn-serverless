import Fastify, { FastifyReply } from "fastify";
import fastifySwagger from "@fastify/swagger";
import fastifySwaggerUi from "@fastify/swagger-ui";
import { TypeBoxTypeProvider } from "@fastify/type-provider-typebox";
import kyselyPlugin from "@_fastify/plugins/kysely";
import { offerRoutes } from "@_fastify/modules/offers/routes";
import fastifyCors from "@fastify/cors"; // Import the CORS plugin
import { categoryRoutes } from "./modules/categories/routes";
import { reviewRoutes } from "./modules/reviews.routes";

const fastifyApp = Fastify({
  logger: true,
}).withTypeProvider<TypeBoxTypeProvider>();

// Register CORS plugin
fastifyApp.register(fastifyCors, {
  origin: true, // Allow all origins
  credentials: true,
  methods: ["GET", "POST", "PUT", "DELETE"],
  allowedHeaders: ["Content-Type", "Authorization"],
});

// Register Swagger (optional)
fastifyApp.register(fastifySwagger, {
  swagger: {
    info: {
      title: "My Fastify API",
      description: "API documentation for my Fastify project",
      version: "1.0.0",
    },
    host: "localhost:3000",
    schemes: ["http"],
    consumes: ["application/json"],
    produces: ["application/json"],
  },
});

fastifyApp.register(fastifySwaggerUi, {
  routePrefix: "/docs",
  uiConfig: {
    docExpansion: "full",
    deepLinking: false,
  },
});

fastifyApp.register(kyselyPlugin);

fastifyApp.register(offerRoutes, { prefix: "/api/v1/offers" });
fastifyApp.register(categoryRoutes, { prefix: "/api/v1/categories" });
fastifyApp.register(reviewRoutes, { prefix: "/api/v1/reviews" });

// Declare a route
fastifyApp.get("/", function (request, reply): FastifyReply {
  return reply.send({ hello: "world" });
});

export { fastifyApp };
