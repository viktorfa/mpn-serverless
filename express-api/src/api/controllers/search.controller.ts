import _ from "lodash";
import { Parser, Response, Route, route, URL } from "typera-express";
import * as t from "io-ts";
import {
  search as searchElastic,
  querySuggestion as querySuggestionElastic,
  registerClick as registerClickElastic,
} from "@/api/services/search";
import { DEFAULT_PRODUCT_COLLECTION } from "../utils/constants";
import { stage } from "@/config/vars";

export const getEngineName = (productCollectionName: string): string => {
  let result = "";
  if (productCollectionName.endsWith("s")) {
    result = productCollectionName;
  } else {
    result = `${productCollectionName}s`;
  }
  if (stage === "prod") {
    return result;
  } else {
    return `${result}-dev`;
  }
};

const filterDuplicateOffers = (offers: MpnResultOffer[]): MpnResultOffer[] =>
  _.uniqBy(offers, (x) => x.dealer + x.pricing.price + x.title);

const productCollectionQueryParams = t.type({
  productCollection: t.union([t.string, t.undefined]),
});
const productCollectionAndLimitQueryParams = t.type({
  productCollection: t.union([t.string, t.undefined]),
  limit: t.union([t.number, t.undefined]),
});
const searchQueryParams = t.type({
  query: t.string,
  productCollection: t.union([t.string, t.undefined]),
  limit: t.union([t.number, t.undefined]),
});

export const search: Route<
  Response.Ok<MpnResultOffer[]> | Response.BadRequest<string>
> = route
  .get("/search")
  .use(Parser.query(searchQueryParams))
  .handler(async (request) => {
    const {
      limit = 256,
      query,
      productCollection = DEFAULT_PRODUCT_COLLECTION,
    } = request.query;
    const searchResults = await searchElastic(
      query,
      getEngineName(productCollection),
      limit,
    );
    return Response.ok(filterDuplicateOffers(searchResults));
  });
export const searchPathParam: Route<
  Response.Ok<MpnResultOffer[]> | Response.BadRequest<string>
> = route
  .get("/search/", URL.str("query"))
  .use(Parser.query(productCollectionAndLimitQueryParams))
  .handler(async (request) => {
    const query = request.routeParams.query;
    const {
      productCollection = DEFAULT_PRODUCT_COLLECTION,
      limit = 256,
    } = request.query;
    const searchResults = await searchElastic(
      query,
      getEngineName(productCollection),
      limit,
    );
    return Response.ok(filterDuplicateOffers(searchResults));
  });

export const querySuggestion: Route<
  Response.Ok<string[]> | Response.BadRequest<string>
> = route
  .get("/search/hint")
  .use(Parser.query(searchQueryParams))
  .handler(async (request) => {
    const { productCollection = DEFAULT_PRODUCT_COLLECTION } = request.query;
    const query = request.query.query;
    const searchResults = await querySuggestionElastic(
      query,
      getEngineName(productCollection),
    );
    return Response.ok(searchResults);
  });

const registerClickBody = t.type({
  query: t.string,
  document_id: t.string,
  request_id: t.string,
  tags: t.union([t.array(t.string), t.undefined]),
});

export const registerClick: Route<
  Response.NoContent | Response.BadRequest<string>
> = route
  .post("/search/click")
  .use(Parser.query(productCollectionQueryParams))
  .use(Parser.body(registerClickBody))
  .handler(async (request) => {
    const { productCollection = DEFAULT_PRODUCT_COLLECTION } = request.query;
    try {
      await registerClickElastic(
        request.body,
        getEngineName(productCollection),
      );
      return Response.noContent();
    } catch (e) {
      console.error(e);
      console.error(`Could not register click for ${request.body.request_id}`);
      return Response.badRequest();
    }
  });
