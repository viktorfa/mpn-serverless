import _, { take, get, pick } from "lodash";
import * as t from "io-ts";
import { Parser, Response, Route, route } from "typera-express";
import {
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
  MongoSearchParams,
  searchWithMongoNoFacets,
} from "@/api/services/search";
import { defaultOfferProjection } from "../models/mpnOffer.model";
import { getDaysAhead, getNowDate } from "../utils/helpers";
import { getEngineName } from "@/api/controllers/search.controller";
import { indexDocuments } from "../services/elastic";
import { getCollection } from "@/config/mongo";
import { getOfferBiRelations } from "../services/offer-relations";
import { getBoolean, getStringList } from "./request-param-parsing";
import { Filter } from "mongodb";
import {
  offerBiRelationsCollectionName,
  offerCollectionName,
} from "../utils/constants";
import {
  getLimitFromQueryParam,
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
    selection.isRecent = true;

    const offerCollection = await getCollection("mpnoffers_with_context");

    const offers = await offerCollection
      .find(selection)
      .project<MpnOffer>(defaultOfferProjection)
      .sort({ pageviews: -1 })
      .limit(_limit)
      .toArray();

    return Response.ok({ items: offers });
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
    const mongoSearchResponse = await searchWithMongoNoFacets({
      query: offer.title.substring(0, 127),
      productCollections: [productCollection],
      markets: [market],
      limit: 32,
    });

    return Response.ok(mongoSearchResponse.items);
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
  const offersCollection = await getCollection("mpnoffers_with_context");
  const similarOffers = await offersCollection
    .aggregate<MpnOffer>(pipeline)
    .toArray();

  if (similarOffers.length === 0) {
    console.warn(
      `Offer ${request.routeParams.id} did not have any time valid similar offers.`,
    );
    const mongoSearchResponse = await searchWithMongoNoFacets({
      query: offer.title.substring(0, 127),
      productCollections: [productCollection],
      markets: [market],
      limit: 32,
    });

    return Response.ok(mongoSearchResponse.items);
  }
  const result = similarOffers.map((x, i) => ({
    ...x,
    score: offer.similarOffers[i].score,
  }));
  return Response.ok(result);
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
    if (false && offer.categories && Array.isArray(offer.categories)) {
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

    const searchResults = await searchWithMongoNoFacets(searchParams);
    searchResults.items = searchResults.items.filter((x) => x.score > 1);
    searchResults.items = filterIdenticalOffers({
      offers: searchResults.items,
      excludeUris: [offer.uri],
    });

    return Response.ok(searchResults.items);
  });

export const promoted: Route<
  Response.Ok<MpnOffer[]> | Response.BadRequest<string>
