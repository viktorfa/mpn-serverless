import { FastifyReply, FastifyRequest, type FastifyInstance } from "fastify";
import { Static, Type } from "@sinclair/typebox";
import { sql } from "kysely";
import { convertDenormalizedProduct, getCommaSeparatedAsList } from "./utils";
import { jsonObjectFrom } from "kysely/helpers/postgres";

export const searchRelationsSchema = {
  schema: {
    querystring: Type.Object({
      market: Type.String(),
      productCollection: Type.String(),
      limit: Type.Integer(),
      page: Type.Integer(),
      sort: Type.String(),
      dealers: Type.Optional(Type.String()),
      categories: Type.Optional(Type.String()),
      query: Type.Optional(Type.String()),
    }),

    response: {
      200: Type.Object({
        items: Type.Array(Type.Object({}, { additionalProperties: true })),
        meta: Type.Object(
          {
            count: Type.Integer(),
            page: Type.Integer(),
            pageSize: Type.Integer(),
            pageCount: Type.Integer(),
          },
          { additionalProperties: true },
        ),
        facets: Type.Object(
          {
            dealersFacet: Type.Object(
              {
                buckets: Type.Array(
                  Type.Object(
                    {
                      _id: Type.String(),
                      key: Type.String(),
                      market: Type.String(),
                      text: Type.String(),
                      count: Type.Integer(),
                    },
                    { additionalProperties: true },
                  ),
                ),
              },
              { additionalProperties: true },
            ),
          },
          { additionalProperties: true },
        ),
      }),
      404: Type.Object({
        error: Type.String(),
      }),
    },
  },
};

export const searchRelationsHandler = async (
  request: FastifyRequest<{
    Querystring: Static<typeof searchRelationsSchema.schema.querystring>;
  }>,
  reply: FastifyReply,
  server: FastifyInstance,
): Promise<Static<(typeof searchRelationsSchema.schema.response)["200"]>> => {
  const dealerKeys = getCommaSeparatedAsList(request.query.dealers);
  const categoryKeys = getCommaSeparatedAsList(request.query.categories);

  console.log({ dealerKeys, categoryKeys });

  const limitToUse = Math.min(request.query.limit, 10);

  let productsQuery = server.db
    .selectFrom("denormalized_products")
    .selectAll("denormalized_products")
    //.innerJoin("brands", "denormalized_products.brand_key", "brands.key")
    //.select("brands.title as brand")
    .select((eb) =>
      eb
        .selectFrom("brands")
        .select(["brands.title"])
        .where("market", "=", request.query.market)
        .whereRef("denormalized_products.brand_key", "=", "brands.key")
        .as("brand"),
    )
    .where("denormalized_products.market", "=", request.query.market)
    .offset((request.query.page - 1) * limitToUse)
    .limit(limitToUse);
  let aggregateQuery = server.db
    .selectFrom("denormalized_products")
    .select(sql<number>`count(*)`.as("count"))
    .where("market", "=", request.query.market);

  if (dealerKeys.length > 0) {
    productsQuery = productsQuery.where("dealer_keys", "in", dealerKeys);
    aggregateQuery = aggregateQuery.where("dealer_keys", "in", dealerKeys);
  }
  if (categoryKeys.length > 0) {
    productsQuery = productsQuery.where("category_key", "in", categoryKeys);
    aggregateQuery = aggregateQuery.where("category_key", "in", categoryKeys);
  }
  if (request.query.query) {
    const queryText = request.query.query;

    const rank =
      sql<number>`ts_rank(tsvector_col, plainto_tsquery('simple', ${queryText}))`.as(
        "rank",
      );

    productsQuery = productsQuery
      .select(rank)
      .where(sql<any>`tsvector_col @@ plainto_tsquery('simple', ${queryText})`)
      .orderBy("rank", "desc");

    aggregateQuery = aggregateQuery.where(
      sql<any>`tsvector_col @@ plainto_tsquery('simple', ${queryText})`,
    );
  }

  const [products, aggregateResult, dealerBuckets] = await Promise.all([
    productsQuery.execute(),
    aggregateQuery.executeTakeFirst(),
    server.db
      .selectFrom("denormalized_products as dp")
      // Lateral join to unnest 'dealer_keys'
      .innerJoinLateral(
        (eb) =>
          eb
            .selectFrom(
              // Unnest 'dp.dealer_keys' array
              sql`unnest(dp.dealer_keys)`.as("dealer_key"),
            )
            .select([sql<string>`dealer_key`.as("dealer_key")])
            .as("dk"), // Alias the subquery as 'dk'
        (join) => join.onTrue(), // No join condition needed
      )
      // Left join with 'dealers' table to get dealer information
      .leftJoin("dealers as d", (join) =>
        join
          .onRef("d.key", "=", "dk.dealer_key")
          .onRef("d.market", "=", "dp.market"),
      )
      // Select the required fields
      .select([
        "dk.dealer_key as _id",
        "dk.dealer_key as key",
        "d.title as text",
        "d.market",
        sql<number>`COUNT(*)`.as("count"),
      ])
      // Filter by market
      .where("dp.market", "=", request.query.market)
      // Group by dealer key and dealer information
      .groupBy(["dk.dealer_key", "d.title", "d.market"])
      // Order by count descending
      .orderBy("count", "desc")
      // Limit to top 10
      .limit(10)
      // Execute the query
      .execute(),
  ]);

  console.log({ dealerBuckets });

  const meta = {
    count: aggregateResult.count,
    page: request.query.page,
    pageSize: limitToUse,
    pageCount: Math.ceil(aggregateResult.count / limitToUse),
  };

  const facets = { dealersFacet: { buckets: dealerBuckets } };

  const items = products.map((product) => {
    return {
      ...convertDenormalizedProduct(product),
      score: product.rank,
    };
  });

  return reply.code(200).send({ items, meta, facets });
};
