import _ from "lodash";
import { Parser, Response, Route, route, URL } from "typera-express";
import * as t from "io-ts";
import {
  search as searchElastic,
  querySuggestion as querySuggestionElastic,
  registerClick as registerClickElastic,
} from "@/api/services/search";
import { stage } from "@/config/vars";
import {
  getLimitFromQueryParam,
  productCollectionAndLimitQueryParams,
  productCollectionQueryParams,
} from "./typera-types";

export const getEngineName = (productCollectionName: string): string => {
  if (stage === "prod") {
    return productCollectionName;
  } else {
    return `${productCollectionName}-dev`;
  }
};

const filterDuplicateOffers = (offers: MpnResultOffer[]): MpnResultOffer[] =>
  _.uniqBy(offers, (x) => x.dealer + x.pricing.price + x.title);

const searchQueryParams = t.type({
  query: t.string,
  productCollection: t.string,
  limit: t.union([t.string, t.undefined]),
});

export const searchExtra: Route<
  Response.Ok<MpnResultOffer[]> | Response.BadRequest<string>
> = route
  .get("/searchextra")
  .use(Parser.query(searchQueryParams))
  .handler(async (request) => {
    const { limit, query } = request.query;
    if (query.length > 128) {
      return Response.badRequest("Query longer than 128 characters");
    }
    const _limit = getLimitFromQueryParam(limit, 8);

    const productCollection = "extraoffers";
    const searchResults = await searchElastic(query, productCollection, _limit);
    return Response.ok(
      filterDuplicateOffers(searchResults.filter((offer) => offer.score > 20)),
    );
  });

export const search: Route<
  Response.Ok<MpnResultOffer[]> | Response.BadRequest<string>
> = route
  .get("/search")
  .use(Parser.query(searchQueryParams))
  .handler(async (request) => {
    const { limit, query, productCollection } = request.query;
    if (query.length > 128) {
      return Response.badRequest("Query longer than 128 characters");
    }
    const _limit = getLimitFromQueryParam(limit, 256);

    const searchResults = await searchElastic(
      query,
      getEngineName(productCollection),
      _limit,
    );
    return Response.ok(filterDuplicateOffers(searchResults));
  });
export const searchPathParam: Route<
  Response.Ok<MpnResultOffer[]> | Response.BadRequest<string>
> = route
  .get("/search/:query")
  .use(Parser.query(productCollectionAndLimitQueryParams))
  .handler(async (request) => {
    const query = request.routeParams.query;
    if (query.length > 128) {
      return Response.badRequest("Query longer than 128 characters");
    }
    const { productCollection, limit } = request.query;
    const _limit = getLimitFromQueryParam(limit, 256);
    const searchResults = await searchElastic(
      query,
      getEngineName(productCollection),
      _limit,
    );
    return Response.ok(filterDuplicateOffers(searchResults));
  });

export const querySuggestion: Route<
  Response.Ok<string[]> | Response.BadRequest<string>
> = route
  .get("/search/hint")
  .use(Parser.query(searchQueryParams))
  .handler(async (request) => {
    const { productCollection } = request.query;
    const query = request.query.query;
    if (query.length > 128) {
      return Response.badRequest("Query longer than 128 characters");
    }
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
    const { productCollection } = request.query;
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
