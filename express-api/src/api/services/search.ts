import {
  defaultDealerProjection,
  defaultOfferProjection,
} from "@/api/models/mpnOffer.model";
import { elasticOfferToMpnOffer } from "@/api/models/mpnOffer.model";
import { getElasticClient } from "@/config/elastic";
import { getNowDate } from "../utils/helpers";
import APIError from "../utils/APIError";
import { getCollection } from "@/config/mongo";
import { offerCollectionName } from "../utils/constants";
import { getOffersByUris } from "./offers";
import { get } from "lodash";

export type MongoSearchParams = {
  query: string;
  productCollections?: string[];
  markets?: string[];
  limit?: number;
  page?: number;
  dealers?: string[];
  categories?: string[];
  brands?: string[];
  vendors?: string[];
  price?: { from?: number; to?: number };
  sort?: { [key: string]: 1 | -1 };
  isPartner?: boolean;
  isExtraOffers?: boolean;
  includeOutdated?: boolean;
  projection?: Record<string, number | boolean | Record<number, boolean>>;
};

export const searchWithMongo = async ({
  query,
  productCollections,
  markets,
  limit = 32,
  page = 1,
  dealers,
  categories,
  brands,
  vendors,
  price,
  sort,
  isPartner = false,
  isExtraOffers = false,
  includeOutdated = false,
  projection = defaultOfferProjection,
}: MongoSearchParams): Promise<MpnMongoSearchResponse> => {
  if (query.length > 127) {
    const message = `Query ${query} is too long (${query.length} characters). Max is 128.`;
    console.error(message);
    throw new APIError({
      status: 500,
      message,
    });
  }
  const now = getNowDate();

  const offerCollection = await getCollection(offerCollectionName);

  const facets: Record<string, { type: string; path: string }> = {
    dealersFacet: {
      type: "string",
      path: "dealer",
    },
  };

  const operator = {
    compound: {
      filter: [],
      must: [],
      should: [],
    },
  };

  if (price) {
    if (price.from) {
      operator.compound.filter.push({
        range: { gte: price.from, path: "pricing.price" },
      });
    }
    if (price.to) {
      operator.compound.filter.push({
        range: { lte: price.to, path: "pricing.price" },
      });
    }
  }

  if (isPartner) {
    operator.compound.filter.push({
      equals: { value: true, path: "isPartner" },
    });
  }
  if (!includeOutdated) {
    operator.compound.filter.push({
      range: { gte: now, path: "validThrough" },
    });
  }
  if (markets) {
    operator.compound.filter.push({ text: { query: markets, path: "market" } });
  }
  if (dealers) {
    operator.compound.filter.push({
      text: { query: dealers, path: "dealer" },
    });
  }
  if (brands) {
    operator.compound.filter.push({
      text: { query: brands, path: "brandKey" },
    });
  }
  if (vendors) {
    operator.compound.filter.push({
      text: { query: vendors, path: "vendorKey" },
    });
  }
  if (productCollections && !isExtraOffers) {
    operator.compound.filter.push({
      text: { query: productCollections, path: "siteCollection" },
    });
  }
  if (categories) {
    operator.compound.filter.push({
      text: { query: categories, path: "mpnCategories.key" },
    });
  }

  if (query && !sort) {
    operator.compound.must.push({
      text: {
        path: ["title", "subtitle", "brand"],
        query,
      },
    });
    operator.compound.should.push({
      text: {
        path: ["title"],
        query,
        score: { boost: { value: 3 } },
      },
    });
    operator.compound.should.push({
      text: {
        path: ["subtitle", "brand", "categories", "mpnCategories"],
        query,
        score: { boost: { value: 1.5 } },
      },
    });
    if (isExtraOffers) {
      const siteCollection = get(productCollections, [0]);
      if (siteCollection) {
        operator.compound.should.push({
          text: {
            path: "siteCollection",
            query: siteCollection,
            score: { boost: { value: 1.5 } },
          },
        });
      }
      operator.compound.should.push({
        equals: {
          path: "isPartner",
          value: true,
          score: { boost: { value: 1.5 } },
        },
      });
    }
    // Attempt to make search more restrictive (AND) after selecting sort
  } else if (query && sort) {
    query
      .split(" ")
      .map((x) => x.trim())
      .forEach((x) => {
        operator.compound.must.push({
          text: {
            path: ["title", "subtitle", "brand", "categories", "mpnCategories"],
            query: x,
          },
        });
      });
  }

  if (sort) {
    operator.compound.should.push({
      near: {
        path: Object.keys(sort)[0],
        origin: Object.values(sort)[0] === 1 ? -1e3 : 1e7 * 1,
        pivot: 2,
        score: { boost: { value: Number.MAX_SAFE_INTEGER } },
      },
    });
  }

  const aggregationPipeline: Record<string, any>[] = [
    {
      $search: {
        facet: {
          operator,
          facets,
        },
      },
    },
    { $limit: Math.min(limit, 1000) }, // Will be incredibly slow when sorting if the results are many
    { $skip: (Math.max(page - 1, 0) || 0) * limit },
    {
      $project: {
        ...projection,
        score: { $meta: "searchScore" },
      },
    },
    {
      $facet: {
        items: [{ $limit: limit }],
        meta: [{ $replaceWith: "$$SEARCH_META" }, { $limit: 1 }],
      },
    },
    { $unwind: "$meta" },
    {
      $set: {
        dealerKeys: {
          $map: {
            input: "$meta.facet.dealersFacet.buckets",
            as: "t",
            in: "$$t._id",
          },
        },
      },
    },
    {
      $lookup: {
        from: "dealers",
        localField: "dealerKeys",
        foreignField: "key",
        as: "dealers",
        pipeline: [{ $project: defaultDealerProjection }],
      },
    },
  ];

  const mongoSearchResponse = await offerCollection
    .aggregate(aggregationPipeline)
    .toArray();

  if (!mongoSearchResponse[0]?.items.length) {
    return {
      items: [],
      meta: { count: 0, page: 1 },
      facets: { dealersFacet: { buckets: [] } },
    };
  }

  const meta: MpnMongoSearchResponseMeta = {
    count: mongoSearchResponse[0].meta.count.lowerBound,
    page,
  };

  const result = {
    items: mongoSearchResponse[0].items,
    meta,
    facets: mongoSearchResponse[0].meta.facet,
  };

  const dealerMap = {};
  mongoSearchResponse[0].dealers.forEach((x) => {
    dealerMap[x.key] = x;
  });

  result.items.forEach((x) => {
    x.dealerObject = dealerMap[x.dealer] || { key: x.dealer };
  });
  result.facets.dealersFacet.buckets = result.facets.dealersFacet.buckets.map(
    (x) => {
      return {
        ...(dealerMap[x._id] || { key: x._id, _id: x._id }),
        ...x,
      };
    },
  );

  return result;
};
export const searchWithMongoNoFacets = async ({
  query,
  productCollections,
  markets,
  limit = 32,
  page = 1,
  dealers,
  categories,
  brands,
  vendors,
  price,
  sort,
  isPartner = false,
  isExtraOffers = false,
  includeOutdated = false,
  projection = defaultOfferProjection,
}: MongoSearchParams): Promise<Omit<MpnMongoSearchResponse, "facets">> => {
  if (query.length > 127) {
    const message = `Query ${query} is too long (${query.length} characters). Max is 128.`;
    console.error(message);
    throw new APIError({
      status: 500,
      message,
    });
  }
  const now = getNowDate();
  const offerCollection = await getCollection(offerCollectionName);

  const operator = {
    compound: {
      filter: [],
      must: [],
      should: [],
    },
  };

  if (price) {
    if (price.from) {
      operator.compound.filter.push({
        range: { gte: price.from, path: "pricing.price" },
      });
    }
    if (price.to) {
      operator.compound.filter.push({
        range: { lte: price.to, path: "pricing.price" },
      });
    }
  }

  if (isPartner) {
    operator.compound.filter.push({
      equals: { value: true, path: "isPartner" },
    });
  }
  if (!includeOutdated) {
    operator.compound.filter.push({
      range: { gte: now, path: "validThrough" },
    });
  }
  if (markets) {
    operator.compound.filter.push({ text: { query: markets, path: "market" } });
  }
  if (dealers) {
    operator.compound.filter.push({
      text: { query: dealers, path: "dealer" },
    });
  }
  if (brands) {
    operator.compound.filter.push({
      text: { query: brands, path: "brandKey" },
    });
  }
  if (vendors) {
    operator.compound.filter.push({
      text: { query: vendors, path: "vendorKey" },
    });
  }
  if (productCollections && !isExtraOffers) {
    operator.compound.filter.push({
      text: { query: productCollections, path: "siteCollection" },
    });
  }
  if (categories) {
    operator.compound.filter.push({
      text: { query: categories, path: "mpnCategories.key" },
    });
  }

  if (query && !sort) {
    operator.compound.must.push({
      text: {
        path: ["title", "subtitle", "brand"],
        query,
      },
    });
    operator.compound.should.push({
      text: {
        path: ["title"],
        query,
        score: { boost: { value: 3 } },
      },
    });
    operator.compound.should.push({
      text: {
        path: ["subtitle", "brand", "categories", "mpnCategories"],
        query,
        score: { boost: { value: 1.5 } },
      },
    });
    if (isExtraOffers) {
      const siteCollection = get(productCollections, [0]);
      if (siteCollection) {
        operator.compound.should.push({
          text: {
            path: "siteCollection",
            query: siteCollection,
            score: { boost: { value: 1.5 } },
          },
        });
      }
      operator.compound.should.push({
        equals: {
          path: "isPartner",
          value: true,
          score: { boost: { value: 1.5 } },
        },
      });
    }
    // Attempt to make search more restrictive (AND) after selecting sort
  } else if (query && sort) {
    query
      .split(" ")
      .map((x) => x.trim())
      .forEach((x) => {
        operator.compound.must.push({
          text: {
            path: ["title", "subtitle", "brand", "categories", "mpnCategories"],
            query: x,
          },
        });
      });
  }

  if (sort) {
    operator.compound.should.push({
      near: {
        path: Object.keys(sort)[0],
        origin: Object.values(sort)[0] === 1 ? -1e3 : 1e6 * 1,
        pivot: 2,
        score: { boost: { value: Number.MAX_SAFE_INTEGER } },
      },
    });
  }

  const aggregationPipeline: Record<string, any>[] = [
    {
      $search: {
        ...operator,
      },
    },
    { $limit: Math.min(limit, 1000) }, // Will be incredibly slow when sorting if the results are many
    { $skip: (Math.max(page - 1, 0) || 0) * limit },
    {
      $project: {
        ...projection,
        score: { $meta: "searchScore" },
      },
    },
    {
      $facet: {
        items: [{ $limit: limit }],
        meta: [{ $replaceWith: "$$SEARCH_META" }, { $limit: 1 }],
      },
    },
    { $unwind: "$meta" },
    {
      $set: {
        dealerKeys: {
          $map: {
            input: "$items",
            as: "t",
            in: "$$t.dealer",
          },
        },
      },
    },
    {
      $lookup: {
        from: "dealers",
        localField: "dealerKeys",
        foreignField: "key",
        as: "dealers",
        pipeline: [{ $project: defaultDealerProjection }],
      },
    },
  ];

  const mongoSearchResponse = await offerCollection
    .aggregate(aggregationPipeline)
    .toArray();

  if (!mongoSearchResponse[0]?.items.length) {
    return {
      items: [],
      meta: { count: 0, page: 1 },
    };
  }

  const meta: MpnMongoSearchResponseMeta = {
    count: mongoSearchResponse[0].meta.count.lowerBound,
    page,
  };

  const result = {
    items: mongoSearchResponse[0].items,
    meta,
  };

  const dealerMap = {};
  mongoSearchResponse[0].dealers.forEach((x) => {
    dealerMap[x.key] = x;
  });
  result.items = result.items.map((x) => {
    x.dealerObject = dealerMap[x.dealer] || { key: x.dealer };
    return x;
  });

  return result;
};

