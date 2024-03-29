import {
  defaultDealerProjection,
  defaultOfferProjection,
} from "@/api/models/mpnOffer.model";
import { getNowDate } from "../utils/helpers";
import { getCollection } from "@/config/mongo";
import { get } from "lodash";
import { ObjectId } from "mongodb";

export type MongoSearchParams = {
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

export const searchWithMongo = async ({
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
}: MongoSearchParams): Promise<MpnMongoSearchResponse> => {
  const _query = (query || "").trim().substring(0, 128);
  const now = getNowDate();
  const _limit = Math.min(limit, 1000);
  const offerCollection = await getCollection(`mpnoffers_${market}`);

  const facets: Record<string, { type: string; path: string }> = {
    dealersFacet: {
      type: "string",
      path: "dealerKey",
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
  if (dealers) {
    operator.compound.filter.push({
      text: { query: dealers, path: "dealerKey" },
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

  if (_query && !sort) {
    operator.compound.must.push({
      text: {
        path: ["title", "subtitle", "brand"],
        query: _query,
      },
    });
    operator.compound.should.push({
      text: {
        path: ["title"],
        query: _query,
        score: { boost: { value: 3 } },
      },
    });
    operator.compound.should.push({
      text: {
        path: ["subtitle", "brand", "categories", "mpnCategories"],
        query: _query,
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
  } else if (_query && sort) {
    _query
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
  const searchConfig = {
    facet: {
      operator,
      facets,
    },
  };
  if (sort && !sort.score) {
    searchConfig.sort = sort;
    searchConfig.facet.operator.compound.filter.push({
      exists: { path: Object.keys(sort)[0] },
    });
  }

  const aggregationPipeline: Record<string, any>[] = [
    {
      $search: searchConfig,
    },
    { $limit: _limit }, // Will be incredibly slow when sorting if the results are many
    { $skip: (Math.max(page - 1, 0) || 0) * _limit },
    {
      $project: {
        ...projection,
        score: { $meta: "searchScore" },
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
      meta: { count: 0, page: 1, pageCount: 1, pageSize: _limit },
      facets: { dealersFacet: { buckets: [] } },
    };
  }

  const itemCount = mongoSearchResponse[0].meta.count.lowerBound;
  const meta: MpnMongoSearchResponseMeta = {
    count: itemCount,
    page,
    pageSize: _limit,
    pageCount: Math.ceil(itemCount / _limit),
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
    x.dealerObject = dealerMap[x.dealerKey] || {
      key: x.dealerKey,
    };
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
}: MongoSearchParams): Promise<Omit<MpnMongoSearchResponse, "facets">> => {
  const _query = (query || "").trim().substring(0, 128);
  const now = getNowDate();
  const offerCollection = await getCollection(`mpnoffers_${market}`);
  const _limit = Math.min(limit, 1000);

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
  if (dealers) {
    operator.compound.filter.push({
      text: { query: dealers, path: "dealerKey" },
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

  if (_query && !sort) {
    operator.compound.must.push({
      text: {
        path: ["title", "subtitle", "brand"],
        query: _query,
      },
    });
    operator.compound.should.push({
      text: {
        path: ["title"],
        query: _query,
        score: { boost: { value: 3 } },
      },
    });
    operator.compound.should.push({
      text: {
        path: ["subtitle", "brand", "categories", "mpnCategories"],
        query: _query,
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
  } else if (_query && sort) {
    _query
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
  const searchConfig = {
    ...operator,
  };
  if (sort && !sort.score) {
    searchConfig.sort = sort;
    searchConfig.compound.filter.push({
      exists: { path: Object.keys(sort)[0] },
    });
  }

  const aggregationPipeline: Record<string, any>[] = [
    {
      $search: searchConfig,
    },
    { $limit: _limit }, // Will be incredibly slow when sorting if the results are many
    { $skip: (Math.max(page - 1, 0) || 0) * _limit },
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
            in: "$$t.dealerKey",
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
      meta: { count: 0, page: 1, pageCount: 1, pageSize: _limit },
    };
  }

  const itemCount = mongoSearchResponse[0].meta.count.lowerBound;
  const meta: MpnMongoSearchResponseMeta = {
    count: itemCount,
    page,
    pageSize: _limit,
    pageCount: Math.ceil(itemCount / _limit),
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
    x.dealerObject = dealerMap[x.dealerKey] || {
      key: x.dealerKey,
    };
    return x;
  });

  return result;
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
  value?: { from?: number; to?: number };
  proteins?: { from?: number; to?: number };
  carbs?: { from?: number; to?: number };
  fats?: { from?: number; to?: number };
  kcals?: { from?: number; to?: number };
  processedScore?: { from?: number; to?: number };
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
  offerUri?: string;
  relationId?: string;
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
  value,
  proteins,
  carbs,
  fats,
  kcals,
  processedScore,
  sort,
  isPartner = false,
  isExtraOffers = false,
  includeOutdated = false,
  projection = defaultOfferProjection,
}: MongoSearchParamsRelations): Promise<MpnMongoRelationsSearchResponse> => {
  const _query = (query || "").trim().substring(0, 128);
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
  if (value) {
    if (value.from) {
      operator.compound.filter.push({
        range: { gte: value.from, path: "valueMin" },
      });
    }
    if (value.to) {
      operator.compound.filter.push({
        range: { lte: value.to, path: "valueMin" },
      });
    }
  }
  if (proteins) {
    if (proteins.from) {
      operator.compound.filter.push({
        range: { gte: proteins.from, path: "mpnNutrition.proteins.value" },
      });
    }
    if (proteins.to) {
      operator.compound.filter.push({
        range: { lte: proteins.to, path: "mpnNutrition.proteins.value" },
      });
    }
  }
  if (kcals) {
    if (kcals.from) {
      operator.compound.filter.push({
        range: { gte: kcals.from, path: "mpnNutrition.energyKcal.value" },
      });
    }
    if (kcals.to) {
      operator.compound.filter.push({
        range: { lte: kcals.to, path: "mpnNutrition.energyKcal.value" },
      });
    }
  }
  if (fats) {
    if (fats.from) {
      operator.compound.filter.push({
        range: { gte: fats.from, path: "mpnNutrition.fats.value" },
      });
    }
    if (fats.to) {
      operator.compound.filter.push({
        range: { lte: fats.to, path: "mpnNutrition.fats.value" },
      });
    }
  }
  if (carbs) {
    if (carbs.from) {
      operator.compound.filter.push({
        range: { gte: carbs.from, path: "mpnNutrition.carbohydrates.value" },
      });
    }
    if (carbs.to) {
      operator.compound.filter.push({
        range: { lte: carbs.to, path: "mpnNutrition.carbohydrates.value" },
      });
    }
  }
  if (processedScore) {
    if (processedScore.from) {
      operator.compound.filter.push({
        range: {
          gte: processedScore.from,
          path: "mpnIngredients.processedScore",
        },
      });
    }
    if (processedScore.to) {
      operator.compound.filter.push({
        range: {
          lte: processedScore.to,
          path: "mpnIngredients.processedScore",
        },
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
        like: [{ title: _query }],
      },
    });
  } else if (_query && !sort) {
    operator.compound.must.push({
      text: {
        path: ["title", "subtitle", "brand", "mpnCategories.name"],
        query: _query,
      },
    });
    operator.compound.should.push({
      text: {
        path: ["title"],
        query: _query,
        score: { boost: { value: 3 } },
      },
    });
    operator.compound.should.push({
      text: {
        path: ["subtitle", "brand", "offers.categories", "mpnCategories.name"],
        query: _query,
        score: { boost: { value: 1.5 } },
      },
    });

    // Attempt to make search more restrictive (AND) after selecting sort
  } else if (_query && sort) {
    _query
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
              "mpnCategories.name",
            ],
            query: x,
          },
        });
      });
  }
  const searchConfig = {
    facet: {
      operator,
      facets,
    },
  };
  if (sort && !sort.score) {
    searchConfig.sort = sort;
    searchConfig.facet.operator.compound.filter.push({
      exists: { path: Object.keys(sort)[0] },
    });
  }

  const aggregationPipeline: Record<string, any>[] = [
    {
      $search: searchConfig,
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

  const itemCount = mongoSearchResponse[0].meta.count.lowerBound;
  const meta: MpnMongoSearchResponseMeta = {
    count: itemCount,
    page,
    pageSize: _limit,
    pageCount: Math.ceil(itemCount / _limit),
  };

  const result = {
    items: mongoSearchResponse[0].items,
    meta,
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
export const searchWithMongoRelationsNoFacets = async ({
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
}: MongoSearchParamsRelations): Promise<
  Omit<MpnMongoRelationsSearchResponse, "facets">
> => {
  const _query = (query || "").trim().substring(0, 128);
  const now = getNowDate();
  const _limit = Math.min(limit, 64);

  const searchCollection = await getCollection(
    `relations_with_offers_${market}`,
  );

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
        like: [{ title: _query }],
      },
    });
  } else if (_query && !sort) {
    operator.compound.must.push({
      text: {
        path: ["title", "subtitle", "brand"],
        query: _query,
      },
    });
    operator.compound.should.push({
      text: {
        path: ["title"],
        query: _query,
        score: { boost: { value: 3 } },
      },
    });
    operator.compound.should.push({
      text: {
        path: ["subtitle", "brand", "offers.categories", "mpnCategories"],
        query: _query,
        score: { boost: { value: 1.5 } },
      },
    });

    // Attempt to make search more restrictive (AND) after selecting sort
  } else if (_query && sort) {
    _query
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
  const searchConfig = {
    ...operator,
  };
  if (sort && !sort.score) {
    searchConfig.sort = sort;
    searchConfig.compound.filter.push({
      exists: { path: Object.keys(sort)[0] },
    });
  }

  const aggregationPipeline: Record<string, any>[] = [
    {
      $search: searchConfig,
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
          $reduce: {
            initialValue: [],
            input: "$items.offers.dealerKey",
            in: {
              $setUnion: {
                $concatArrays: ["$$value", "$$this"],
              },
            },
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

  const mongoSearchResponse = await searchCollection
    .aggregate(aggregationPipeline)
    .toArray();

  if (!mongoSearchResponse[0]?.items.length) {
    return {
      items: [],
      meta: { count: 0, page: 1, pageSize: _limit, pageCount: 1 },
    };
  }

  const itemCount = mongoSearchResponse[0].meta.count.lowerBound;
  const meta: MpnMongoSearchResponseMeta = {
    count: itemCount,
    page,
    pageSize: _limit,
    pageCount: Math.ceil(itemCount / _limit),
  };
  const result = {
    items: mongoSearchResponse[0].items,
    meta,
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
  relationId,
}: MongoSearchParamsRelationsExtra): Promise<
  Omit<MpnMongoRelationsSearchResponse, "facets">
> => {
  const now = getNowDate();
  const _limit = Math.min(limit, 64);

  const searchCollection = await getCollection(
    `relations_with_offers_${market}`,
  );

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

  const relationsMatch = {};
  if (offerUri) {
    relationsMatch.offerSet = { $ne: offerUri };
  }
  if (relationId) {
    relationsMatch._id = { $ne: new ObjectId(relationId) };
  }

  const searchConfig = {
    ...operator,
  };

  const aggregationPipeline: Record<string, any>[] = [
    {
      $search: searchConfig,
    },
    { $match: relationsMatch },
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
          $reduce: {
            initialValue: [],
            input: "$items.offers.dealerKey",
            in: {
              $setUnion: {
                $concatArrays: ["$$value", "$$this"],
              },
            },
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

  const mongoSearchResponse = await searchCollection
    .aggregate(aggregationPipeline)
    .toArray();

  if (!mongoSearchResponse[0]?.items.length) {
    return {
      items: [],
      meta: { count: 0, page: 1, pageSize: _limit, pageCount: 1 },
    };
  }

  const itemCount = mongoSearchResponse[0].meta.count.lowerBound;
  const meta: MpnMongoSearchResponseMeta = {
    count: itemCount,
    page,
    pageSize: _limit,
    pageCount: Math.ceil(itemCount / _limit),
  };
  const result = {
    items: mongoSearchResponse[0].items,
    meta,
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

  return result;
};
