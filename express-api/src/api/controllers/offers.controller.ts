import _, { take } from "lodash";
import * as t from "io-ts";
import { Parser, Response, Route, route } from "typera-express";
import {
  addDealerToOffers,
  addPricingToOffers,
  addTagToOffers,
  filterIdenticalOffers,
  findOne,
  findOneFull,
  findSimilarPromoted,
  getOfferUrisForTags,
  getSimilarGroupedOffersFromOfferUris,
  getTagsForOffer,
  removeTagFromOffers,
} from "@/api/services/offers";
import {
  searchWithElastic,
  searchWithMongo,
  MongoSearchParams,
} from "@/api/services/search";
import { defaultOfferProjection } from "../models/mpnOffer.model";
import { getDaysAhead, getNowDate } from "../utils/helpers";
import { getEngineName } from "@/api/controllers/search.controller";
import { indexDocuments } from "../services/elastic";
import { getCollection } from "@/config/mongo";
import { getOfferBiRelations } from "../services/offer-relations";
import { getBoolean, getStringList } from "./request-param-parsing";
import { Filter } from "mongodb";
import { offerCollectionName } from "../utils/constants";
import {
  getLimitFromQueryParam,
  limitQueryParams,
  marketQueryParams,
  productCollectionAndLimitQueryParams,
  productCollectionQueryParams,
} from "./typera-types";
import { getQuantityObject, getValueObject } from "../utils/quantity";
import {
  getPricingHistory,
  getPricingHistoryV2,
} from "../services/pricing-history";
import { addDays } from "date-fns";

const offersQueryParams = t.type({
  productCollection: t.string,
  tags: t.union([t.string, t.undefined]),
  limit: t.union([t.string, t.undefined]),
  category: t.union([t.string, t.undefined]),
  dealer: t.union([t.string, t.undefined]),
});

interface ListOffersResponse {
  items: MpnOffer[];
}

export const list: Route<
  Response.Ok<ListOffersResponse> | Response.BadRequest<string>
> = route
  .get("/")
  .use(Parser.query(offersQueryParams))
  .handler(async (request) => {
    const { productCollection, tags, limit, category, dealer } = request.query;

    let _limit = getLimitFromQueryParam(limit, 32, 128);

    const selection: Filter<FullMpnOffer> = {
      siteCollection: productCollection,
    };
    if (tags) {
      selection.uri = { $in: await getOfferUrisForTags(getStringList(tags)) };
    }
    if (category) {
      selection["mpnCategories.key"] = category;
    }
    if (dealer) {
      selection.dealer = dealer;
    }

    const now = getNowDate();
    selection.validThrough = { $gte: now };

    const offerCollection = await getCollection(offerCollectionName);

    const offers = await offerCollection
      .find(selection)
      .project<MpnOffer>(defaultOfferProjection)
      .sort({ pageviews: -1, url_fingerprint: 1 })
      .limit(_limit)
      .toArray();

    const result = await addDealerToOffers({ offers });

    return Response.ok({ items: result });
  });

export const addToElastic: Route<
  Response.NoContent | Response.NotFound<string> | Response.BadRequest<string>
> = route
  .put("/elastic/:id")
  .use(Parser.query(productCollectionQueryParams))
  .handler(async (request) => {
    const { productCollection } = request.query;

    let offer: FullMpnOffer;
    try {
      offer = await findOneFull(request.routeParams.id);
      if (!offer) {
        throw new Error();
      }
    } catch (e) {
      return Response.notFound(
        `Could not find offer with id ${request.routeParams.id}`,
      );
    }
    const indexResult = await indexDocuments(
      [offer],
      getEngineName(productCollection),
    );
    return Response.noContent();
  });

