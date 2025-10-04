// src/fastify-app/plugins/kysely.ts
import { FastifyInstance, FastifyPluginOptions } from "fastify";
import fp from "fastify-plugin";
import pg from "pg";
const { Pool } = pg; // CJS default import interop
import { Kysely, PostgresDialect } from "kysely";
import type { DB } from "../../../generated/kysely.d";

// Fix pg types parsing for ESM
const types = pg.types;
types.setTypeParser(types.builtins.NUMERIC, function (val) {
  return Number.parseFloat(val);
});

async function kyselyPlugin(
  fastify: FastifyInstance,
  options: FastifyPluginOptions,
) {
  const pool = new Pool({
    // Initialize the PostgreSQL pool using config from env plugin
    connectionString: fastify.config.DATABASE_URL,
    max: fastify.config.NODE_ENV === "test" ? 5 : 20, // Increased from 10
    min: fastify.config.STAGE === "prod" ? 2 : 0, // Keep 2 warm connections
    idleTimeoutMillis: fastify.config.NODE_ENV === "test" ? 5000 : 30000, // Increased
    connectionTimeoutMillis: 5000, // Fail fast if no connection available
    statement_timeout: 10000, // 10s query timeout
    query_timeout: 10000, // Additional safety
    allowExitOnIdle: true,
  });

  pool.on("error", (err) => {
    fastify.log.error({ err }, "Unexpected pool error");
  });

  // Initialize Kysely with the Postgres dialect
  const kyselyDb = new Kysely<DB>({
    dialect: new PostgresDialect({
      pool: pool, // Direct reference, not a function
    }),
  });

  // Decorate Fastify instance with Kysely
  fastify.decorate("db", kyselyDb);

  // Handle graceful shutdown
  fastify.addHook("onClose", async () => {
    try {
      await fastify.db.destroy();
      await pool.end(); // Explicitly close pool
    } catch (err) {
      fastify.log.error({ err }, "Error closing database connections");
    }
  });
}

// Export the plugin wrapped with fastify-plugin
export default fp(kyselyPlugin, {
  name: "kysely-plugin",
  dependencies: ["@fastify/env"],
});
