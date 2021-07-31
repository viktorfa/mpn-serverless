import * as t from "io-ts";

export const productCollectionQueryParams = t.type({
  productCollection: t.string,
});
export const limitQueryParams = t.type({
  limit: t.union([t.string, t.undefined]),
});
export const productCollectionAndLimitQueryParams = t.type({
  productCollection: t.string,
  limit: t.union([t.string, t.undefined]),
});
export const marketQueryParams = t.type({
  market: t.union([t.string, t.undefined]),
});

export const getLimitFromQueryParam = (
  limitParam: string | undefined,
  _default: number = 32,
  max: number = 256,
): number => {
  const parsedLimit = Number.parseInt(limitParam);
  return parsedLimit ? Math.min(max, parsedLimit) : _default;
};