const similarHandler = async (request) => {
  const { productCollection, market } = request.query;
  const useSearch = getBoolean(request.query.useSearch);

  const offersCollection = await getCollection(offerCollectionName);

  let offer: FullMpnOffer;
  try {
    offer = await findOneFull(request.routeParams.id);
    if (!offer) {
      throw new Error();
    }
  } catch (e) {
    return Response.notFound(
      `Could not find offer with id ${request.routeParams.id}`,
    );
  }

  const offerHasSimilarOffers =
    offer.similarOffers && offer.similarOffers.length > 0;

  if (!offerHasSimilarOffers) {
    const mongoSearchResponse = await searchWithMongo({
      query: offer.title.substring(0, 127),
      productCollections: [productCollection],
      markets: [market],
      limit: 32,
    });
    const resultWithDealer = await addDealerToOffers({
      offers: mongoSearchResponse.items,
    });
    return Response.ok(resultWithDealer);
  }

  const now = getNowDate();
  const similarOffersUris = offer.similarOffers.map((x) => x.uri);
  const pipeline = [
    {
      $match: {
        _id: { $ne: offer._id },
        uri: { $in: similarOffersUris },
        validThrough: { $gte: now },
      },
    },
    {
      $addFields: { __order: { $indexOfArray: [similarOffersUris, "$uri"] } },
    },
    { $sort: { __order: 1 } },
    {
      $project: defaultOfferProjection,
    },
  ];
  const similarOffers = await offersCollection
    .aggregate<MpnOffer>(pipeline)
    .toArray();

  if (similarOffers.length === 0) {
    console.warn(
      `Offer ${request.routeParams.id} did not have any time valid similar offers.`,
    );
    const mongoSearchResponse = await searchWithMongo({
      query: offer.title.substring(0, 127),
      productCollections: [productCollection],
      markets: [market],
      limit: 32,
    });
    const resultWithDealer = await addDealerToOffers({
      offers: mongoSearchResponse.items,
    });
    return Response.ok(resultWithDealer);
  }
  const result = similarOffers.map((x, i) => ({
    ...x,
    score: offer.similarOffers[i].score,
  }));
  const resultWithDealer = await addDealerToOffers({ offers: result });
  return Response.ok(resultWithDealer);
};

const similarHandlerV1 = async (request) => {
  const { productCollection } = request.query;
  const useSearch = getBoolean(request.query.useSearch);

  const offersCollection = await getCollection(offerCollectionName);

  let offer: FullMpnOffer;
  try {
    offer = await findOneFull(request.routeParams.id);
    if (!offer) {
      throw new Error();
    }
  } catch (e) {
    return Response.notFound(
      `Could not find offer with id ${request.routeParams.id}`,
    );
  }

  const offerHasSimilarOffers =
    offer.similarOffers && offer.similarOffers.length > 0;

  if (!offerHasSimilarOffers) {
    console.warn(
      `Offer ${request.routeParams.id} did not have any similar offers.`,
    );
  }

  //if (useSearch === true || !offerHasSimilarOffers) {
  if (!offerHasSimilarOffers) {
    const elasticResponse = await searchWithElastic({
      query: offer.title.substring(0, 127),
      engineName: getEngineName(productCollection),
      limit: 32,
    });
    const resultWithDealer = await addDealerToOffers({
      offers: elasticResponse.items,
    });
    return Response.ok(resultWithDealer);
  }

  const now = getNowDate();
  const similarOffersUris = offer.similarOffers.map((x) => x.uri);
  const pipeline = [
    {
      $match: {
        _id: { $ne: offer._id },
        uri: { $in: similarOffersUris },
        validThrough: { $gte: now },
      },
    },
    {
      $addFields: { __order: { $indexOfArray: [similarOffersUris, "$uri"] } },
    },
    { $sort: { __order: 1 } },
    {
      $project: defaultOfferProjection,
    },
  ];
  const similarOffers = await offersCollection
    .aggregate<MpnOffer>(pipeline)
    .toArray();

  if (similarOffers.length === 0) {
    console.warn(
      `Offer ${request.routeParams.id} did not have any time valid similar offers.`,
    );
    const result = await searchWithElastic({
      query: offer.title.substring(0, 127),
      engineName: getEngineName(productCollection),
      limit: 32,
    });
    const resultWithDealer = await addDealerToOffers({ offers: result });
    return Response.ok(resultWithDealer);
  }
  const result = similarOffers.map((x, i) => ({
    ...x,
    score: offer.similarOffers[i].score,
  }));
  const resultWithDealer = await addDealerToOffers({ offers: result });
  return Response.ok(resultWithDealer);
};

const similarOffersQueryParams = t.type({
  productCollection: t.string,
  useSearch: t.union([t.string, t.undefined]),
  market: t.union([t.string, t.undefined]),
  limit: t.union([t.string, t.undefined]),
});

