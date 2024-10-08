import {
  FastifyReply,
  FastifyRequest,
  type FastifyInstance,
  type FastifyPluginOptions,
} from "fastify";
import { Static, Type } from "@sinclair/typebox";
import { sql } from "kysely";
import { Categories } from "generated/kysely";
import { getPricingHandler, getPricingSchema } from "./prices";
import {
  getUri,
  getQuantity,
  getValue,
  convertDenormalizedProduct,
  convertDenormalizedOffer,
} from "./utils";
import {
  priceDifferencesHandler,
  priceDifferencesSchema,
} from "./price-differences";
import { searchRelationsHandler, searchRelationsSchema } from "./browse";

export const offerRoutes = async (
  server: FastifyInstance,
  options: FastifyPluginOptions,
) => {
  server.get("/:uri/pricing", getPricingSchema, (request, reply) =>
    getPricingHandler(request, reply, server),
  );

  const getSchema = {
    schema: {
      querystring: Type.Object({
        limit: Type.Optional(Type.Integer()),
        order_by: Type.Optional(Type.String()),
        market: Type.String(),
      }),
      response: {
        200: Type.Array(Type.Object({}, { additionalProperties: true })),
      },
    },
  };
  const getHandler = async (
    request: FastifyRequest<{
      Querystring: Static<typeof getSchema.schema.querystring>;
    }>,
    reply: FastifyReply,
  ): Promise<Static<(typeof getSchema.schema.response)["200"]>> => {
    console.log({ "server.db": server.db });

    console.log({ "request.query": request.query });

    const offers = await server.db
      .selectFrom("offers")
      .selectAll()
      .where("market", "=", request.query.market)
      .limit(10)
      .execute();

    return reply.code(200).send(offers);
  };
  server.get("/", getSchema, getHandler);

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
  ): Promise<Static<(typeof getSchema.schema.response)["200"]>> => {
    const uri = getUri(request.params.uri);

    const products = await server.db
      .selectFrom("denormalized_products")
      .selectAll()
      .where("market", "=", request.query.market)
      .limit(Math.min(request.query.limit, 10))
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

  const getSingleSchema = {
    schema: {
      params: Type.Object({
        uri: Type.String(),
      }),
      response: {
        200: Type.Object({
          offer: Type.Object({}, { additionalProperties: true }),
          identical: Type.Array(
            Type.Object({}, { additionalProperties: true }),
          ),
          interchangeable: Type.Array(
            Type.Object({}, { additionalProperties: true }),
          ),
        }),
        404: Type.Object({
          error: Type.String(),
        }),
      },
    },
  };

  const getSingleHandler = async (
    request: FastifyRequest<{
      Params: Static<typeof getSingleSchema.schema.params>;
    }>,
    reply: FastifyReply,
  ): Promise<Static<(typeof getSingleSchema.schema.response)["200"]>> => {
    console.log({ "server.db": server.db });

    const uri = getUri(request.params.uri);

    const offer = await server.db
      .selectFrom("offers")
      .selectAll()
      .where("uri", "=", uri)
      .executeTakeFirst();

    if (!offer) {
      return reply.code(404).send({ error: "Offer not found" });
    } else {
      let identical = [];
      const denormalizedProduct = await server.db
        .selectFrom("denormalized_products")
        .selectAll()
        .where("product_id", "=", offer.product_id)
        .where("market", "=", offer.market)
        .executeTakeFirst();

      if (denormalizedProduct) {
        identical = denormalizedProduct.offers
          .filter((o) => o.uri !== uri)
          .map((o) =>
            convertDenormalizedOffer({
              newOffer: o,
              product: denormalizedProduct,
            }),
          );
      }

      const marketInfo = await server.db
        .selectFrom("product_market_infos")
        .selectAll()
        .where("product_id", "=", offer.product_id)
        .where("market", "=", offer.market)
        .executeTakeFirst();
      const product = await server.db
        .selectFrom("products")
        .selectAll()
        .where("id", "=", offer.product_id)
        .executeTakeFirst();
      const { rows: categories } = await sql<Categories[]>`
      WITH RECURSIVE category_tree AS (
        SELECT *
        FROM categories
        WHERE key = ${marketInfo.category_key} AND context = ${marketInfo.context}
      
        UNION ALL
      
        SELECT c.*
        FROM categories c
        INNER JOIN category_tree ct
        ON c.key = ct.parent AND c.context = ct.context
      )
      SELECT * FROM category_tree
      `.execute(server.db);
      const ingredients = await server.db
        .selectFrom("product_has_ingredient")
        .selectAll()
        .where("product_id", "=", offer.product_id)
        .innerJoin("ingredients", "ingredient_id", "id")
        .execute();
      const dealer = await server.db
        .selectFrom("dealers")
        .selectAll()
        .where("key", "=", offer.dealer_key)
        .where("market", "=", offer.market)
        .executeTakeFirst();
      const vendor = await server.db
        .selectFrom("vendors")
        .selectAll()
        .where("key", "=", marketInfo.vendor_key)
        .where("market", "=", offer.market)
        .executeTakeFirst();
      const brand = await server.db
        .selectFrom("brands")
        .selectAll()
        .where("key", "=", marketInfo.brand_key)
        .where("market", "=", offer.market)
        .executeTakeFirst();
      const dbGtins = await server.db
        .selectFrom("offer_has_gtin")
        .select(["gtin"])
        .where("offer_uri", "=", uri)
        .execute();

      const quantity = getQuantity({
        unit: product.quantity_unit,
        amount: parseFloat(product.quantity_amount),
      });
      let pricePerQuantity: number;
      try {
        pricePerQuantity =
          parseFloat(offer.price) / quantity?.size.standard.min;
      } catch (e) {
        console.warn("Error parsing price per quantity");
        console.warn(e);
        pricePerQuantity = 0;
      }

      const [namespace, sku] = offer.uri.split(":");
      const legacyUri = `${namespace}:product:${sku}`;

      const gtins: Record<string, string> = {};
      dbGtins.forEach((dbGtin) => {
        const [gtinType, gtin] = dbGtin.gtin.split(":");
        if (!gtinType.startsWith("_")) {
          gtins[gtinType] = gtin;
        }
      });

      const formattedOffer = {
        gtins,
        denormalizedProduct,
        uri: legacyUri,
        dealer: dealer?.title,
        dealerKey: offer.dealer_key,
        dealerObject: dealer,
        brand: brand?.title,
        brandKey: marketInfo.brand_key,
        brandObject: brand,
        vendor: vendor?.title,
        vendorKey: marketInfo.vendor_key,
        vendorObject: vendor,
        href: offer.href,
        imageUrl: offer.image,
        mpnStock: offer.mpn_stock,
        pricing: {
          price: offer.price,
          currency: offer.currency,
          prePrice: offer.pre_price,
          priceUnit: offer.price_unit,
        },
        provenance: offer.provenance,
        quantity: getQuantity({
          unit: product.quantity_unit,
          amount: parseFloat(product.quantity_amount),
        }),
        subtitle: offer.subtitle,
        title: offer.title,
        validFrom: offer.valid_from,
        validThrough: offer.valid_through,
        value: getValue({
          unit: product.quantity_unit,
          amount: pricePerQuantity,
        }),
        description: offer.description,
        market: offer.market,
        ahref: offer.ahref,
        mpnIngredients: {
          ingredients: ingredients.reduce((acc, curr) => {
            return {
              ...acc,
              [curr.id]: {
                key: curr.id,
                name: curr.title,
                shortDescription: curr.short_description,
              },
            };
          }, {}),
          processedScore: ingredients.reduce((acc, curr) => {
            return acc + curr.processed_value;
          }, 0),
        },
        mpnNutrition: Object.entries(product.nutrition).reduce(
          (acc, curr) => ({
            ...acc,
            [curr[0]]: {
              key: curr[0],
              name: curr[0],
              value: curr[1],
            },
          }),
          {},
        ),
        mpnProperties: {},
        mpnCategories: categories.map((cat) => ({
          ...cat,
          text: cat.title,
          name: cat.title,
        })),
      };

      return reply.code(200).send({
        offer: formattedOffer,
        identical,
        interchangeable: [],
      });
    }
  };

  server.get("/:uri", getSingleSchema, getSingleHandler);
};
