import { isSameDay, addDays, parse, format } from "date-fns";
import { mean as calcMean, uniqBy } from "lodash";

import { getCollection } from "@/config/mongo";

export const getPricingHistory = async ({ uri }) => {
  const offerPricingCollection = await getCollection("offerpricings");
  const pricingHistory: PricingHistoryObject[] = uniqBy(
    await offerPricingCollection
      .find<PricingHistoryObject>({ uri })
      .sort({ date: 1 })
      .toArray(),
    (x) => x.date,
  );
  if (pricingHistory.length > 0) {
    const prices = pricingHistory.map((x) => x.pricing.price);
    const mean = calcMean(prices);
    const max = Math.max(...prices);
    const min = Math.min(...prices);
    const filledHistory = fillPricingHistory({ pricingHistory });
    return {
      history: filledHistory.map((x) => ({
        ...x,
        normalizedPrice: x.pricing.price / max,
      })),
      mean,
      max,
      min,
    };
  } else {
    return { history: [] };
  }
};

export const fillPricingHistory = ({
  pricingHistory,
}: {
  pricingHistory: PricingHistoryObject[];
}) => {
  const startDate = addDays(parse(pricingHistory[0].date, "yyyy-MM-dd", 0), 1);
  const endDate = new Date();
  let counterDate = new Date(startDate);
  let counterPricingIndex = 0;
  let counterPricing = pricingHistory[counterPricingIndex];

  const result = [counterPricing];

  while (!isSameDay(counterDate, addDays(endDate, 1))) {
    if (
      pricingHistory[counterPricingIndex + 1] &&
      isSameDay(
        counterDate,
        parse(pricingHistory[counterPricingIndex + 1].date, "yyyy-MM-dd", 0),
      )
    ) {
      counterPricingIndex++;
      counterPricing = pricingHistory[counterPricingIndex];
      result.push({ ...counterPricing });
    } else {
      result.push({
        ...counterPricing,
        date: format(new Date(counterDate), "yyyy-MM-dd"),
      });
    }
    counterDate = addDays(counterDate, 1);
  }

  return result;
};