export const similar: Route<
  | Response.Ok<MpnOffer[]>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route
  .get("/similar/:id")
  .use(Parser.query(similarOffersQueryParams))
  .handler(similarHandler);

const similarPromotedOffersQueryParams = t.type({
  market: t.union([t.string, t.undefined]),
  limit: t.union([t.string, t.undefined]),
});

export const similarPromoted: Route<
  | Response.Ok<MpnOffer[]>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route
  .get("/similar/promoted/:id")
  .use(Parser.query(similarPromotedOffersQueryParams))
  .handler(async (request) => {
    const { market, limit } = request.query;
    const _limit = getLimitFromQueryParam(limit, 2);
    const result = await findSimilarPromoted({
      limit: _limit,
      market,
      uri: request.routeParams.id,
    });
    return Response.ok(result);
  });
export const similarEnd: Route<
  | Response.Ok<MpnOffer[]>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route
  .get("/:id/similar")
  .use(Parser.query(similarOffersQueryParams))
  .handler(similarHandler);
export const similarV1: Route<
  | Response.Ok<MpnOffer[]>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route
  .get("/similar/:id")
  .use(Parser.query(similarOffersQueryParams))
  .handler(similarHandlerV1);
export const similarEndV1: Route<
  | Response.Ok<MpnOffer[]>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route
  .get("/:id/similar")
  .use(Parser.query(similarOffersQueryParams))
  .handler(similarHandlerV1);

const extraOffersQueryParams = t.type({
  productCollection: t.union([t.string, t.undefined]),
  limit: t.union([t.string, t.undefined]),
  market: t.string,
});

export const extra: Route<
  | Response.Ok<MpnResultOffer[]>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route
  .get("/extra/:id")
  .use(Parser.query(extraOffersQueryParams))
  .handler(async (request) => {
    const { limit, productCollection, market } = request.query;
    let _limit = getLimitFromQueryParam(limit, 5);

    let offer: FullMpnOffer;
    try {
      offer = await findOneFull(request.routeParams.id);
      if (!offer) {
        throw new Error();
      }
    } catch (e) {
      return Response.notFound(
        `Could not find offer with id ${request.routeParams.id}`,
      );
    }

    let query = offer.title;
    if (offer.categories && Array.isArray(offer.categories)) {
      query += ` ${offer.categories.join(" ")}`;
    }

    query = query.substring(0, 127);

    const searchParams: MongoSearchParams = {
      query,
      markets: [market],
      limit: _limit,
      isExtraOffers: true,
    };

    if (productCollection) {
      searchParams.productCollections = [productCollection];
    }

    const searchResults = await searchWithMongo(searchParams);
    searchResults.items = searchResults.items.filter((x) => x.score > 1);
    searchResults.items = filterIdenticalOffers({
      offers: searchResults.items,
      excludeUris: [offer.uri],
    });
    searchResults.items = await addDealerToOffers({
      offers: searchResults.items,
    });

    return Response.ok(searchResults.items);
  });
export const extraV1: Route<
  | Response.Ok<MpnResultOffer[]>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route
  .get("/extra/:id")
  .use(Parser.query(extraOffersQueryParams))
  .handler(async (request) => {
    const { limit, productCollection, market } = request.query;
    let _limit = getLimitFromQueryParam(limit, 5);

    const engineName = getEngineName(`${market}-mpn-offers`);

    let offer: FullMpnOffer;
    try {
      offer = await findOneFull(request.routeParams.id);
      if (!offer) {
        throw new Error();
      }
    } catch (e) {
      return Response.notFound(
        `Could not find offer with id ${request.routeParams.id}`,
      );
    }

    const query = offer.title.substring(0, 127);

    const boosts: AppSearchOfferBoosts = {
      is_partner: [
        {
          type: "value",
          value: "true",
          operation: "multiply",
          factor: 1.6,
        },
      ],
    };

    if (productCollection) {
      boosts.site_collection = [
        {
          type: "value",
          value: productCollection,
          operation: "multiply",
          factor: 1.4,
        },
      ];
    }

    const searchResults = await searchWithElastic({
      query,
      engineName,
      limit: _limit,
      boosts,
      precision: 2,
    });
    searchResults.items = searchResults.items.filter(
      (offer) => offer.score > 1,
    );
    searchResults.items = await addDealerToOffers({
      offers: searchResults.items,
    });

    return Response.ok(searchResults.items);
  });