export const searchWithElastic = async ({
  query,
  engineName,
  limit = 32,
  page = 1,
  dealers,
  categories,
  price,
  sort,
  boosts,
  precision = 4,
}: {
  query: string;
  engineName: string;
  limit?: number;
  page?: number;
  dealers?: string[];
  categories?: string[];
  price?: { from?: number; to?: number };
  sort?: { [key: string]: "desc" | "asc" };
  boosts?: AppSearchOfferBoosts;
  precision?: number;
}): Promise<{ items: MpnResultOffer[]; facets: any; meta: any }> => {
  const elasticClient = await getElasticClient();
  if (query.length > 127) {
    const message = `Query ${query} is too long (${query.length} characters). Max is 128.`;
    console.error(message);
    throw new APIError({
      status: 500,
      message,
    });
  }
  const now = getNowDate();
  const filters: { all: Record<string, any>[] } = {
    all: [{ valid_through: { from: now } }],
  };

  if (dealers) {
    filters.all.push({ dealer: dealers });
  }
  if (categories) {
    filters.all.push({ mpn_categories: categories });
  }

  if (price) {
    filters.all.push({ price });
  }

  const facets: { dealer: any; brand: any; mpn_categories?: any } = {
    dealer: [
      {
        type: "value",
      },
    ],
    brand: [
      {
        type: "value",
      },
    ],
  };
  if (engineName.startsWith("groceryoffers")) {
    facets.mpn_categories = [
      {
        type: "value",
      },
    ];
  }
  const searchOptions: AppSearchParams = {
    page: { size: limit, current: page },
    precision,
    filters,
    facets,
  };

  if (sort) {
    searchOptions.sort = sort;
  }
  if (boosts) {
    searchOptions.boosts = boosts;
  }

  const searchResponse = await elasticClient.search<ElasticMpnOfferRaw>(
    engineName,
    query,
    searchOptions,
  );

  try {
    const mpnResults = searchResponse.results.map((x) => {
      return elasticOfferToMpnOffer(x);
    });

    // Filter offers that only exist in Elastic and not in Mongo
    const resultUris = mpnResults.map((x) => x.uri);
    const urisFromMongoSet = new Set(
      (await getOffersByUris(resultUris, null, { uri: 1 })).map((x) => x.uri),
    );

    const validOffers = mpnResults.filter((x) => urisFromMongoSet.has(x.uri));

    return {
      facets: searchResponse.facets,
      meta: searchResponse.meta,
      items: validOffers,
    };
  } catch (e) {
    console.error(e);
    throw new APIError({
      status: 500,
      message: `Could not search for ${query}`,
    });
  }
};

