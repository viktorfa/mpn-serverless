import * as t from "io-ts";

export const productCollectionQueryParams = t.type({
  productCollection: t.string,
});
