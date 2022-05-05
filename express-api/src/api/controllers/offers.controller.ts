import _, { sortBy } from "lodash";
import * as t from "io-ts";
import { Parser, Response, Route, route } from "typera-express";
import {
  addDealerToOffers,
  addTagToOffers,
  findOne,
  findOneFull,
  getOfferUrisForTags,
  getSimilarGroupedOffersFromOfferUris,
  getTagsForOffer,
  removeTagFromOffers,
} from "@/api/services/offers";
import { searchWithElastic, searchWithMongo } from "@/api/services/search";
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
import { getPricingHistory } from "../services/pricing-history";

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
    console.warn(
      `Offer ${request.routeParams.id} did not have any similar offers.`,
    );
  }

  //if (useSearch === true || !offerHasSimilarOffers) {
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
});

export const similar: Route<
  | Response.Ok<MpnOffer[]>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route
  .get("/similar/:id")
  .use(Parser.query(similarOffersQueryParams))
  .handler(similarHandler);
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

    const query = offer.title.substring(0, 127);

    const searchResults = await searchWithMongo({
      query,
      markets: [market],
      limit: _limit,
    });
    searchResults.items = searchResults.items.filter(
      (offer) => offer.score > 1,
    );
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

    const promotedOfferUris = await getOfferUrisForTags(["promoted"]);

    const now = getNowDate();
    const selection: Record<string, any> = {
      validThrough: { $gte: now },
      uri: { $in: promotedOfferUris },
      siteCollection: productCollection,
      isPromotionRestricted: { $ne: true },
    };

    const offerCollection = await getCollection(offerCollectionName);

    const promotedOffers = await offerCollection
      .find(selection)
      .project<MpnOffer>(defaultOfferProjection)
      .limit(_limit)
      .toArray();

    const result = [...promotedOffers];

    if (promotedOffers.length < _limit) {
      const extraOffers = await offerCollection
        .find({
          validThrough: { $gte: now },
          siteCollection: productCollection,
          isPromotionRestricted: { $ne: true },
        })
        .project<MpnOffer>(defaultOfferProjection)
        .sort({ pageviews: -1 })
        .limit(_limit - promotedOffers.length)
        .toArray();
      result.push(...extraOffers);
    }

    const limitedResult = _.take(result, _limit);
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
    const mongoResponse = await offerCollection.updateOne(
      { uri: request.body.uri },
      {
        $set: {
          "meta.quantity.manual": {
            value: quantityObject,
            updated: getNowDate(),
          },
          quantity: quantityObject,
          value: valueObject,
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

const priceDifferencesQueryParams = t.type({
  direction: t.union([t.string, t.undefined]),
  namespaces: t.union([t.string, t.undefined]),
  categories: t.union([t.string, t.undefined]),
  limit: t.union([t.string, t.undefined]),
});

export const offersWithPriceDifference: Route<
  Response.Ok<object[]> | Response.BadRequest<string>
> = route
  .get("/pricedifferences")
  .use(Parser.query(priceDifferencesQueryParams))
  .handler(async (request) => {
    const direction = request.query.direction || "desc";
    const namespaces = request.query.namespaces || "kolonial,meny,coop";
    const categories = request.query.categories || "";
    const limit = request.query.limit;
    let _limit = getLimitFromQueryParam(limit, 32, 128);

    const sortDirection = direction === "desc" ? -1 : 1;
    const namespacesArray = namespaces.split(",");
    const categoriesArray = categories.split(",").filter((x) => !!x);

    const before8Days = getDaysAhead(-8);

    const offerPricingCollection = await getCollection("offerpricings");
    const pricingObjects = await offerPricingCollection
      .find({
        date: { $gt: before8Days.toISOString().substring(0, 10) }, // YYYY-MM-DD
        difference: { $exists: 1 },
        uri: { $regex: `^(${namespacesArray.join("|")})\:` },
      })
      .sort({ difference: sortDirection })
      .limit(1024)
      .toArray();

    const pricingMap = {};

    pricingObjects.forEach((x) => {
      pricingMap[x.uri] = x;
    });

    const offerCollection = await getCollection(offerCollectionName);
    const offerSelection = {
      uri: { $in: Object.keys(pricingMap) },
    };
    if (categoriesArray.length > 0) {
      offerSelection["mpnCategories.key"] = { $in: categoriesArray };
    }
    console.log("categoriesArray");
    console.log(categoriesArray);
    console.log("Object.keys(pricingMap)");
    console.log(Object.keys(pricingMap));
    const offers = await offerCollection
      .find(offerSelection)
      .project(defaultOfferProjection)
      .limit(_limit)
      .toArray();

    let result = await addDealerToOffers({ offers });

    result = result.map((x) => {
      return { ...x, pricingHistoryObject: pricingMap[x.uri] };
    });

    result = sortBy(
      result,
      (x) => x.pricingHistoryObject.difference * sortDirection,
    );

    return Response.ok(result);
  });
