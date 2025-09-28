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
  // Initialize the PostgreSQL pool using config from env plugin
  const pool = new Pool({
    connectionString: fastify.config.DATABASE_URL,
    max: fastify.config.NODE_ENV === 'test' ? 5 : 10, // Smaller pool for tests
    min: 0,
    idleTimeoutMillis: fastify.config.NODE_ENV === 'test' ? 5000 : 10000,
    allowExitOnIdle: true,
  });

  // Initialize Kysely with the Postgres dialect
  const kyselyDb = new Kysely<DB>({
    dialect: new PostgresDialect({
      pool: () => pool,
    }),
  });

  // Decorate Fastify instance with Kysely
  fastify.decorate("db", kyselyDb);

  // Handle graceful shutdown
  fastify.addHook("onClose", async (instance, done) => {
    await instance.db.destroy();
    done();
  });
}

// Export the plugin wrapped with fastify-plugin
export default fp(kyselyPlugin, {
  name: "kysely-plugin",
  dependencies: ["@fastify/env"],
});
