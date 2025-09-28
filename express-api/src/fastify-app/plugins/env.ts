import fastifyEnv from "@fastify/env";
import { Type } from "@sinclair/typebox";

// Define the environment schema with validation
const envSchema = Type.Object({
  NODE_ENV: Type.Union(
    [
      Type.Literal("development"),
      Type.Literal("production"),
      Type.Literal("test"),
    ],
    { default: "development" },
  ),

  STAGE: Type.Optional(Type.String()),

  // Database configuration
  DATABASE_URL: Type.String({
    description: "PostgreSQL connection string",
  }),

  // Server configuration
  PORT: Type.Number({
    default: 3000,
    description: "Server port",
  }),

  HOST: Type.String({
    default: "0.0.0.0",
    description: "Server host",
  }),

  // Logging configuration
  LOG_LEVEL: Type.Union(
    [
      Type.Literal("fatal"),
      Type.Literal("error"),
      Type.Literal("warn"),
      Type.Literal("info"),
      Type.Literal("debug"),
      Type.Literal("trace"),
    ],
    { default: "info" },
  ),

  // OpenTelemetry configuration
  OTEL_EXPORTER_OTLP_ENDPOINT: Type.Optional(
    Type.String({
      description: "OTLP endpoint for traces",
    }),
  ),
  OTEL_SERVICE_NAME: Type.Optional(
    Type.String({
      description: "Service name for OpenTelemetry",
    }),
  ),
  OTEL_EXPORTER_OTLP_HEADERS: Type.Optional(
    Type.String({
      description: "Headers for OTLP authentication",
    }),
  ),
});

// Create the plugin options based on environment
const createEnvOptions = () => {
  const nodeEnv = process.env.NODE_ENV || "development";
  const stage = process.env.STAGE;

  // Priority: STAGE-specific env file, then NODE_ENV-specific
  let envFile = ".env";
  if (stage) {
    envFile = `.env.${stage}`;
  } else if (nodeEnv === "development") {
    envFile = ".env.local";
  } else {
    envFile = `.env.${nodeEnv}`;
  }

  return {
    schema: envSchema,
    dotenv: {
      path: envFile,
    },
  };
};

// Export the plugin registration function
export const registerEnv = (fastify: any) => {
  const nodeEnv = process.env.NODE_ENV || "development";
  const initialStage = process.env.STAGE;
  const options = createEnvOptions();

  return fastify.register(fastifyEnv, options).after(() => {
    // Log which environment configuration was loaded after the plugin registers
    const envFile = initialStage
      ? `.env.${initialStage}`
      : nodeEnv === "development"
      ? ".env.local"
      : `.env.${nodeEnv}`;
    fastify.log.info(
      `Environment loaded from ${envFile} (NODE_ENV: ${nodeEnv}, STAGE: ${
        fastify.config.STAGE || "not set"
      })`,
    );
  });
};

// TypeScript declaration for the environment config
declare module "fastify" {
  interface FastifyInstance {
    config: {
      NODE_ENV: "development" | "production" | "test";
      STAGE?: string;
      DATABASE_URL: string;
      PORT: number;
      HOST: string;
      LOG_LEVEL: "fatal" | "error" | "warn" | "info" | "debug" | "trace";
      OTEL_EXPORTER_OTLP_ENDPOINT?: string;
      OTEL_SERVICE_NAME?: string;
      OTEL_EXPORTER_OTLP_HEADERS?: string;
    };
  }
}
