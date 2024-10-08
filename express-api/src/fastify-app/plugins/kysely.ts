// src/fastify-app/plugins/kysely.ts
import { FastifyInstance, FastifyPluginOptions } from "fastify";
import fp from "fastify-plugin";
import { Pool } from "pg";
import { Kysely, PostgresDialect } from "kysely";
import type { DB } from "../../../generated/kysely.d";
var types = require("pg").types;

var types = require("pg").types;
types.setTypeParser(types.builtins.NUMERIC, function (val) {
  return Number.parseFloat(val);
});

async function kyselyPlugin(
  fastify: FastifyInstance,
  options: FastifyPluginOptions,
) {
  // Initialize the PostgreSQL pool
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    max: 10,
    min: 0,
    idleTimeoutMillis: 10000,
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
});
