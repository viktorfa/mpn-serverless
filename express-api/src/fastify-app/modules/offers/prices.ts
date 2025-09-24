import { FastifyReply, FastifyRequest, type FastifyInstance } from "fastify";
import { Static, Type } from "@sinclair/typebox";
import { getUri } from "./utils";

export const getPricingSchema = {
  schema: {
    params: Type.Object({
      uri: Type.String(),
    }),
    response: {
      200: Type.Object({}, { additionalProperties: true }),
      404: Type.Object({
        error: Type.String(),
      }),
    },
  },
};

export const getPricingHandler = async (
  request: FastifyRequest<{
    Params: Static<typeof getPricingSchema.schema.params>;
  }>,
  reply: FastifyReply,
  server: FastifyInstance,
): Promise<Static<(typeof getPricingSchema.schema.response)["200"]>> => {
  const uri = getUri(request.params.uri);

  const recordedPrices = await server.db
    .selectFrom("offer_prices")
    .select(["offer_prices.price", "offer_prices.recorded_at"])
    .where("uri", "=", uri)
    .orderBy("recorded_at", "asc")
    .execute();

  if (recordedPrices.length === 0) {
    return reply.code(404).send({ error: "Offer not found" });
  }

  const result = {
    uri,
    history: [],

    latestPrice: 0,
    difference: 0,
    differencePercentage: 0,

    price7DaysMean: 0,
    difference7DaysMean: 0,
    difference7DaysMeanPercentage: 0,

    price30DaysMean: 0,
    difference30DaysMean: 0,
    difference30DaysMeanPercentage: 0,

    price365DaysMean: 0,
    difference365DaysMean: 0,
    difference365DaysMeanPercentage: 0,

    price90DaysMean: 0,
    difference90DaysMean: 0,
    difference90DaysMeanPercentage: 0,

    pricePrevYear90DaysMean: 0,
    differencePrevYear90DaysMean: 0,
    differencePrevYear90DaysPercentage: 0,

    mean: 0,
    max: 0,
    min: Number.MAX_SAFE_INTEGER,
  };

  const now = new Date();
  now.setUTCHours(23, 59, 59, 999);
  const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
  const ninetyDaysAgo = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
  const yearAgo = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
  const yearAndNinetyDaysAgo = new Date(
    now.getTime() - 455 * 24 * 60 * 60 * 1000,
  );
  const sevenDaysPrices = [];
  const thirtyDaysPrices = [];
  const ninetyDaysPrices = [];
  const yearPrices = [];
  const yearAndNinetyDaysPrices = [];

  for (const priceObject of recordedPrices) {
    const price = parseFloat(priceObject.price);
    if (priceObject.recorded_at > sevenDaysAgo) {
      sevenDaysPrices.push(price);
      result.price7DaysMean += price;
    }
    if (priceObject.recorded_at > thirtyDaysAgo) {
      thirtyDaysPrices.push(price);
      result.price30DaysMean += price;
    }
    if (priceObject.recorded_at > ninetyDaysAgo) {
      ninetyDaysPrices.push(price);
      result.price90DaysMean += price;
    }
    if (priceObject.recorded_at > yearAgo) {
      yearPrices.push(price);
      result.price365DaysMean += price;
    }
    if (
      priceObject.recorded_at > yearAndNinetyDaysAgo &&
      priceObject.recorded_at < yearAgo
    ) {
      yearAndNinetyDaysPrices.push(price);
      result.pricePrevYear90DaysMean += price;
    }
    if (price > result.max) {
      result.max = price;
    }
    if (price < result.min) {
      result.min = price;
    }
    result.mean += price;
  }

  result.latestPrice = parseFloat(
    recordedPrices[recordedPrices.length - 1].price,
  );
  result.mean /= recordedPrices.length;
  result.price7DaysMean /= sevenDaysPrices.length;
  result.price30DaysMean /= thirtyDaysPrices.length;
  result.price90DaysMean /= ninetyDaysPrices.length;
  result.price365DaysMean /= yearPrices.length;
  result.pricePrevYear90DaysMean /= yearAndNinetyDaysPrices.length;
  result.difference =
    result.latestPrice -
    (recordedPrices.length > 1
      ? parseFloat(recordedPrices[recordedPrices.length - 2].price)
      : result.latestPrice);
  result.differencePercentage = (result.difference / result.latestPrice) * 100;
  result.difference7DaysMean = result.latestPrice - result.price7DaysMean;
  result.difference7DaysMeanPercentage =
    (result.difference7DaysMean / result.latestPrice) * 100;
  result.difference30DaysMean = result.latestPrice - result.price30DaysMean;
  result.difference30DaysMeanPercentage =
    (result.difference30DaysMean / result.latestPrice) * 100;
  result.difference90DaysMean = result.latestPrice - result.price90DaysMean;
  result.difference90DaysMeanPercentage =
    (result.difference90DaysMean / result.latestPrice) * 100;
  result.difference365DaysMean = result.latestPrice - result.price365DaysMean;
  result.difference365DaysMeanPercentage =
    (result.difference365DaysMean / result.latestPrice) * 100;
  result.differencePrevYear90DaysMean =
    result.latestPrice - result.pricePrevYear90DaysMean;
  result.differencePrevYear90DaysPercentage =
    (result.differencePrevYear90DaysMean / result.latestPrice) * 100;

  result.history = recordedPrices.map((priceObject) => ({
    price: parseFloat(priceObject.price),
    date: priceObject.recorded_at.toISOString().substring(0, 10),
    normalizedPrice: parseFloat(priceObject.price) / result.max,
  }));

  return reply.code(200).send(result);
};
