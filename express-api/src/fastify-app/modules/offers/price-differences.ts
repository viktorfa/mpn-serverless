import { jsonObjectFrom } from "kysely/helpers/postgres";
import { FastifyReply, FastifyRequest, type FastifyInstance } from "fastify";
import { Static, Type } from "@sinclair/typebox";
import { sql } from "kysely";
import {
  getCommaSeparatedAsList,
  getQuantity,
  getValue,
  standardizeQuantity,
} from "./utils";
import { Offers } from "generated/kysely";

export const priceDifferencesSchema = {
  schema: {
    querystring: Type.Object({
      market: Type.String(),
      productCollection: Type.String(),
      limit: Type.Integer(),
      direction: Type.Union([Type.Literal("asc"), Type.Literal("desc")]),
      dealers: Type.Optional(Type.String()),
      daysPast: Type.Integer(),
      categories: Type.Optional(Type.String()),
    }),

    response: {
      200: Type.Array(Type.Object({}, { additionalProperties: true })),
      404: Type.Object({
        error: Type.String(),
      }),
    },
  },
};

export const priceDifferencesHandler = async (
  request: FastifyRequest<{
    Querystring: Static<typeof priceDifferencesSchema.schema.querystring>;
  }>,
  reply: FastifyReply,
  server: FastifyInstance,
): Promise<Static<(typeof priceDifferencesSchema.schema.response)["200"]>> => {
  const orderNullsLast = (direction: "asc" | "desc") =>
    sql`${sql.raw(direction)} nulls last`;

  const dealerKeys = getCommaSeparatedAsList(request.query.dealers);
  const categoryKeys = getCommaSeparatedAsList(request.query.categories);

  const now = new Date();

  const offersQuery = server.db
    .selectFrom("offers")
    .selectAll("offers")
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
          .where("market", "=", request.query.market)
          .whereRef("offers.dealer_key", "=", "dealers.key"),
      ).as("dealerObject"),
    ])
    .select((eb) => [
      jsonObjectFrom(
        eb
          .selectFrom("products")
          .select([
            "products.id",
            "products.quantity_unit",
            "products.quantity_amount",
          ])
          .whereRef("offers.product_id", "=", "products.id"),
      ).as("productObject"),
    ])
    .where("offers.market", "=", request.query.market)
    .where("offers.valid_through", ">", now)
    .orderBy(
      "difference_180_days_mean_percentage",
      orderNullsLast(request.query.direction),
    )
    .limit(Math.min(request.query.limit, 10));

  if (dealerKeys.length > 0) {
    offersQuery.where("dealer_key", "in", dealerKeys);
  }
  if (categoryKeys.length > 0) {
  }

  const offers = await offersQuery.execute();

  const result = offers.map((offer) => {
    const pricingHistoryObject = {
      difference7DaysMeanPercentage: offer.difference_7_days_mean_percentage,
      difference7DaysMean: offer.difference_7_days_mean,
      difference30DaysMeanPercentage: offer.difference_30_days_mean_percentage,
      difference30DaysMean: offer.difference_30_days_mean,
      difference90DaysMeanPercentage: offer.difference_90_days_mean_percentage,
      difference90DaysMean: offer.difference_90_days_mean,
      difference180DaysMeanPercentage:
        offer.difference_180_days_mean_percentage,
      difference180DaysMean: offer.difference_180_days_mean,
    };

    return {
      ...convertOffer({ newOffer: offer, product: offer.productObject }),
      ...pricingHistoryObject,
      imageUrl: offer.image,
      pricingHistoryObject,
    };
  });

  return reply.code(200).send(result);
};

export function convertOffer({
  newOffer,
  product,
}: {
  newOffer: Offers;
  product?: any;
}): any {
  const [dealer, sku] = newOffer.uri.split(":");
  // Must keep old urls on frontend
  const uri = `${dealer}:product:${sku}`;

  const standardQuantityAmount = standardizeQuantity(
    product?.quantity_unit,
    product?.quantity_amount,
  );

  const quantity = getQuantity({
    unit: product?.quantity_unit,
    amount: product?.quantity_amount,
  });
  const rawStandardValue = newOffer.price / standardQuantityAmount;
  const value = getValue({
    unit: product?.quantity_unit,
    amount: rawStandardValue,
  });

  return {
    title: newOffer.title,
    uri,
    href: newOffer.href,
    mpnStock: newOffer.mpn_stock, // Default value as it's not available
    pricing: {
      price: newOffer.price,
      currency: newOffer.currency,
      prePrice: newOffer.pre_price || null,
      priceUnit: newOffer.price_unit || null,
    },
    validThrough: newOffer.valid_through,
    market: newOffer.market,
    ahref: newOffer.ahref || null,
    dealerKey: newOffer.dealer_key,
    quantity,
    value,
    dealerObject: newOffer.dealerObject
      ? {
          key: newOffer.dealerObject.key,
          logoUrl: newOffer.dealerObject.logo_url || null,
          market: newOffer.dealerObject.market,
          text: newOffer.dealerObject.title || null,
          url: newOffer.dealerObject.url || null,
        }
      : null,
  };
}
