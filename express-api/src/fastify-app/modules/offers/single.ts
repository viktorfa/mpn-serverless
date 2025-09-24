import {
  type FastifyReply,
  type FastifyRequest,
  type FastifyInstance,
} from "fastify";
import { Static, Type } from "@sinclair/typebox";
import { sql } from "kysely";

import {
  getUri,
  getQuantity,
  getValue,
  convertDenormalizedOffer,
} from "./utils";
import { jsonArrayFrom, jsonObjectFrom } from "kysely/helpers/postgres";

export const getSingleSchema = {
  schema: {
    params: Type.Object({
      uri: Type.String(),
    }),
    query: Type.Object({
      market: Type.String(),
    }),
    response: {
      200: Type.Object({
        offer: Type.Object({}, { additionalProperties: true }),
        identical: Type.Array(Type.Object({}, { additionalProperties: true })),
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

export const getSingleHandler = async (
  request: FastifyRequest<{
    Params: Static<typeof getSingleSchema.schema.params>;
    Querystring: Static<typeof getSingleSchema.schema.query>;
  }>,
  reply: FastifyReply,
  server: FastifyInstance,
): Promise<Static<(typeof getSingleSchema.schema.response)["200"]>> => {
  const uri = getUri(request.params.uri);

  const offer = await server.db
    .selectFrom("offers")
    .select([
      "offers.uri",
      "offers.product_id",
      "offers.market",
      "offers.price",
      "offers.pre_price",
      "offers.currency",
      "offers.href",
      "offers.ahref",
      "offers.title",
      "offers.subtitle",
      "offers.description",
      "offers.short_description",
      "offers.dealer_key",
      "offers.image",
      "offers.mpn_stock",
      "offers.provenance",
      "offers.valid_from",
      "offers.valid_through",
    ])
    .select((eb) => [
      jsonArrayFrom(
        eb
          .selectFrom("dealers")
          .select([
            "dealers.key",
            "dealers.title",
            "dealers.logo_url",
            "dealers.url",
            "dealers.market",
          ])
          //.where("dealers.market", "=", request.query.market)
          .whereRef("dealers.key", "=", "offers.dealer_key"),
      ).as("dealerObject"),
    ])
    .select((eb) => [
      jsonArrayFrom(
        eb
          .selectFrom("offer_has_gtin")
          .select(["offer_has_gtin.gtin"])
          .whereRef("offer_has_gtin.offer_uri", "=", "offers.uri"),
      ).as("dbGtins"),
    ])
    .where("uri", "=", uri)
    .executeTakeFirst();

  if (!offer) {
    return reply.code(404).send({ error: "Offer not found" });
  } else {
    let identical = [];

    const [denormalizedProduct, marketInfo] = await Promise.all([
      server.db
        .selectFrom("denormalized_products")
        .select([
          "denormalized_products.offers",
          "denormalized_products.quantity_unit",
          "denormalized_products.quantity_amount",
        ])
        .where("product_id", "=", offer.product_id)
        .where("market", "=", offer.market)
        .executeTakeFirst(),
      server.db
        .selectFrom("product_market_infos")
        .select([
          "product_market_infos.product_id",
          "product_market_infos.brand_key",
          "product_market_infos.vendor_key",
        ])
        .select((eb) => [
          jsonObjectFrom(
            eb
              .selectFrom("products")
              .select([
                "products.id",
                "products.quantity_unit",
                "products.quantity_amount",
                "products.nutrition",
              ])
              .whereRef("product_market_infos.product_id", "=", "products.id"),
          ).as("productObject"),
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
              .whereRef(
                "product_market_infos.product_id",
                "=",
                "product_has_ingredient.product_id",
              )
              .innerJoin(
                "ingredients",
                "product_has_ingredient.ingredient_id",
                "ingredients.id",
              )
              .distinctOn("ingredients.id"),
          ).as("ingredients"),
        ])
        .select((eb) => [
          jsonObjectFrom(
            eb
              .selectFrom("vendors")
              .select(["vendors.key", "vendors.title"])
              .whereRef("vendors.key", "=", "product_market_infos.vendor_key")
              .where("market", "=", offer.market),
          ).as("vendorObject"),
        ])
        .select((eb) => [
          jsonObjectFrom(
            eb
              .selectFrom("brands")
              .select(["brands.key", "brands.title"])
              .whereRef("brands.key", "=", "product_market_infos.brand_key")
              .where("market", "=", offer.market),
          ).as("brandObject"),
        ])
        .select((eb) => [
          jsonArrayFrom(
            eb
              .selectFrom("categories")
              .select(["categories.key", "categories.title"])
              .where(
                sql<boolean>`categories.key = ANY(SELECT unnest(public.get_category_hierarchy(${eb.ref(
                  "product_market_infos.category_key",
                )}, ${eb.ref("product_market_infos.context")})))`,
              ),
          ).as("categories"),
        ])
        .where("product_id", "=", offer.product_id)
        .where("market", "=", offer.market)
        .executeTakeFirst(),
    ]);

    if (denormalizedProduct) {
      const offerUris = [];
      denormalizedProduct.offers
        .filter((o) => o.uri !== uri)
        .forEach((o) => {
          if (!offerUris.includes(o.uri)) {
            offerUris.push(o.uri);
            identical.push(
              convertDenormalizedOffer({
                newOffer: o,
                product: denormalizedProduct,
              }),
            );
          }
        });
    }

    const quantity = getQuantity({
      unit: marketInfo.productObject?.quantity_unit,
      amount: parseFloat(marketInfo.productObject?.quantity_amount),
    });
    let pricePerQuantity: number;
    try {
      pricePerQuantity = parseFloat(offer.price) / quantity?.size.standard.min;
    } catch (e) {
      console.warn("Error parsing price per quantity");
      console.warn(e);
      pricePerQuantity = 0;
    }

    const [namespace, sku] = offer.uri.split(":");
    const legacyUri = `${namespace}:product:${sku}`;

    const gtins: Record<string, string> = {};
    offer.dbGtins.forEach((dbGtin) => {
      const [gtinType, gtin] = dbGtin.gtin.split(":");
      if (!gtinType.startsWith("_")) {
        gtins[gtinType] = gtin;
      }
    });

    const marketDealer = offer.dealerObject.find(
      (x) => x.market == request.query.market,
    );
    const dealerObject = marketDealer || offer.dealerObject[0];

    const formattedOffer = {
      uri: legacyUri,
      dealer: dealerObject?.title,
      dealerKey: dealerObject?.key,
      dealerObject,
      brand: marketInfo.brandObject?.title,
      brandKey: marketInfo.brandObject?.key,
      brandObject: marketInfo.brandObject,
      vendor: marketInfo.vendorObject?.title,
      vendorKey: marketInfo.vendorObject?.key,
      vendorObject: marketInfo.vendorObject,
      href: offer.href,
      imageUrl: offer.image,
      mpnStock: offer.mpn_stock,
      pricing: {
        price: offer.price,
        currency: offer.currency,
        prePrice: offer.pre_price,
      },
      provenance: offer.provenance,
      quantity,
      subtitle: offer.subtitle,
      title: offer.title,
      validThrough: offer.valid_through,
      value: getValue({
        unit: marketInfo.productObject?.quantity_unit,
        amount: pricePerQuantity,
      }),
      description: offer.description,
      market: offer.market,
      ahref: offer.ahref,
      mpnIngredients: {
        ingredients: marketInfo.ingredients.reduce((acc, curr) => {
          return {
            ...acc,
            [curr.ingredient_id]: {
              key: curr.ingredient_id,
              name: curr.title,
              shortDescription: curr.short_description,
            },
          };
        }, {}),
        processedScore: marketInfo.ingredients.reduce((acc, curr) => {
          return acc + curr.processed_value;
        }, 0),
      },
      mpnNutrition: Object.entries(
        marketInfo.productObject?.nutrition || {},
      ).reduce((acc, [k, v]) => {
        if (k === "kcals") {
          return {
            ...acc,
            energy: { value: v, key: "energy", name: "energy" },
            [k]: {
              key: k,
              name: k,
              value: v,
            },
          };
        }
        return {
          ...acc,
          [k]: {
            key: k,
            name: k,
            value: v,
          },
        };
      }, {}),
      mpnProperties: {},
      mpnCategories: marketInfo.categories.map((cat) => ({
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
