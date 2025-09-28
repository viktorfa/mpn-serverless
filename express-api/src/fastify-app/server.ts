// Import the regular app (OpenTelemetry handled by plugin)
import { fastifyApp } from "./app";
import os from "os";

// Start the server using environment configuration
const start = async () => {
  try {
    // Debug logging for environment
    console.log("=== SERVER STARTUP DEBUG INFO ===");
    console.log("Process ENV variables:");
    console.log(`  NODE_ENV: ${process.env.NODE_ENV}`);
    console.log(`  STAGE: ${process.env.STAGE}`);
    console.log(
      `  DATABASE_URL: ${process.env.DATABASE_URL ? "[SET]" : "[NOT SET]"}`,
    );
    console.log(`  PORT: ${process.env.PORT}`);
    console.log(`  HOST: ${process.env.HOST}`);

    // Set standard OTEL headers for SDK auto-instrumentation

    console.log(
      `OTEL_EXPORTER_OTLP_HEADERS: ${
        process.env.OTEL_EXPORTER_OTLP_HEADERS ? "[SET]" : "[NOT SET]"
      }`,
    );

    console.log("Network interfaces:");
    const interfaces = os.networkInterfaces();
    Object.keys(interfaces).forEach((name) => {
      interfaces[name]?.forEach((iface) => {
        if (iface.family === "IPv4") {
          console.log(`  ${name}: ${iface.address}`);
        }
      });
    });
    console.log("=================================");

    // Wait for all plugins to be registered (including env plugin)
    await fastifyApp.ready();

    // Log configuration after env plugin loads
    console.log("=== FASTIFY CONFIG AFTER ENV PLUGIN ===");
    console.log(`  PORT: ${fastifyApp.config.PORT}`);
    console.log(`  HOST: ${fastifyApp.config.HOST}`);
    console.log(
      `  DATABASE_URL: ${
        fastifyApp.config.DATABASE_URL ? "[SET]" : "[NOT SET]"
      }`,
    );
    console.log(`  NODE_ENV: ${fastifyApp.config.NODE_ENV}`);
    console.log(`  STAGE: ${fastifyApp.config.STAGE || "not set"}`);
    console.log("=======================================");

    // Use configuration from the env plugin
    // Force host to 0.0.0.0 to listen on all interfaces in Docker
    const host = "0.0.0.0";
    const port = fastifyApp.config.PORT;

    console.log(`Attempting to listen on ${host}:${port}...`);

    const address = await fastifyApp.listen({
      port: port,
      host: host,
    });

    console.log("=== SERVER STARTED SUCCESSFULLY ===");
    fastifyApp.log.info(`Server is now listening on ${address}`);
    fastifyApp.log.info(`Environment: ${fastifyApp.config.NODE_ENV}`);
    fastifyApp.log.info(`Stage: ${fastifyApp.config.STAGE || "not set"}`);
    fastifyApp.log.info(
      `Database URL: ${
        fastifyApp.config.DATABASE_URL ? "[CONFIGURED]" : "[MISSING]"
      }`,
    );

    if (fastifyApp.config.OTEL_EXPORTER_OTLP_ENDPOINT) {
      fastifyApp.log.info(
        `OpenTelemetry enabled - endpoint: ${fastifyApp.config.OTEL_EXPORTER_OTLP_ENDPOINT}`,
      );
      fastifyApp.log.info(
        `OpenTelemetry service: ${fastifyApp.config.OTEL_SERVICE_NAME}`,
      );
      fastifyApp.log.info(
        `OpenTelemetry headers: ${
          fastifyApp.config.OTEL_EXPORTER_OTLP_HEADERS ? "[SET]" : "[NOT SET]"
        }`,
      );
    } else {
      fastifyApp.log.warn(
        "OpenTelemetry endpoint not configured - telemetry disabled",
      );
    }

    // Test database connection
    try {
      console.log("Testing database connection...");
      const result = await fastifyApp.db
        .selectFrom("offers")
        .select(["uri"])
        .limit(1)
        .execute();
      console.log(
        `Database connection successful! Found ${result.length} offer(s)`,
      );
    } catch (dbErr) {
      console.error("Database connection test FAILED:", dbErr);
      fastifyApp.log.error("Database connection test failed", dbErr);
    }
  } catch (err) {
    console.error("=== SERVER STARTUP FAILED ===");
    console.error(err);
    fastifyApp.log.error(err);
    process.exit(1);
  }
};

// Handle shutdown gracefully
const gracefulShutdown = async (signal: string) => {
  console.log(`Received ${signal}, shutting down gracefully...`);
  try {
    await fastifyApp.close();
    process.exit(0);
  } catch (err) {
    console.error("Error during shutdown:", err);
    process.exit(1);
  }
};

process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
process.on("SIGINT", () => gracefulShutdown("SIGINT"));

start();