export const similarExtra: Route<
  | Response.Ok<MpnResultOffer[]>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route
  .get("/similarextra/:id")
  .use(Parser.query(limitQueryParams))
  .handler(async (request) => {
    const { limit } = request.query;

    let _limit = getLimitFromQueryParam(limit, 5);

    let offer: FullMpnOffer;
    try {
      offer = await findOneFull(request.routeParams.id);
      if (!offer) {
        throw new Error();
      }
    } catch (e) {
      return Response.notFound(
        `Could not find offer with id ${request.routeParams.id}`,
      );
    }

    const query = offer.title.substring(0, 127);

    const searchResults = await searchWithElastic({
      query,
      engineName: "extraoffers",
      limit: _limit,
    });

    const filteredOffers = searchResults.items.filter(
      (offer) => offer.score > 20,
    );
    const offersWithDealer = await addDealerToOffers({
      offers: filteredOffers,
    });

    return Response.ok(offersWithDealer);
  });

const similarFromExtraOffersQueryParams = t.type({
  limit: t.union([t.string, t.undefined]),
  productCollection: t.string,
});

export const similarFromExtra: Route<
  | Response.Ok<MpnResultOffer[]>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route
  .get("/similarfromextra/:id")
  .use(Parser.query(similarFromExtraOffersQueryParams))
  .handler(async (request) => {
    const { limit, productCollection } = request.query;
    const _limit = getLimitFromQueryParam(limit, 5);

    let offer: FullMpnOffer;
    try {
      offer = await findOneFull(request.routeParams.id);
      if (!offer) {
        throw new Error();
      }
    } catch (e) {
      return Response.notFound(
        `Could not find offer with id ${request.routeParams.id}`,
      );
    }

    const query = offer.title.substring(0, 127);

    const searchResults = await searchWithElastic({
      query,
      engineName: getEngineName(productCollection),
      limit: _limit,
    });

    const filteredOffers = searchResults.items.filter(
      (offer) => offer.score > 10,
    );
    const offersWithDealer = await addDealerToOffers({
      offers: filteredOffers,
    });

    return Response.ok(offersWithDealer);
  });

export const promoted: Route<
  Response.Ok<MpnOffer[]> | Response.BadRequest<string>
> = route
  .get("/promoted")
  .use(Parser.query(productCollectionAndLimitQueryParams))
  .handler(async (request) => {
    const { limit, productCollection } = request.query;

    let _limit = getLimitFromQueryParam(limit, 32);
    const offerCollection = await getCollection(offerCollectionName);
    const now = getNowDate();

    /*const promotedOfferUris = await getOfferUrisForTags(["promoted"]);

    const selection: Record<string, any> = {
      uri: { $in: promotedOfferUris },
      validThrough: { $gte: now },
      siteCollection: productCollection,
    };

    
    const promotedOffers = await offerCollection
    .find(selection)
    .project<MpnOffer>({
      ...defaultOfferProjection,
        isPromotionRestricted: 1,
      })
      .limit(_limit)
      .toArray();*/

    const promotedOffers = [];

    const result = [...promotedOffers];

    if (promotedOffers.length < _limit) {
      const extraOffers = await offerCollection
        .find({
          validThrough: { $gte: now },
          siteCollection: productCollection,
        })
        .project<MpnOffer>({
          ...defaultOfferProjection,
          isPromotionRestricted: 1,
        })
        .sort({ pageviews: -1 })
        .limit(_limit - promotedOffers.length)
        .toArray();
      result.push(...extraOffers);
    }

    const limitedResult = _.take(result, _limit).filter(
      // Filter this on server to avoid creating index
      (x) => x.isPromotionRestricted !== true,
    );
    const dealerResult = await addDealerToOffers({ offers: limitedResult });
    return Response.ok(dealerResult);
  });

export const find: Route<
  | Response.Ok<MpnOffer>
  | Response.NotFound<string>
  | Response.BadRequest<string>
> = route.get("/:id").handler(async (request) => {
  try {
    const offer = await findOne(request.routeParams.id);
    if (!offer) {
      throw new Error(`Could not find offer with id ${request.routeParams.id}`);
    }
    return Response.ok(offer);
  } catch (e) {
    return Response.notFound(
      `Could not find offer with id ${request.routeParams.id}`,
    );
  }
});