export const querySuggestion = async (query, engineName): Promise<string[]> => {
  if (query.length > 127) {
    const message = `Query ${query} is too long (${query.length} characters). Max is 128.`;
    console.error(message);
    throw new APIError({
      status: 500,
      message,
    });
  }
  const elasticClient = await getElasticClient();
  const searchResponse = await elasticClient.querySuggestion(engineName, query);

  return searchResponse.results.documents.map(({ suggestion }) => suggestion);
};

export const registerClick = async (
  registerClickArgs,
  engineName,
): Promise<void> => {
  const elasticClient = await getElasticClient();
  const searchResponse = await elasticClient.client.post(
    `engines/${encodeURIComponent(engineName)}/click`,
    registerClickArgs,
  );
  return;
};

export type MongoSearchParamsRelations = {
  query: string;
  productCollections?: string[];
  market: string;
  limit?: number;
  page?: number;
  dealers?: string[];
  categories?: string[];
  brands?: string[];
  vendors?: string[];
  price?: { from?: number; to?: number };
  sort?: { [key: string]: 1 | -1 };
  isPartner?: boolean;
  isExtraOffers?: boolean;
  includeOutdated?: boolean;
  projection?: Record<string, number | boolean | Record<number, boolean>>;
};
export type MongoSearchParamsRelationsExtra = {
  title: string;
  mustProductCollections?: string[];
  mustCategories?: string[];
  mustBrands?: string[];
  productCollections?: string[];
  market: string;
  limit?: number;
  page?: number;
  dealers?: string[];
  categories?: string[];
  brands?: string[];
  vendors?: string[];
  price?: { from?: number; to?: number };
  sort?: { [key: string]: 1 | -1 };
  isPartner?: boolean;
  projection?: Record<string, number | boolean | Record<number, boolean>>;
  offerUri: string;
};

