import { isSameDay, addDays, parse, format } from "date-fns";
import { mean as calcMean, uniqBy, sortBy } from "lodash";

import { getCollection } from "@/config/mongo";

export const getPricingHistoryV2 = ({
  pricingHistory,
  endDate,
}: {
  endDate?: Date;
  pricingHistory: { history: PricingHistoryObject[] };
}) => {
  const prices = pricingHistory.history.map((x) => x.price);
  const mean = calcMean(prices);
  const max = Math.max(...prices);
  const min = Math.min(...prices);
  const filledHistory = fillPricingHistory({
    pricingHistory: sortBy(uniqBy(pricingHistory.history, "date"), ["date"]),
    endDate,
  });

  return {
    ...pricingHistory,
    history: filledHistory.map((x) => ({
      ...x,
      normalizedPrice: x.price / max,
    })),
    mean,
    max,
    min,
  };
};
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
  endDate: _endDate,
}: {
  pricingHistory: PricingHistoryObject[];
  endDate?: Date;
}) => {
  const startDate = addDays(parse(pricingHistory[0].date, "yyyy-MM-dd", 0), 1);
  let endDate = new Date();
  if (_endDate && _endDate < endDate) {
    endDate = _endDate;
  }
  let counterDate = new Date(startDate);
  let counterPricingIndex = 0;
  let counterPricing = pricingHistory[counterPricingIndex];

  const result = [counterPricing];

  while (!isSameDay(counterDate, addDays(endDate, 1))) {
    if (
      pricingHistory[counterPricingIndex + 1] &&
      format(counterDate, "yyyy-MM-dd") ===
        pricingHistory[counterPricingIndex + 1].date
    ) {
      counterPricingIndex++;
      counterPricing = pricingHistory[counterPricingIndex];
      result.push({ ...counterPricing });
    } else {
    }
    counterDate = addDays(counterDate, 1);
  }

  return result;
};