export const findByGtin: Route<
  Response.Ok<{ items: MpnOffer[] }> | Response.BadRequest<string>
> = route
  .get("/gtin/:gtin")
  .use(Parser.query(marketQueryParams))
  .handler(async (request) => {
    const offerCollection = await getCollection(offerCollectionName);
    const offers = await offerCollection
      .find({
        $or: [
          { "gtins.ean": request.routeParams.gtin },
          { "gtins.gtin12": request.routeParams.gtin },
          { "gtins.gtin13": request.routeParams.gtin },
          { "gtins.nobb": request.routeParams.gtin },
          { "gtins.isbn": request.routeParams.gtin },
        ],
      })
      .project<MpnOffer>(defaultOfferProjection)
      .toArray();
    const offersWithDealer = await addDealerToOffers({ offers });
    const responseData = {
      items: offersWithDealer,
      market: "",
      title: "",
      description: "",
      shortDescription: "",
      subtitle: "",
      imageUrl: "",
    };
    if (request.query.market) {
      responseData.market = request.query.market;
    }
    const mainOffer =
      offersWithDealer.find((x) => x.market === request.query.market) ||
      offersWithDealer.find(() => true);
    responseData.title = mainOffer.title;
    responseData.description = mainOffer.description;
    responseData.subtitle = mainOffer.subtitle;
    responseData.imageUrl = mainOffer.imageUrl;
    return Response.ok(responseData);
  });

export const relatedOffers: Route<
  | Response.Ok<{ identical: MpnOffer[]; interchangeable: MpnOffer[] }>
  | Response.NotFound
  | Response.BadRequest<string>
> = route
  .get("/:id/related")
  .use(Parser.query(marketQueryParams))
  .handler(async (request) => {
    const offerCollection = await getCollection(offerCollectionName);

    const now = new Date();

    try {
      const relationResults = await getOfferBiRelations(request.routeParams.id);
      const identicalUris = _.get(
        relationResults,
        ["identical", "offerSet"],
        [],
      ).filter((x) => x !== request.routeParams.id);
      const interchangeableUris = _.get(
        relationResults,
        ["interchangeable", "offerSet"],
        [],
      ).filter((x) => x !== request.routeParams.id);
      const offerFilter: Filter<OfferInstance> = {
        uri: { $in: [...identicalUris, ...interchangeableUris] },
        validThrough: { $gt: now },
      };
      if (request.query.market) {
        offerFilter.market = request.query.market;
      }
      const offers = await offerCollection
        .find(offerFilter)
        .project<MpnOffer>(defaultOfferProjection)
        .toArray();

      const offersWithDealer = await addDealerToOffers({ offers });

      return Response.ok({
        identical: offersWithDealer.filter((offer) =>
          identicalUris.includes(offer.uri),
        ),
        interchangeable: offersWithDealer.filter((offer) =>
          interchangeableUris.includes(offer.uri),
        ),
      });
    } catch (e) {
      return Response.notFound();
    }
  });

const addTagToOffersBody = t.type({
  offerUris: t.array(t.string),
  tag: t.string,
});

export const postAddTagToOffers: Route<
  Response.NoContent<any> | Response.BadRequest<string>
> = route
  .post("/tags")
  .use(Parser.body(addTagToOffersBody))
  .handler(async (request) => {
    if (request.body.offerUris.length === 0) {
      return Response.badRequest("Need at least on offer uri.");
    }
    return Response.noContent(
      await addTagToOffers(request.body.offerUris, request.body.tag),
    );
  });
export const putRemoveTagFromOffers: Route<
  Response.NoContent<any> | Response.BadRequest<string>
> = route
  .put("/tags/remove")
  .use(Parser.body(addTagToOffersBody))
  .handler(async (request) => {
    if (request.body.offerUris.length === 0) {
      return Response.badRequest("Need at least on offer uri.");
    }
    return Response.noContent(
      await removeTagFromOffers(request.body.offerUris, request.body.tag),
    );
  });

export const getTagsForOfferHandler: Route<
  Response.Ok<OfferTag[]> | Response.BadRequest<string>
> = route.get("/:id/tags").handler(async (request) => {
  return Response.ok(await getTagsForOffer(request.routeParams.id));
});

const putQuantityPutBody = t.type({
  uri: t.string,
  quantityValue: t.number,
  quantityUnit: t.string,
});

