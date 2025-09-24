import { FastifyReply, FastifyRequest, type FastifyInstance } from "fastify";
import { Static, Type } from "@sinclair/typebox";
import { sql } from "kysely";
import { convertDenormalizedProduct, getUri } from "./utils";

export const extraRelationsSchema = {
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

export const extraRelationsHandler = async (
  request: FastifyRequest<{
    Params: Static<typeof extraRelationsSchema.schema.params>;
    Querystring: Static<typeof extraRelationsSchema.schema.querystring>;
  }>,
  reply: FastifyReply,
  server: FastifyInstance,
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

  // Step 1: Sanitize the query to allow letters, numbers, and spaces, including international characters
  const sanitizedQuery = offer.title.replace(/[^\p{L}\p{N}\s]/gu, " "); // \p{L} for any letter, \p{N} for any number

  const maxWords = 6;
  // Step 2: Replace multiple spaces with a single space
  const singleSpacedQuery = sanitizedQuery.replace(/\s+/g, " ");

  // Step 3: Split the sanitized query into an array of words
  const words = singleSpacedQuery.trim().split(" ").slice(0, maxWords);
  const shortenedSingleSpacedQuery = words.join(" ");

  // Step 4: Join the words with the OR operator (|) for to_tsquery format
  const tsQuery = words.join("|");

  //const rank = sql<any>`ts_rank(tsvector_col, 'simple', ${tsQuery})`.as("rank");
  const rank =
    sql<number>`ts_rank(tsvector_col, to_tsquery('simple', ${tsQuery}))`.as(
      "rank",
    );

  const trigramSimilarity =
    sql<number>`similarity(trigram_col, ${shortenedSingleSpacedQuery})`.as(
      "similarity",
    );

  const productsQuery = server.db
    .selectFrom("denormalized_products")
    .select([
      "denormalized_products.brand_key",
      "denormalized_products.quantity_amount",
      "denormalized_products.quantity_unit",
      "denormalized_products.image_url",
      "denormalized_products.value_min",
      "denormalized_products.value_max",
      "denormalized_products.price_min",
      "denormalized_products.price_max",
      "denormalized_products.nutrition",
      "denormalized_products.gtins",
      "denormalized_products.title",
      "denormalized_products.subtitle",
      "denormalized_products.description",
      "denormalized_products.short_description",
      "denormalized_products.valid_through",
      "denormalized_products.valid_through",
      "denormalized_products.offers",
    ])
    .where("denormalized_products.product_id", "!=", offer.product_id) // Explicit reference here too
    .where("denormalized_products.market", "=", request.query.market) // Explicitly using "denormalized_products.market"
    //.where(sql<any>`trigram_col % ${shortenedSingleSpacedQuery}`)
    //.where(sql<any>`tsvector_col @@ to_tsquery('simple', ${tsQuery})`)
    .select(rank)
    .select(trigramSimilarity)
    .where((eb) =>
      eb.or([
        sql<any>`tsvector_col @@ to_tsquery('simple', ${tsQuery})`,
        //sql<any>`trigram_col % ${shortenedSingleSpacedQuery}`,
        //sql<any>`dealers.is_partner = true`,
        //eb("denormalized_products.market", "=", request.query.market),
      ]),
    )
    //.orderBy("rank", "desc")
    //.orderBy("similarity", "desc")
    .limit(100);

  //const _sql = productsQuery.compile().sql;
  //const parameters = productsQuery.compile().parameters;
  //console.log({ _sql, parameters });
  //const analyzed = await productsQuery.explain("text", sql`analyze`);
  //console.log({ analyzed });

  const products = await productsQuery.execute();

  // It takes a long time to sort in the db as of now, so we just sort a subset
  products.sort((a, b) => {
    if (a.rank === b.rank) {
      return b.similarity - a.similarity;
    }
    return b.rank - a.rank;
  });

  const items = products
    .slice(0, Math.min(request.query.limit, 12))
    .map((product) => {
      return convertDenormalizedProduct(product);
    });

  return reply.code(200).send({ items });
};
