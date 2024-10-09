import {
  type FastifyReply,
  type FastifyRequest,
  type FastifyInstance,
  type FastifyPluginOptions,
} from "fastify";
import { Static, Type } from "@sinclair/typebox";
import { getPricingHandler, getPricingSchema } from "./prices";
import { getUri, convertDenormalizedProduct } from "./utils";
import {
  priceDifferencesHandler,
  priceDifferencesSchema,
} from "./price-differences";
import { searchRelationsHandler, searchRelationsSchema } from "./browse";
import { getSingleHandler, getSingleSchema } from "./single";
import { sql } from "kysely";

export const offerRoutes = async (
  server: FastifyInstance,
  options: FastifyPluginOptions,
) => {
  server.get("/:uri/pricing", getPricingSchema, (request, reply) =>
    getPricingHandler(request, reply, server),
  );

  server.get("/searchrelations", searchRelationsSchema, (request, reply) =>
    searchRelationsHandler(request, reply, server),
  );

  const extraRelationsSchema = {
    schema: {
      params: Type.Object({
        uri: Type.String(),
      }),
      querystring: Type.Object({
        market: Type.String(),
        productCollection: Type.String(),
        limit: Type.Integer(),
      }),

      response: {
        200: Type.Object({
          items: Type.Array(Type.Object({}, { additionalProperties: true })),
          /*meta: Type.Object(
            {
              count: Type.Integer(),
              page: Type.Integer(),
              pageSize: Type.Integer(),
              pageCount: Type.Integer(),
            },
            { additionalProperties: true },
          ),*/
        }),
        404: Type.Object({
          error: Type.String(),
        }),
      },
    },
  };
  const extraRelationsHandler = async (
    request: FastifyRequest<{
      Params: Static<typeof extraRelationsSchema.schema.params>;
      Querystring: Static<typeof extraRelationsSchema.schema.querystring>;
    }>,
    reply: FastifyReply,
  ): Promise<Static<(typeof extraRelationsSchema.schema.response)["200"]>> => {
    const uri = getUri(request.params.uri);

    const offer = await server.db
      .selectFrom("offers")
      .select(["title", "product_id"])
      .where("uri", "=", uri)
      .executeTakeFirst();

    if (!offer) {
      return reply.code(404).send({ error: "Not found" });
    }

    const sanitizedQuery = offer.title.replace(/[^\w\s]/g, " ");
    const tsQuery = sanitizedQuery.replace(/\s+/g, "|");

    const rank = sql<any>`tsvector_col @@ to_tsquery('simple', ${tsQuery})`.as(
      "rank",
    );
    const trigramSimilarity =
      sql<number>`similarity(trigram_col, ${sanitizedQuery})`.as("similarity");

    const products = await server.db
      .selectFrom("denormalized_products")
      .selectAll("denormalized_products")
      .select(rank)
      .select(trigramSimilarity)
      // Use | to OR the terms
      .where((eb) =>
        eb.or([
          sql<any>`(tsvector_col @@ to_tsquery('simple', ${tsQuery}) `,
          sql<any>`trigram_col % ${sanitizedQuery})`,
          //sql<any>`dealers.is_partner = true`,
          eb("denormalized_products.market", "=", request.query.market),
        ]),
      )
      .where("denormalized_products.market", "=", request.query.market) // Explicitly using "denormalized_products.market"
      .where("denormalized_products.product_id", "!=", offer.product_id) // Explicit reference here too
      .limit(Math.min(request.query.limit, 10))
      .orderBy("rank", "desc")
      .orderBy("similarity", "desc")
      .execute();

    const items = products.map((product) => {
      return convertDenormalizedProduct(product);
    });

    return reply.code(200).send({ items });
  };
  server.get(
    "/extrarelations/:uri",
    extraRelationsSchema,
    extraRelationsHandler,
  );

  server.get("/pricedifferences", priceDifferencesSchema, (request, reply) =>
    priceDifferencesHandler(request, reply, server),
  );

  server.get("/:uri", getSingleSchema, (request, reply) =>
    getSingleHandler(request, reply, server),
  );
};
