import { filterIdenticalOffers } from "./../services/offers";
import _, { pick } from "lodash";
import { Parser, Response, Route, route } from "typera-express";
import * as t from "io-ts";
import {
  searchWithMongo,
  searchWithMongoRelations,
} from "@/api/services/search";
import { getLimitFromQueryParam } from "./typera-types";

const searchQueryParams = t.type({
  query: t.string,
  productCollection: t.union([t.string, t.undefined]),
  limit: t.union([t.string, t.undefined]),
  market: t.string,
  page: t.union([t.string, t.undefined]),
  dealers: t.union([t.string, t.undefined]),
  categories: t.union([t.string, t.undefined]),
  brands: t.union([t.string, t.undefined]),
  vendors: t.union([t.string, t.undefined]),
  price: t.union([t.string, t.undefined]),
  value: t.union([t.string, t.undefined]),
  proteins: t.union([t.string, t.undefined]),
  carbs: t.union([t.string, t.undefined]),
  fats: t.union([t.string, t.undefined]),
  kcals: t.union([t.string, t.undefined]),
  processedScore: t.union([t.string, t.undefined]),
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
      market,
      limit: _limit,
    });

    const result = {
      ...searchResults,
      items: searchResults.items.filter((offer) => offer.score > 20),
    };

    return Response.ok(result);
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
      brands,
      vendors,
      sort,
      market,
    } = request.query;
    const _query = query.substring(0, 127) || "";

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
      brands: brands ? brands.split(",") : null,
      vendors: vendors ? vendors.split(",") : null,
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
      query: _query,
      productCollections: productCollection ? [productCollection] : null,
      market: market,
      limit: _limit,
      ...searchArgs,
    });

    searchResults.items = filterIdenticalOffers({
      offers: searchResults.items,
    });

    return Response.ok(searchResults);
  });

const getRangeField = ({ field }: { field: string }) => {
  const [min, max] = (field || "").split(",");
  const result: { from?: number; to?: number } = {};
  if (min) {
    result.from = min ? Number.parseInt(min) : null;
  }
  if (max) {
    result.to = max ? Number.parseInt(max) : null;
  }
  return result;
};

export const searchRelations: Route<
  Response.Ok<MpnMongoRelationsSearchResponse> | Response.BadRequest<string>
> = route
  .get("/searchrelations")
  .use(Parser.query(searchQueryParams))
  .handler(async (request) => {
    const {
      query,
      productCollection,
      limit,
      page,
      dealers,
      price,
      value,
      proteins,
      carbs,
      fats,
      kcals,
      processedScore,
      categories,
      brands,
      vendors,
      sort,
      market,
    } = request.query;
    const _query = query.substring(0, 127) || "";

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
      brands: brands ? brands.split(",") : null,
      vendors: vendors ? vendors.split(",") : null,
      sort: sortConfig,
      price: null,
      value: null,
      page: Number.parseInt(page || "1"),
    };
    const _price = getRangeField({ field: price });
    if (_price.from || _price.to) {
      searchArgs.price = _price;
    }
    const _value = getRangeField({ field: value });
    if (_value.from || _value.to) {
      searchArgs.value = _value;
    }
    const _proteins = getRangeField({ field: proteins });
    if (_proteins.from || _proteins.to) {
      searchArgs.proteins = _proteins;
    }
    const _kcals = getRangeField({ field: kcals });
    if (_kcals.from || _kcals.to) {
      searchArgs.kcals = _kcals;
    }
    const _carbs = getRangeField({ field: carbs });
    if (_carbs.from || _carbs.to) {
      searchArgs.carbs = _carbs;
    }
    const _fats = getRangeField({ field: fats });
    if (_fats.from || _fats.to) {
      searchArgs.fats = _fats;
    }
    const _processedScore = getRangeField({ field: processedScore });
    if (_processedScore.from || _processedScore.to) {
      searchArgs.processedScore = _processedScore;
    }

    const searchResults = await searchWithMongoRelations({
      query: _query,
      productCollections: productCollection ? [productCollection] : null,
      market,
      limit: _limit,
      ...searchArgs,
    });

    //searchResults.items = filterIdenticalOffers({
    //  offers: searchResults.items,
    //});

    return Response.ok(searchResults);
  });
export const searchRelationsCondensed: Route<
  Response.Ok<MpnMongoRelationsSearchResponse> | Response.BadRequest<string>
> = route
  .get("/searchrelationscondensed")
  .use(Parser.query(searchQueryParams))
  .handler(async (request) => {
    const {
      query,
      productCollection,
      limit,
      page,
      dealers,
      price,
      value,
      proteins,
      carbs,
      fats,
      kcals,
      processedScore,
      categories,
      brands,
      vendors,
      sort,
      market,
    } = request.query;
    const _query = query.substring(0, 127) || "";

    const _limit = getLimitFromQueryParam(limit, 6);

    const _sort = sort ? sort.split(":") : null;
    const sortField = _.get(_sort, [0], "");
    const sortDirection = _.get(_sort, [1]) === "desc" ? -1 : 1;
    const sortConfig: { [x: string]: 1 | -1 } = sortField
      ? { [sortField]: sortDirection }
      : null;

    const searchArgs = {
      dealers: dealers ? dealers.split(",") : null,
      categories: categories ? categories.split(",") : null,
      brands: brands ? brands.split(",") : null,
      vendors: vendors ? vendors.split(",") : null,
      sort: sortConfig,
      price: null,
      value: null,
      page: Number.parseInt(page || "1"),
    };
    const _price = getRangeField({ field: price });
    if (_price.from || _price.to) {
      searchArgs.price = _price;
    }
    const _value = getRangeField({ field: value });
    if (_value.from || _value.to) {
      searchArgs.value = _value;
    }
    const _proteins = getRangeField({ field: proteins });
    if (_proteins.from || _proteins.to) {
      searchArgs.proteins = _proteins;
    }
    const _kcals = getRangeField({ field: kcals });
    if (_kcals.from || _kcals.to) {
      searchArgs.kcals = _kcals;
    }
    const _carbs = getRangeField({ field: carbs });
    if (_carbs.from || _carbs.to) {
      searchArgs.carbs = _carbs;
    }
    const _fats = getRangeField({ field: fats });
    if (_fats.from || _fats.to) {
      searchArgs.fats = _fats;
    }
    const _processedScore = getRangeField({ field: processedScore });
    if (_processedScore.from || _processedScore.to) {
      searchArgs.processedScore = _processedScore;
    }

    const searchResults = await searchWithMongoRelations({
      query: _query,
      productCollections: productCollection ? [productCollection] : null,
      market,
      limit: _limit,
      ...searchArgs,
      projection: { title: 1, imageUrl: 1 },
    });

    //searchResults.items = filterIdenticalOffers({
    //  offers: searchResults.items,
    //});

    const condensedResponse = searchResults.items.map((item) => {
      return pick(
        {
          ...item,
          offers: item.offers.map((offer) =>
            pick(offer, [
              "href",
              "ahref",
              "subtitle",
              "pricing",
              "validThrough",
              "dealerKey",
            ]),
          ),
        },
        ["offers", "title", "imageUrl"],
      );
    });

    return Response.ok(condensedResponse);
  });
