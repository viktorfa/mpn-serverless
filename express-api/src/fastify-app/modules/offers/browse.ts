import { FastifyReply, FastifyRequest, type FastifyInstance } from "fastify";
import { Static, Type } from "@sinclair/typebox";
import { Kysely, sql } from "kysely";
import {
  convertDenormalizedProduct,
  getCommaSeparatedAsList,
  getOfferContextFromSiteCollection,
  orderNullsLast,
} from "./utils";
import { DB } from "generated/kysely";

export const searchRelationsSchema = {
  schema: {
    querystring: Type.Object({
      market: Type.Optional(Type.String()),
      productCollection: Type.Optional(Type.String()),
      limit: Type.Integer(),
      page: Type.Integer(),
      sort: Type.Optional(Type.String()),
      dealers: Type.Optional(Type.String()),
      brands: Type.Optional(Type.String()),
      vendors: Type.Optional(Type.String()),
      categories: Type.Optional(Type.String()),
      query: Type.Optional(Type.String()),
      getMeta: Type.Optional(Type.Boolean()),
      getBuckets: Type.Optional(Type.Boolean()),
    }),

    response: {
      200: Type.Object({
        items: Type.Array(Type.Object({}, { additionalProperties: true })),
        meta: Type.Optional(
          Type.Object(
            {
              count: Type.Integer(),
              page: Type.Integer(),
              pageSize: Type.Integer(),
              pageCount: Type.Integer(),
              sort: Type.Optional(Type.String()),
            },
            { additionalProperties: true },
          ),
        ),
        facets: Type.Optional(
          Type.Object(
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
        ),
      }),
      404: Type.Object({
        error: Type.String(),
      }),
    },
  },
};

const getQueries = async ({
  db,
  limitToUse,
  market,
  context,
  page,
  dealerKeys,
  categoryKeys,
  brandKeys,
  vendorKeys,
  sortCol,
  sortDirection,
  query,
  getMeta = true,
  getBuckets = true,
}: {
  db: Kysely<DB>;
  limitToUse: number;
  market?: string;
  context?: string;
  page: number;
  dealerKeys: string[];
  categoryKeys: string[];
  brandKeys: string[];
  vendorKeys: string[];
  sortCol: string;
  sortDirection: "asc" | "desc";
  query?: string;
  getMeta?: boolean;
  getBuckets?: boolean;
}) => {
  let productsQuery = db
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
    .select((eb) =>
      eb
        .selectFrom("brands")
        .select(["brands.title"])
        .where("brands.market", "=", market)
        .whereRef("denormalized_products.brand_key", "=", "brands.key")
        .as("brand"),
    )
    .offset((page - 1) * limitToUse)
    // TODO Remove
    //.orderBy("denormalized_products.created_at", "desc")
    //.orderBy(
    //  sql<number>`(denormalized_products.nutrition->>'kcals')::numeric`,
    //  "desc",
    //)

    .limit(limitToUse);

  let aggregateQuery = db
    .selectFrom("denormalized_products")
    .select(sql<number>`count(*)`.as("count"));

  if ((market && !context) || query) {
    productsQuery = productsQuery.where(
      "denormalized_products.market",
      "=",
      market,
    );
    aggregateQuery = aggregateQuery.where(
      "denormalized_products.market",
      "=",
      market,
    );
  }
  if (context) {
    productsQuery = productsQuery.where(
      "denormalized_products.context",
      "=",
      context,
    );
    aggregateQuery = aggregateQuery.where(
      "denormalized_products.context",
      "=",
      context,
    );
  }
  if (dealerKeys.length > 0) {
    productsQuery = productsQuery.where(
      "denormalized_products.dealer_keys",
      "&&",
      sql<string[]>`${dealerKeys}`,
    );
    aggregateQuery = aggregateQuery.where(
      "denormalized_products.dealer_keys",
      "&&",
      sql<string[]>`${dealerKeys}`,
    );
  }
  if (brandKeys.length > 0) {
    productsQuery = productsQuery.where(
      "denormalized_products.brand_key",
      "in",
      brandKeys,
    );
    aggregateQuery = aggregateQuery.where(
      "denormalized_products.brand_key",
      "in",
      brandKeys,
    );
  }
  if (vendorKeys.length > 0) {
    productsQuery = productsQuery.where(
      "denormalized_products.vendor_key",
      "in",
      vendorKeys,
    );
    aggregateQuery = aggregateQuery.where(
      "denormalized_products.vendor_key",
      "in",
      vendorKeys,
    );
  }
  if (categoryKeys.length > 0) {
    productsQuery = productsQuery.where(
      "denormalized_products.category_keys",
      "&&",
      sql<string[]>`${categoryKeys}`,
    );
    aggregateQuery = aggregateQuery.where(
      "denormalized_products.category_keys",
      "&&",
      sql<string[]>`${categoryKeys}`,
    );
  }
  if (sortCol && (sortDirection === "asc" || sortDirection === "desc")) {
    if (sortCol === "priceMin") {
      productsQuery = productsQuery.orderBy(
        "denormalized_products.price_min",
        orderNullsLast(sortDirection),
      );
    }
    if (sortCol === "valueMin") {
      productsQuery = productsQuery.orderBy(
        "denormalized_products.value_min",
        orderNullsLast(sortDirection),
      );
    }
    if (sortCol === "pageviews") {
      productsQuery = productsQuery.orderBy(
        "denormalized_products.page_views",
        orderNullsLast(sortDirection),
      );
    }
  }
  if (query) {
    // Step 1: Sanitize the query to allow letters, numbers, and spaces, including international characters
    const sanitizedQuery = query.replace(/[^\p{L}\p{N}\s]/gu, " "); // \p{L} for any letter, \p{N} for any number

    // Step 2: Replace multiple spaces with a single space
    const singleSpacedQuery = sanitizedQuery.replace(/\s+/g, " ").trim();
    const maxWords = 6;
    const words = singleSpacedQuery.split(" ").slice(0, maxWords);
    const shortenedSingleSpacedQuery = words.join(" ");

    // Step 3: Replace spaces with the OR operator (|)
    //const tsQuery = singleSpacedQuery.replace(/\s+/g, "|");
    const tsQuery = shortenedSingleSpacedQuery;
    //await db.selectFrom(sql`set_limit(0.1)`).execute();

    const rank =
      sql<number>`ts_rank(tsvector_col, plainto_tsquery('simple', ${tsQuery}))`.as(
        "rank",
      );
    const trigramSimilarity =
      sql<number>`similarity(trigram_col, ${shortenedSingleSpacedQuery})`.as(
        "similarity",
      );

    productsQuery = productsQuery
      .select(rank)
      .select(trigramSimilarity)
      .where(
        sql<any>`(tsvector_col @@ plainto_tsquery('simple', ${tsQuery}) OR trigram_col % ${shortenedSingleSpacedQuery})`,
      )
      .orderBy("rank", "desc")
      .orderBy("similarity", "desc");

    aggregateQuery = aggregateQuery.where(
      sql<any>`(tsvector_col @@ plainto_tsquery('simple', ${tsQuery}) OR trigram_col % ${shortenedSingleSpacedQuery})`,
    );
  }

  //const _sql = productsQuery.compile().sql;
  //const parameters = productsQuery.compile().parameters;
  //console.log({ _sql, parameters });
  //const analyzed = await productsQuery.explain("text", sql`analyze`);
  //const analyzedAgg = await aggregateQuery.explain("text", sql`analyze`);
  //console.log({ analyzed, analyzedAgg });

  const bucketQuery = db
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
    .where("dp.context", "=", context)
    // Group by dealer key and dealer information
    .groupBy(["dk.dealer_key", "d.title", "d.market"])
    // Order by count descending
    .orderBy("count", "desc")
    // Limit to top 10
    .limit(10);

  const [products, aggregate, buckets] = await Promise.all([
    productsQuery.execute(),
    getMeta ? aggregateQuery.executeTakeFirst() : null,
    getBuckets ? bucketQuery.execute() : null,
  ]);

  return {
    products,
    aggregate,
    buckets,
  };
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
  const brandKeys = getCommaSeparatedAsList(request.query.brands);
  const vendorKeys = getCommaSeparatedAsList(request.query.vendors);

  const limitToUse = Math.min(request.query.limit, 16);

  const getMeta =
    typeof request.query.getMeta === "undefined" ? true : request.query.getMeta;
  const getBuckets =
    typeof request.query.getBuckets === "undefined"
      ? true
      : request.query.getBuckets;

  let [sortCol, sortDirection] = request.query.sort
    ? request.query.sort.split(":")
    : ["", ""];

  const context = request.query.productCollection
    ? getOfferContextFromSiteCollection(request.query.productCollection)
    : null;

  if (!request.query.market && request.query.query) {
    return reply
      .code(400)
      .send({ error: "Market is required when using text search" });
  }

  const { products, aggregate, buckets } = await getQueries({
    db: server.db,
    limitToUse,
    market: request.query.market,
    context,
    page: request.query.page,
    dealerKeys,
    categoryKeys,
    brandKeys,
    vendorKeys,
    sortCol,
    sortDirection: sortDirection as "asc" | "desc",
    query: request.query.query,
    getMeta,
    getBuckets,
  });

  const meta = getMeta
    ? {
        count: aggregate.count,
        page: request.query.page,
        pageSize: limitToUse,
        pageCount: Math.ceil(aggregate.count / limitToUse),
      }
    : null;

  const facets = getBuckets ? { dealersFacet: { buckets } } : null;

  const items = products.map((product) => {
    return {
      ...convertDenormalizedProduct(product),
    };
  });

  return reply.code(200).send({ items, meta, facets });
};
