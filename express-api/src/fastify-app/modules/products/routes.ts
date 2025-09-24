import {
  type FastifyReply,
  type FastifyRequest,
  type FastifyInstance,
  type FastifyPluginOptions,
} from "fastify";
import { Static, Type } from "@sinclair/typebox";
import { jsonArrayFrom, jsonObjectFrom } from "kysely/helpers/postgres";
import { getLegacyUri, getSIUnit } from "../offers/utils";

export const productRoutes = async (
  server: FastifyInstance,
  options: FastifyPluginOptions,
) => {
  const getSingleSchema = {
    schema: {
      params: Type.Object({
        productId: Type.String(),
      }),
      querystring: Type.Object({
        market: Type.Optional(Type.String()),
      }),
      response: {
        200: Type.Object({
          product: Type.Object({}, { additionalProperties: true }),
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
      Querystring: Static<typeof getSingleSchema.schema.querystring>;
    }>,
    reply: FastifyReply,
  ): Promise<Static<(typeof getSingleSchema.schema.response)["200"]>> => {
    const productResponse = await server.db
      .selectFrom("products")
      .select(["products.id"])
      .select((eb) => [
        jsonArrayFrom(
          eb
            .selectFrom("offers")
            .select(["offers.product_id", "offers.uri", "offers.price"])
            .whereRef("products.id", "=", "offers.product_id"),
        ).as("offers"),
      ])
      .select((eb) => [
        jsonArrayFrom(
          eb
            .selectFrom("product_market_infos")
            .select([
              "product_market_infos.product_id",
              "product_market_infos.category_keys",
              "product_market_infos.title",
            ])
            .whereRef("products.id", "=", "product_market_infos.product_id"),
        ).as("product_market_infos"),
      ])
      .select((eb) => [
        jsonArrayFrom(
          eb
            .selectFrom("gtins")
            .select(["gtins.gtin"])
            .whereRef("products.id", "=", "gtins.product_id"),
        ).as("gtins"),
      ])
      .select((eb) => [
        jsonArrayFrom(
          eb
            .selectFrom("product_has_ingredient")
            .select([
              "product_has_ingredient.ingredient_id",
              "ingredients.title",
              "ingredients.short_description",
            ])
            .whereRef("products.id", "=", "product_has_ingredient.product_id")
            .innerJoin(
              "ingredients",
              "product_has_ingredient.ingredient_id",
              "ingredients.id",
            ),
        ).as("ingredients"),
      ])
      .where("id", "=", request.params.productId)
      .executeTakeFirst();

    if (!productResponse) {
      return reply.status(404).send({ error: "Product not found" });
    }

    return reply.status(200).send({ product: productResponse });
  };

  server.get("/:productId", getSingleSchema, getSingleHandler);

  const getByGtinSchema = {
    schema: {
      querystring: Type.Object({
        market: Type.Optional(Type.String()),
        gtin: Type.String(),
      }),
      response: {
        200: Type.Object({
          product: Type.Object({}, { additionalProperties: true }),
        }),
        404: Type.Object({
          error: Type.String(),
        }),
      },
    },
  };

  const getByGtinHandler = async (
    request: FastifyRequest<{
      Querystring: Static<typeof getByGtinSchema.schema.querystring>;
    }>,
    reply: FastifyReply,
  ): Promise<Static<(typeof getByGtinSchema.schema.response)["200"]>> => {
    const gtin = request.query.gtin;

    const productResponse = await server.db
      .selectFrom("gtins")
      .select(["gtins.gtin", "gtins.product_id"])
      .innerJoin("offer_has_gtin", (join) =>
        join.onRef("offer_has_gtin.gtin", "=", "gtins.gtin"),
      )
      .innerJoin(
        (eb) =>
          eb
            .selectFrom("products")
            .select([
              "products.quantity_amount",
              "products.quantity_unit",
              "products.quantity_standard_amount",
              "products.id",
            ])
            .as("products"),
        (join) => join.onRef("products.id", "=", "gtins.product_id"),
      )
      .select([
        "products.quantity_amount",
        "products.quantity_unit",
        "products.quantity_standard_amount",
      ])
      .select((eb) => [
        jsonArrayFrom(
          eb
            .selectFrom("offers")
            .select([
              "offers.uri",
              "offers.price",
              "offers.pre_price",
              "offers.dealer_key",
              "offers.market",
              "offers.image",
            ])
            .select((eb) => [
              jsonObjectFrom(
                eb
                  .selectFrom("dealers")
                  .select([
                    "dealers.key",
                    "dealers.title",
                    "dealers.logo_url",
                    "dealers.description",
                    "dealers.is_partner",
                    "dealers.url",
                  ])
                  .whereRef("dealers.market", "=", "offers.market")
                  .whereRef("offers.dealer_key", "=", "dealers.key"),
              ).as("dealerObject"),
            ])
            .whereRef("offers.uri", "=", "offer_has_gtin.offer_uri"),
        ).as("offers"),
      ])
      .select((eb) => [
        jsonArrayFrom(
          eb
            .selectFrom("product_market_infos")
            .select([
              "product_market_infos.title",
              "product_market_infos.market",
              "product_market_infos.brand_key",
            ])
            .select((eb) => [
              jsonObjectFrom(
                eb
                  .selectFrom("brands")
                  .select(["brands.key", "brands.title"])
                  .whereRef("brands.market", "=", "product_market_infos.market")
                  .whereRef(
                    "brands.key",
                    "=",
                    "product_market_infos.brand_key",
                  ),
              ).as("brandObject"),
            ])
            .whereRef(
              "gtins.product_id",
              "=",
              "product_market_infos.product_id",
            ),
        ).as("product_market_infos"),
      ])
      .where("gtins.gtin", "=", gtin)
      .executeTakeFirst();

    if (!productResponse) {
      return reply.status(404).send({ error: "Product not found" });
    }

    const standardUnit = getSIUnit(productResponse.quantity_unit);
    productResponse.offers = productResponse.offers.map((offer) => ({
      ...offer,
      uri: getLegacyUri(offer.uri),
    }));

    return reply.status(200).send({
      product: { ...productResponse, standard_unit: standardUnit.symbol },
    });
  };

  server.get("/gtins/gtin", getByGtinSchema, getByGtinHandler);
};