export const putOfferQuantity: Route<
  Response.Ok | Response.NotFound<string> | Response.BadRequest<string>
> = route
  .put("/quantity")
  .use(Parser.body(putQuantityPutBody))
  .handler(async (request) => {
    const offerCollection = await getCollection(offerCollectionName);
    const offerMetaCollection = await getCollection("offermeta");
    const offer: MpnMongoOffer = await offerCollection.findOne<MpnMongoOffer>({
      uri: request.body.uri,
    });
    if (!offer) {
      return Response.notFound(`Not found offer with uri: ${request.body.uri}`);
    }
    const size = getQuantityObject({
      quantityUnit: request.body.quantityUnit,
      quantityValue: request.body.quantityValue,
    });
    const sizeValue = getValueObject({
      price: offer.pricing.price,
      quantity: size,
    });
    const quantityObject = {
      size,
      pieces: offer.quantity.pieces,
    };
    const valueObject = { size: sizeValue, pieces: offer.value.pieces };
    const offerMongoResponse = await offerCollection.updateOne(
      { uri: request.body.uri },
      {
        $set: {
          quantity: quantityObject,
          value: valueObject,
        },
      },
    );
    const offerMetaMongoResponse = await offerMetaCollection.updateOne(
      { uri: request.body.uri },
      {
        $set: {
          "manual.quantityString": {
            value: `${request.body.quantityValue}${request.body.quantityUnit}`,
            key: "quantityString",
            updatedAt: getNowDate(),
          },
        },
      },
    );

    return Response.ok();
  });

const offerGroupsQueryParams = t.type({
  tags: t.string,
  limit: t.union([t.string, t.undefined]),
  market: t.union([t.string, t.undefined]),
  productCollection: t.union([t.string, t.undefined]),
});

export const getOfferGroups: Route<
  Response.Ok<ListResponse<SimilarOffersObject>> | Response.BadRequest<string>
> = route
  .get("/offer-groups")
  .use(Parser.query(offerGroupsQueryParams))
  .handler(async (request) => {
    const { tags, limit, market, productCollection } = request.query;

    if (!tags) {
      return Response.badRequest("Need at least one tag to get offer groups.");
    }

    let offerUris = [];

    const offerFilter: Record<string, string> = {};
    if (market) {
      offerFilter.market = market;
    }
    if (productCollection) {
      offerFilter.siteCollection = productCollection;
    }
    offerUris = await getOfferUrisForTags(
      tags.split(","),
      limit ? Number.parseInt(limit) : undefined,
    );

    return Response.ok({
      items: await getSimilarGroupedOffersFromOfferUris(
        offerUris,
        offerFilter,
        {
          relationType: { $in: ["identical", "identicaldifferentsize"] },
        },
      ),
    });
  });

export const offerPricingHistory: Route<
  Response.Ok<object> | Response.NotFound | Response.BadRequest<string>
> = route.get("/:id/pricing").handler(async (request) => {
  const offer = await findOne(request.routeParams.id);

  if (!offer) {
    return Response.notFound();
  }

  const pricingObjects = await getPricingHistory({ uri: offer.uri });

  return Response.ok(pricingObjects);
});
export const offerPricingHistoryV2: Route<
  Response.Ok<object> | Response.NotFound | Response.BadRequest<string>
> = route.get("/:id/pricing").handler(async (request) => {
  const offerPricingHistoryCollection = await getCollection(
    "offerpricinghistories",
  );
  const pricingHistory = await offerPricingHistoryCollection.findOne({
    uri: request.routeParams.id,
  });
  if (!pricingHistory) {
    return Response.notFound();
  }

  const pricingObjects = getPricingHistoryV2({
    pricingHistory,
    endDate: addDays(pricingHistory.updatedAt, 7),
  });

  return Response.ok(pricingObjects);
});

const priceDifferencesQueryParams = t.type({
  direction: t.union([t.string, t.undefined]),
  namespaces: t.union([t.string, t.undefined]),
  categories: t.union([t.string, t.undefined]),
  productCollection: t.union([t.string, t.undefined]),
  limit: t.union([t.string, t.undefined]),
  daysPast: t.union([t.string, t.undefined]),
});

export const offersWithPriceDifference: Route<
  Response.Ok<object[]> | Response.BadRequest<string>
