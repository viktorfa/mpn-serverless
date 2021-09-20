import _ from "lodash";
import { Parser, Response, Route, route, URL } from "typera-express";
import * as t from "io-ts";
import {
  search as searchElastic,
  querySuggestion as querySuggestionElastic,
  registerClick as registerClickElastic,
  searchWithFilter,
} from "@/api/services/search";
import { stage } from "@/config/vars";
import {
  getLimitFromQueryParam,
  productCollectionQueryParams,
} from "./typera-types";
import { findByKeys } from "../services/categories";

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
  market: t.union([t.string, t.undefined]),
  page: t.union([t.string, t.undefined]),
  dealers: t.union([t.string, t.undefined]),
  categories: t.union([t.string, t.undefined]),
  price: t.union([t.string, t.undefined]),
  sort: t.union([t.string, t.undefined]),
});
const searchQueryParamsNoQuery = t.type({
  productCollection: t.string,
  limit: t.union([t.string, t.undefined]),
  page: t.union([t.string, t.undefined]),
  dealers: t.union([t.string, t.undefined]),
  categories: t.union([t.string, t.undefined]),
  price: t.union([t.string, t.undefined]),
  sort: t.union([t.string, t.undefined]),
});

export const searchExtra: Route<
  Response.Ok<MpnResultOffer[]> | Response.BadRequest<string>
> = route
  .get("/searchextra")
  .use(Parser.query(searchQueryParams))
  .handler(async (request) => {
    const { limit, query, market } = request.query;
    if (query.length > 128) {
      return Response.badRequest("Query longer than 128 characters");
    }
    const _limit = getLimitFromQueryParam(limit, 8);

    const productCollection = "no-mpn-offers";
    const searchResults = await searchElastic(query, productCollection, _limit);
    return Response.ok(
      filterDuplicateOffers(searchResults.filter((offer) => offer.score > 20)),
    );
  });

export const search: Route<
  Response.Ok<{ items: MpnResultOffer[] }> | Response.BadRequest<string>
> = route
  .get("/search")
  .use(Parser.query(searchQueryParams))
  .handler(async (request) => {
    const {
      query,
      productCollection,
      limit,
      page,
      dealers,
      price,
      categories,
      sort,
    } = request.query;
    if (query.length > 128) {
      return Response.badRequest("Query longer than 128 characters");
    }

    const _limit = getLimitFromQueryParam(limit, 256);

    const _sort = sort ? sort.split(":") : null;
    const sortField = _.get(_sort, [0], "");
    const sortDirection = _.get(_sort, [1]) === "desc" ? "desc" : "asc";
    const sortConfig: { [x: string]: "asc" | "desc" } = sortField
      ? { [sortField]: sortDirection }
      : null;

    const searchArgs = {
      dealers: dealers ? dealers.split(",") : null,
      categories: categories ? categories.split(",") : null,
      sort: sortConfig,
      price: null,
      page: Number.parseInt(page || "1"),
    };
    const [priceMin, priceMax] = (price || "").split(",");
    const _price: { from?: number; to?: number } = {};
    if (priceMin) {
      _price.from = priceMin ? Number.parseInt(priceMin) : null;
    }
    if (priceMax) {
      _price.to = priceMax ? Number.parseInt(priceMax) : null;
    }
    if (_price.from || _price.to) {
      searchArgs.price = _price;
    }

    const searchResults = await searchWithFilter({
      query,
      engineName: getEngineName(productCollection),
      limit: _limit,
      ...searchArgs,
    });

    const result: {
      facets: any;
      meta: any;
      items: MpnResultOffer[];
      categories?: Record<string, MpnCategory>;
    } = {
      facets: searchResults.facets,
      meta: searchResults.meta,
      items: filterDuplicateOffers(searchResults.items),
    };

    if (categories) {
      const mpnCategories = await findByKeys({ keys: categories.split(",") });
      result.categories = {};
      Object.values(mpnCategories).forEach((x) => {
        result.categories[x.key] = x;
      });
    }
    return Response.ok(result);
  });

export const searchPathParam: Route<
  Response.Ok<MpnResultOffer[]> | Response.BadRequest<string>
> = route
  .get("/search/:query")
  .use(Parser.query(searchQueryParamsNoQuery))
  .handler(async (request) => {
    const query = request.routeParams.query;
    if (query.length > 128) {
      return Response.badRequest("Query longer than 128 characters");
    }
    const { productCollection, limit, dealers, price, categories, sort } =
      request.query;
    const _limit = getLimitFromQueryParam(limit, 256);

    const _sort = sort ? sort.split(":") : null;
    const sortField = _.get(_sort, [0], "");
    const sortDirection = _.get(_sort, [1]) === "desc" ? "desc" : "asc";
    const sortConfig: { [x: string]: "asc" | "desc" } = sortField
      ? { [sortField]: sortDirection }
      : null;

    const searchArgs = {
      dealers: dealers ? dealers.split(",") : null,
      categories: categories ? categories.split(",") : null,
      sort: sortConfig,
      price: null,
    };
    const [priceMin, priceMax] = (price || "").split(",");
    const _price: { from?: number; to?: number } = {};
    if (priceMin) {
      _price.from = Number.parseInt(priceMin);
    }
    if (priceMax) {
      _price.to = Number.parseInt(priceMax);
    }
    if (_price.from || _price.to) {
      searchArgs.price = _price;
    }

    const searchResults = await searchWithFilter({
      query,
      engineName: getEngineName(productCollection),
      limit: _limit,
      ...searchArgs,
    });
    return Response.ok(filterDuplicateOffers(searchResults.items));
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