export const searchWithMongoRelations = async ({
  query,
  productCollections,
  market,
  limit = 32,
  page = 1,
  dealers,
  categories,
  brands,
  vendors,
  price,
  sort,
  isPartner = false,
  isExtraOffers = false,
  includeOutdated = false,
  projection = defaultOfferProjection,
}: MongoSearchParamsRelations): Promise<MpnMongoSearchResponse> => {
  if (query.length > 127) {
    const message = `Query ${query} is too long (${query.length} characters). Max is 128.`;
    console.error(message);
    throw new APIError({
      status: 500,
      message,
    });
  }
  const now = getNowDate();
  const _limit = Math.min(limit, 64);

  const searchCollection = await getCollection(
    `relations_with_offers_${market}`,
  );

  const facets: Record<string, { type: string; path: string }> = {
    dealersFacet: {
      type: "string",
      path: "offers.dealerKey",
    },
  };

  const operator = {
    compound: {
      filter: [{ text: { path: "relationType", query: "identical" } }],
      must: [],
      should: [],
    },
  };

  if (price) {
    if (price.from) {
      operator.compound.filter.push({
        range: { gte: price.from, path: "priceMin" },
      });
    }
    if (price.to) {
      operator.compound.filter.push({
        range: { lte: price.to, path: "priceMin" },
      });
    }
  }

  if (isPartner) {
    operator.compound.filter.push({
      equals: { value: true, path: "offers.isPartner" },
    });
  }
  if (!includeOutdated && false) {
    operator.compound.filter.push({
      range: { gte: now, path: "offers.validThrough" },
    });
  }
  /*if (market) {
    operator.compound.filter.push({
      text: { query: market, path: "offers.market" },
    });
  }*/
  if (dealers) {
    operator.compound.filter.push({
      text: { query: dealers, path: "offers.dealerKey" },
    });
  }
  if (brands) {
    operator.compound.filter.push({
      text: { query: brands, path: "brandKey" },
    });
  }
  if (vendors) {
    operator.compound.filter.push({
      text: { query: vendors, path: "offers.vendorKey" },
    });
  }
  if (productCollections && !isExtraOffers) {
    operator.compound.filter.push({
      text: { query: productCollections, path: "offers.siteCollection" },
    });
  }
  if (categories) {
    operator.compound.filter.push({
      text: { query: categories, path: "mpnCategories.key" },
    });
  }
  if (isExtraOffers) {
    const siteCollection = get(productCollections, [0]);
    if (siteCollection) {
      operator.compound.should.push({
        text: {
          path: "offers.siteCollection",
          query: siteCollection,
          score: { boost: { value: 1.5 } },
        },
      });
    }
    operator.compound.should.push({
      equals: {
        path: "offers.isPartner",
        value: true,
        score: { boost: { value: 1.5 } },
      },
    });
    operator.compound.should.push({
      moreLikeThis: {
        like: [{ title: query }],
      },
    });
  } else if (query && !sort) {
    operator.compound.must.push({
      text: {
        path: ["title", "subtitle", "brand"],
        query,
      },
    });
    operator.compound.should.push({
      text: {
        path: ["title"],
        query,
        score: { boost: { value: 3 } },
      },
    });
    operator.compound.should.push({
      text: {
        path: ["subtitle", "brand", "offers.categories", "mpnCategories"],
        query,
        score: { boost: { value: 1.5 } },
      },
    });

    // Attempt to make search more restrictive (AND) after selecting sort
  } else if (query && sort) {
    query
      .split(" ")
      .map((x) => x.trim())
      .forEach((x) => {
        operator.compound.must.push({
          text: {
            path: [
              "title",
              "subtitle",
              "brand",
              "offers.categories",
              "mpnCategories",
            ],
            query: x,
          },
        });
      });
  }

  if (sort) {
    const path = Object.keys(sort)[0];
    operator.compound.should.push({
      near: {
        path,
        origin: Object.values(sort)[0] === 1 ? -1e3 : 1e6 * 1,
        pivot: 2,
        score: { boost: { value: Number.MAX_SAFE_INTEGER } },
      },
    });
  }

  console.log("operator");
  console.log(JSON.stringify(operator, null, 2));

  const aggregationPipeline: Record<string, any>[] = [
    {
      $search: {
        facet: {
          operator,
          facets,
        },
      },
    },
    { $skip: (Math.max(page - 1, 0) || 0) * _limit },
    { $limit: _limit }, // Will be incredibly slow when sorting if the results are many
    {
      $project: {
        ...projection,
        score: { $meta: "searchScore" },
        offers: 1,
        priceMin: 1,
        priceMax: 1,
        valueMin: 1,
        valueMax: 1,
        pageviews: 1,
      },
    },

    {
      $facet: {
        items: [{ $limit: _limit }],
        meta: [{ $replaceWith: "$$SEARCH_META" }, { $limit: 1 }],
      },
    },
    { $unwind: "$meta" },
    {
      $set: {
        dealerKeys: {
          $map: {
            input: "$meta.facet.dealersFacet.buckets",
            as: "t",
            in: "$$t._id",
          },
        },
      },
    },
    {
      $lookup: {
        from: "dealers",
        localField: "dealerKeys",
        foreignField: "key",
        as: "dealers",
        pipeline: [
          { $match: { market } },
          { $project: defaultDealerProjection },
        ],
      },
    },
  ];

  const mongoSearchResponse = await searchCollection
    .aggregate(aggregationPipeline)
    .toArray();

  if (!mongoSearchResponse[0]?.items.length) {
    return {
      items: [],
      meta: { count: 0, page: 1, pageSize: _limit, pageCount: 1 },
      facets: { dealersFacet: { buckets: [] } },
    };
  }

  const meta: MpnMongoSearchResponseMeta = {
    count: mongoSearchResponse[0].meta.count.lowerBound,
    page,
  };

  const result = {
    items: mongoSearchResponse[0].items,
    meta: {
      ...meta,
      pageSize: _limit,
      pageCount: Math.ceil(meta.count / _limit),
    },
    facets: { ...mongoSearchResponse[0].meta.facet },
  };

  const dealerMap = {};
  mongoSearchResponse[0].dealers.forEach((x) => {
    dealerMap[x.key] = x;
  });

  result.items.forEach((rel) => {
    rel.offers.forEach((x) => {
      x.dealerObject = dealerMap[x.dealerKey] || { key: x.dealerKey };
    });
  });
  result.facets.dealersFacet.buckets = result.facets.dealersFacet.buckets
    .map((x) => {
      return {
        ...(dealerMap[x._id] || { key: x._id, _id: x._id }),
        ...x,
      };
    })
    .filter((x) => x.market === market);

  return result;
};
export const searchWithMongoRelationsExtra = async ({
  title,
  productCollections,
  mustProductCollections,
  mustCategories,
  mustBrands,
  market,
  limit = 8,
  page = 1,
  dealers,
  categories,
  brands,
  vendors,
  price,
  isPartner = false,
  projection = defaultOfferProjection,
  offerUri,
}: MongoSearchParamsRelationsExtra): Promise<MpnMongoSearchResponse> => {
  const now = getNowDate();
  const _limit = Math.min(limit, 64);

  const searchCollection = await getCollection(
    `relations_with_offers_${market}`,
  );

  const facets: Record<string, { type: string; path: string }> = {
    dealersFacet: {
      type: "string",
      path: "offers.dealerKey",
    },
  };

  const operator = {
    compound: {
      filter: [{ text: { path: "relationType", query: "identical" } }],
      must: [],
      should: [
        {
          moreLikeThis: {
            like: [{ title, score: { boost: { value: 2 } } }],
          },
        },
      ],
    },
  };

  if (productCollections) {
    operator.compound.should.push({
      moreLikeThis: {
        like: {
          "offers.siteCollection": productCollections,
          score: { boost: { value: 0.6 } },
        },
      },
    });
  }
  if (categories) {
    operator.compound.should.push({
      moreLikeThis: {
        like: {
          "mpnCategories.key": categories,
          score: { boost: { value: 0.6 } },
        },
      },
    });
  }
  if (brands) {
    operator.compound.should.push({
      moreLikeThis: {
        like: { brandKey: brands, score: { boost: { value: 0.3 } } },
      },
    });
  }

  if (price) {
    if (price.from) {
      operator.compound.filter.push({
        range: { gte: price.from, path: "priceMin" },
      });
    }
    if (price.to) {
      operator.compound.filter.push({
        range: { lte: price.to, path: "priceMin" },
      });
    }
  }
  if (isPartner) {
    operator.compound.filter.push({
      equals: { value: true, path: "offers.isPartner" },
    });
  }
  if (dealers) {
    operator.compound.filter.push({
      text: { query: dealers, path: "offers.dealerKey" },
    });
  }
  if (mustBrands) {
    operator.compound.filter.push({
      text: { query: mustBrands, path: "brandKey" },
    });
  }
  if (vendors) {
    operator.compound.filter.push({
      text: { query: vendors, path: "offers.vendorKey" },
    });
  }
  if (mustProductCollections) {
    operator.compound.filter.push({
      text: { query: mustProductCollections, path: "offers.siteCollection" },
    });
  }
  if (mustCategories) {
    operator.compound.filter.push({
      text: { query: mustCategories, path: "mpnCategories.key" },
    });
  }

  operator.compound.should.push({
    equals: {
      path: "offers.isPartner",
      value: true,
      score: { boost: { value: 1.2 } },
    },
  });

  const aggregationPipeline: Record<string, any>[] = [
    {
      $search: {
        facet: {
          operator,
          facets,
        },
      },
    },
    { $match: { offerSet: { $ne: offerUri } } },
    { $skip: (Math.max(page - 1, 0) || 0) * _limit },
    { $limit: _limit }, // Will be incredibly slow when sorting if the results are many
    {
      $project: {
        ...projection,
        score: { $meta: "searchScore" },
        offers: 1,
        priceMin: 1,
        priceMax: 1,
        valueMin: 1,
        valueMax: 1,
        pageviews: 1,
      },
    },

    {
      $facet: {
        items: [{ $limit: _limit }],
        meta: [{ $replaceWith: "$$SEARCH_META" }, { $limit: 1 }],
      },
    },
    { $unwind: "$meta" },
    {
      $set: {
        dealerKeys: {
          $map: {
            input: "$meta.facet.dealersFacet.buckets",
            as: "t",
            in: "$$t._id",
          },
        },
      },
    },
    {
      $lookup: {
        from: "dealers",
        localField: "dealerKeys",
        foreignField: "key",
        as: "dealers",
        pipeline: [
          { $match: { market } },
          { $project: defaultDealerProjection },
        ],
      },
    },
  ];

  const mongoSearchResponse = await searchCollection
    .aggregate(aggregationPipeline)
    .toArray();

  if (!mongoSearchResponse[0]?.items.length) {
    return {
      items: [],
      meta: { count: 0, page: 1, pageSize: _limit, pageCount: 1 },
      facets: { dealersFacet: { buckets: [] } },
    };
  }

  const meta: MpnMongoSearchResponseMeta = {
    count: mongoSearchResponse[0].meta.count.lowerBound,
    page,
  };

  const result = {
    items: mongoSearchResponse[0].items,
    meta: {
      ...meta,
      pageSize: _limit,
      pageCount: Math.ceil(meta.count / _limit),
    },
    facets: { ...mongoSearchResponse[0].meta.facet },
  };

  const dealerMap = {};
  mongoSearchResponse[0].dealers.forEach((x) => {
    dealerMap[x.key] = x;
  });

  result.items.forEach((rel) => {
    rel.offers.forEach((x) => {
      x.dealerObject = dealerMap[x.dealerKey] || { key: x.dealerKey };
    });
  });
  result.facets.dealersFacet.buckets = result.facets.dealersFacet.buckets
    .map((x) => {
      return {
        ...(dealerMap[x._id] || { key: x._id, _id: x._id }),
        ...x,
      };
    })
    .filter((x) => x.market === market);

  return result;
};