> = route
  .get("/pricedifferences")
  .use(Parser.query(priceDifferencesQueryParams))
  .handler(async (request) => {
    const direction = request.query.direction || "desc";
    const categories = request.query.categories || "";
    const limit = request.query.limit;
    let _limit = getLimitFromQueryParam(limit, 32, 128);

    const sortDirection = direction === "desc" ? -1 : 1;
    const categoriesArray = categories.split(",").filter((x) => !!x);

    const before7Days = getDaysAhead(-7);

    const offerPricingCollection = await getCollection("offerpricinghistories");

    const filter: Record<string, any> = {
      updatedAt: { $gt: before7Days },
      siteCollection: request.query.productCollection || "groceryoffers",
    };

    let differenceField = "difference";
    let differencePercentageField = "differencePercentage";

    switch (request.query.daysPast) {
      case "7":
        differenceField = "difference7DaysMean";
        differencePercentageField = "difference7DaysMeanPercentage";
        break;
      case "30":
        differenceField = "difference30DaysMean";
        differencePercentageField = "difference30DaysMeanPercentage";
        break;
      case "90":
        differenceField = "difference90DaysMean";
        differencePercentageField = "difference90DaysMeanPercentage";
        break;
      case "365":
        differenceField = "difference365DaysMean";
        differencePercentageField = "difference365DaysMeanPercentage";
        break;
      default:
        break;
    }

    if (direction === "desc") {
      filter[differencePercentageField] = {
        $gt: 10,
      };
    } else {
      filter[differencePercentageField] = {
        $lt: -10,
      };
    }

    const sort = { [differencePercentageField]: sortDirection };

    const pricingLimit = categoriesArray.length > 0 ? 1024 : _limit;

    const pricingObjects: OfferPricingHistory[] = await offerPricingCollection
      .find(filter)
      .project({
        uri: 1,
        difference: 1,
        differencePercentage: 1,
        difference7DaysMean: 1,
        difference7DaysMeanPercentage: 1,
        difference30DaysMean: 1,
        difference30DaysMeanPercentage: 1,
        difference90DaysMean: 1,
        difference90DaysMeanPercentage: 1,
        difference365DaysMean: 1,
        difference365DaysMeanPercentage: 1,
      })
      .sort(sort)
      .limit(pricingLimit)
      .toArray();

    const pricingMap = {};

    pricingObjects.forEach((x) => {
      pricingMap[x.uri] = x;
    });

    const offerLimit = pricingObjects.length;
    const offerCollection = await getCollection(offerCollectionName);
    const offerSelection = {
      uri: { $in: take(pricingObjects, offerLimit).map((x) => x.uri) },
    };
    if (categoriesArray.length > 0) {
      offerSelection["mpnCategories.key"] = { $in: categoriesArray };
    }

    const offers = await offerCollection
      .find(offerSelection)
      .project(defaultOfferProjection)
      .limit(offerLimit)
      .toArray();

    if (offers.length === 0) {
      return Response.ok([]);
    }

    const offersWithDealer = await addDealerToOffers({ offers });

    const offersMap = {};
    offersWithDealer.map((x) => {
      offersMap[x.uri] = x;
    });

    const result = pricingObjects
      .filter((x) => Object.keys(offersMap).includes(x.uri))
      .map((x) => ({ ...offersMap[x.uri], pricingHistoryObject: x }));

    return Response.ok(take(result, _limit));
  });

const detailedOffersQueryParams = t.type({
  uris: t.string,
});

export const getDetailedOffers: Route<
  Response.Ok<ListOffersResponse> | Response.BadRequest<string>
> = route
  .get("/detailed")
  .use(Parser.query(detailedOffersQueryParams))
  .handler(async (request) => {
    const uris = request.query.uris.split(",");

    const selection: Filter<FullMpnOffer> = {
      uri: { $in: uris },
    };

    const now = getNowDate();
    selection.validThrough = { $gte: now };

    const offerCollection = await getCollection(offerCollectionName);

    const offers = await offerCollection
      .find(selection)
      .project<MpnOffer>(defaultOfferProjection)
      .toArray();

    const offersWithDealer = await addDealerToOffers({ offers });
    const offersWithPricing = await addPricingToOffers({
      offers: offersWithDealer,
    });

    return Response.ok({ items: offersWithPricing });
  });