> = route
  .get("/promoted")
  .use(Parser.query(productCollectionAndLimitQueryParams))
  .handler(async (request) => {
    const { limit, productCollection } = request.query;

    let _limit = getLimitFromQueryParam(limit, 32);

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
      const extraOffers = await searchWithMongoNoFacets({
        query: "",
        productCollections: [productCollection],
        limit: _limit - promotedOffers.length,
        sort: { pageviews: -1 },
        projection: { ...defaultOfferProjection, isPromotionRestricted: 1 },
      });

      /*const extraOffers = await offerCollection
        .find({
          isRecent: true,
          validThrough: { $gte: now },
          siteCollection: productCollection,
        })
        .project<MpnOffer>({
          ...defaultOfferProjection,
          isPromotionRestricted: 1,
        })
        .sort({ pageviews: -1 })
        .limit(_limit - promotedOffers.length)
        .toArray();*/

      result.push(...extraOffers.items);
    }

    const limitedResult = _.take(result, _limit).filter(
      // Filter this on server to avoid creating index
      (x) => x.isPromotionRestricted !== true,
    );

    return Response.ok(limitedResult);
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
export const findV2: Route<
  | Response.Ok<MpnOffer>
  | Response.NotFound<string>
  | Response.BadRequest<string>
> = route
  .get("/:id")
  .use(Parser.query(t.type({ market: t.string })))
  .handler(async (request) => {
    const { market } = request.query;
    try {
      const offerCollection = await getCollection("mpnoffers_with_context");
      const offerRelations = await offerCollection
        .aggregate([
          { $match: { uri: request.routeParams.id } },
          { $limit: 1 },
          { $project: defaultOfferProjection },
          {
            $lookup: {
              from: offerBiRelationsCollectionName,
              localField: "uri",
              foreignField: "offerSet",
              as: "identical",
              pipeline: [
                {
                  $match: {
                    relationType: "identical",
                    isMerged: { $ne: true },
                  },
                },
                {
                  $lookup: {
                    from: "mpnoffers_with_context",
                    localField: "offerSet",
                    foreignField: "uri",
                    as: "offers",
                    pipeline: [
                      {
                        $match: {
                          isRecent: true,
                          validThrough: { $gt: new Date() },
                          market,
                          uri: { $ne: request.routeParams.id },
                        },
                      },
                      { $project: defaultOfferProjection },
                    ],
                  },
                },
              ],
            },
          },
          {
            $lookup: {
              from: "offerbirelations",
              localField: "uri",
              foreignField: "offerSet",
              as: "interchangeable",
              pipeline: [
                {
                  $match: {
                    relationType: "interchangeable",
                    isMerged: { $ne: true },
                  },
                },
                {
                  $lookup: {
                    from: "mpnoffers_with_context",
                    localField: "offerSet",
                    foreignField: "uri",
                    as: "offers",
                    pipeline: [
                      {
                        $match: {
                          isRecent: true,
                          validThrough: { $gt: new Date() },
                          market,
                          uri: { $ne: request.routeParams.id },
                        },
                      },
                      { $project: defaultOfferProjection },
                    ],
                  },
                },
              ],
            },
          },
          {
            $unwind: {
              path: "$identical",
              preserveNullAndEmptyArrays: true,
            },
          },
          {
            $unwind: {
              path: "$interchangeable",
              preserveNullAndEmptyArrays: true,
            },
          },
        ])
        .toArray();

      const offerRelation = offerRelations[0];

      if (!offerRelation) {
        return Response.notFound(
          `Could not find offer with id ${request.routeParams.id}`,
        );
      }

      const identical = offerRelation.identical?.offers || [];
      const interchangeable = offerRelation.interchangeable?.offers || [];

      const marketData = get(offerRelation, ["identical", `m:${market}`]);
      const relCategories = get(marketData, ["mpnCategories"]);
      const relNutrition = get(offerRelation, ["identical", "mpnNutrition"]);
      const relIngredients = get(offerRelation, [
        "identical",
        "mpnIngredients",
      ]);
      const relProperties = get(offerRelation, ["identical", "mpnProperties"]);

      offerRelation.mpnCategories = relCategories;
      offerRelation.mpnNutrition = relNutrition;
      offerRelation.mpnIngredients = relIngredients;
      offerRelation.mpnProperties = relProperties;

      delete offerRelation.identical;
      delete offerRelation.interchangeable;
      return Response.ok({ offer: offerRelation, identical, interchangeable });
    } catch (e) {
      console.error(e);
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
    const offerCollection = await getCollection("mpnoffers_with_context");
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
    const responseData = {
      items: offers,
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
      offers.find((x) => x.market === request.query.market) ||
      offers.find(() => true);
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
    const offerCollection = await getCollection("mpnoffers_with_context");

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

      return Response.ok({
        identical: offers.filter((offer) => identicalUris.includes(offer.uri)),
        interchangeable: offers.filter((offer) =>
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
  dealers: t.union([t.string, t.undefined]),
  categories: t.union([t.string, t.undefined]),
  productCollection: t.union([t.string, t.undefined]),
  limit: t.union([t.string, t.undefined]),
  daysPast: t.union([t.string, t.undefined]),
  market: t.string,
});

export const offersWithPriceDifference: Route<
  Response.Ok<object[]> | Response.BadRequest<string>
> = route
  .get("/pricedifferences")
  .use(Parser.query(priceDifferencesQueryParams))
  .handler(async (request) => {
    const direction = request.query.direction || "desc";
    const categories = request.query.categories || "";
    const dealers = request.query.dealers || "";
    const limit = request.query.limit;
    let _limit = getLimitFromQueryParam(limit, 32, 128);

    const sortDirection = direction === "desc" ? -1 : 1;
    const categoriesArray = categories.split(",").filter((x) => !!x);
    const dealersArray = dealers.split(",").filter((x) => !!x);

    let differenceField = "difference7DaysMean";
    let differencePercentageField = "difference7DaysMeanPercentage";

    // Only index 7 and 90 days
    switch (request.query.daysPast) {
      case "7":
        differenceField = "difference7DaysMean";
        differencePercentageField = "difference7DaysMeanPercentage";
        break;
      //case "30":
      //  differenceField = "difference30DaysMean";
      //  differencePercentageField = "difference30DaysMeanPercentage";
      //  break;
      case "90":
        differenceField = "difference90DaysMean";
        differencePercentageField = "difference90DaysMeanPercentage";
        break;
      //case "365":
      //  differenceField = "difference365DaysMean";
      //  differencePercentageField = "difference365DaysMeanPercentage";
      //  break;
      default:
        break;
    }

    const searchResponse = await searchWithMongoNoFacets({
      query: "",
      markets: [request.query.market],
      productCollections: [request.query.productCollection],
      sort: { [differencePercentageField]: sortDirection },
      limit: _limit,
      categories: categories ? categoriesArray : undefined,
      dealers: dealers ? dealersArray : undefined,
      projection: {
        ...defaultOfferProjection,
        difference7DaysMeanPercentage: 1,
        difference7DaysMean: 1,
        difference90DaysMeanPercentage: 1,
        difference90DaysMean: 1,
      },
    });

    return Response.ok(
      searchResponse.items
        .filter((x) => !!x[differencePercentageField])
        .map((x) => ({
          ...x,
          pricingHistoryObject: pick(x, [
            "difference7DaysMeanPercentage",
            "difference7DaysMean",
            "difference90DaysMeanPercentage",
            "difference90DaysMean",
          ]),
        })),
    );

    const before7Days = getDaysAhead(-7);

    const offerPricingCollection = await getCollection("offerpricinghistories");

    const filter: Record<string, any> = {
      updatedAt: { $gt: before7Days },
      siteCollection: request.query.productCollection || "groceryoffers",
    };

    if (dealersArray.length > 0) {
      filter.uri = { $regex: new RegExp(`^(${dealersArray.join("|")})`) };
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
    const offerCollection = await getCollection("mpnoffers_with_context");
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

    const offersMap = {};
    offers.map((x) => {
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

    const offerCollection = await getCollection("mpnoffers_with_context");

    const offers = await offerCollection
      .find(selection)
      .project<MpnOffer>(defaultOfferProjection)
      .toArray();

    const offersWithPricing = await addPricingToOffers({
      offers,
    });

    return Response.ok({ items: offersWithPricing });
  });
