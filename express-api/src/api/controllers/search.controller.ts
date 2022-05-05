import _ from "lodash";
import { Parser, Response, Route, route } from "typera-express";
import * as t from "io-ts";
import {
  querySuggestion as querySuggestionElastic,
  registerClick as registerClickElastic,
  searchWithMongo,
  searchWithElastic,
} from "@/api/services/search";
import { stage } from "@/config/vars";
import {
  getLimitFromQueryParam,
  productCollectionQueryParams,
} from "./typera-types";
import { findByKeys } from "../services/categories";
import { defaultDealerProjection } from "../services/offers";
import { getCollection } from "@/config/mongo";

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

export const searchExtra: Route<
  Response.Ok<MpnMongoSearchResponse> | Response.BadRequest<string>
> = route
  .get("/searchextra")
  .use(Parser.query(searchQueryParams))
  .handler(async (request) => {
    const { limit, query, market } = request.query;
    if (query.length > 128) {
      return Response.badRequest("Query longer than 128 characters");
    }
    const _limit = getLimitFromQueryParam(limit, 8);

    const searchResults = await searchWithMongo({
      query,
      markets: [market],
      limit: _limit,
    });

    const result = {
      ...searchResults,
      items: searchResults.items.filter((offer) => offer.score > 20),
    };

    return Response.ok(result);
  });

export const searchExtraV1: Route<
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

    const engineName = "no-mpn-offers";
    const searchResults = await searchWithElastic({
      query,
      engineName,
      limit: _limit,
    });
    return Response.ok(
      filterDuplicateOffers(
        searchResults.items.filter((offer) => offer.score > 20),
      ),
    );
  });

export const search: Route<
  Response.Ok<MpnMongoSearchResponse> | Response.BadRequest<string>
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
      market,
    } = request.query;
    if (query.length > 128) {
      return Response.badRequest("Query longer than 128 characters");
    }

    const _limit = getLimitFromQueryParam(limit, 256);

    const _sort = sort ? sort.split(":") : null;
    const sortField = _.get(_sort, [0], "");
    const sortDirection = _.get(_sort, [1]) === "desc" ? -1 : 1;
    const sortConfig: { [x: string]: 1 | -1 } = sortField
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

    const searchResults = await searchWithMongo({
      query,
      productCollections: [productCollection],
      markets: [market],
      limit: _limit,
      ...searchArgs,
    });

    const dealerKeys = Array.from(
      new Set(
        searchResults.facets.dealersFacet.buckets.map(
          (dealerBucket) => dealerBucket._id,
        ),
      ),
    );
    const dealerCollection = await getCollection("dealers");
    const dealerObjects = await dealerCollection
      .find({ key: { $in: dealerKeys } })
      .project(defaultDealerProjection)
      .toArray();
    const dealerMap = {};
    dealerObjects.forEach((dealer) => {
      dealerMap[dealer.key] = dealer;
    });

    const newDealerFacet = { buckets: [] };

    searchResults.facets.dealersFacet.buckets.forEach((dealerBucket) => {
      newDealerFacet.buckets.push({
        ...dealerBucket,
        key: dealerBucket._id,
        ...dealerMap[dealerBucket._id],
      });
    });
    searchResults.facets.dealersFacet = newDealerFacet;

    searchResults.items = searchResults.items.map((offer) => {
      return {
        ...offer,
        dealerObject: dealerMap[offer.dealer] || { key: offer.dealer },
      };
    });

    return Response.ok(searchResults);
  });

export const searchV1: Route<
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

    const searchResults = await searchWithElastic({
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
    const dealerKeys = Array.from(
      new Set(result.items.map((offer) => offer.dealer)),
    );
    const dealerCollection = await getCollection("dealers");
    const dealerObjects = await dealerCollection
      .find({ key: { $in: dealerKeys } })
      .project(defaultDealerProjection)
      .toArray();
    const dealerMap = {};
    dealerObjects.forEach((dealer) => {
      dealerMap[dealer.key] = dealer;
    });
    const newDealerFacet = [{ data: [] }];
    newDealerFacet[0].data = result.facets.dealer[0].data.map((dealer) => {
      if (dealerMap[dealer.value]) {
        return { ...dealerMap[dealer.value], ...dealer };
      } else {
        return { ...dealer };
      }
    });
    result.facets.dealer = newDealerFacet;

    result.items = result.items.map((offer) => {
      return {
        ...offer,
        dealerObject: dealerMap[offer.dealer] || { key: offer.dealer },
      };
    });
    return Response.ok(result);
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
