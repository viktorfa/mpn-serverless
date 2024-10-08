// src/types/fastify.d.ts

import { Kysely } from "kysely";
import type { DB } from "../../generated/kysely.d";
import { fastifyApp } from "./app";

type MyFastifyInstance = typeof fastifyApp;

declare module "fastify" {
  interface FastifyInstance {
    db: Kysely<DB>;
  }
}
