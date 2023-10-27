import _, { take, get, pick } from "lodash";
import * as t from "io-ts";
import { Parser, Response, Route, route } from "typera-express";
import {
  addPricingToOffers,
  addTagToOffers,
  filterIdenticalOffers,
  findOne,
  findOneFull,
  getOfferUrisForTags,
  getSimilarGroupedOffersFromOfferUris,
  getTagsForOffer,
  removeTagFromOffers,
} from "@/api/services/offers";
import {
  MongoSearchParams,
  MongoSearchParamsRelations,
  MongoSearchParamsRelationsExtra,
  searchWithMongoNoFacets,
  searchWithMongoRelations,
  searchWithMongoRelationsExtra,
} from "@/api/services/search";
import { defaultOfferProjection } from "../models/mpnOffer.model";
import { getDaysAhead, getNowDate } from "../utils/helpers";
import { getCollection } from "@/config/mongo";
import { getStringList } from "./request-param-parsing";
import { Filter } from "mongodb";
import {
  offerBiRelationsCollectionName,
  offerCollectionName,
} from "../utils/constants";
import {
  getLimitFromQueryParam,
  productCollectionAndLimitQueryParams,
} from "./typera-types";
import { getQuantityObject, getValueObject } from "../utils/quantity";
import {
  getPricingHistory,
  getPricingHistoryV2,
} from "../services/pricing-history";
import { addDays } from "date-fns";
import { getDealersForMarket } from "../utils/dealers";

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

const extraOffersQueryParams = t.type({
  productCollection: t.union([t.string, t.undefined]),
  limit: t.union([t.string, t.undefined]),
  market: t.string,
  categories: t.union([t.string, t.undefined]),
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
      market: market,
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
export const extraRelations: Route<
  | Response.Ok<Omit<MpnMongoRelationsSearchResponse, "facets">>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route
  .get("/extrarelations/:id")
  .use(Parser.query(extraOffersQueryParams))
  .handler(async (request) => {
    const { limit, productCollection, market, categories } = request.query;
    let _limit = getLimitFromQueryParam(limit, 5);

    const offer = await findOne(request.routeParams.id);
    if (!offer) {
      return Response.notFound(
        `Could not find offer with id ${request.routeParams.id}`,
      );
    }

    const searchParams: MongoSearchParamsRelationsExtra = {
      title: offer.title.substring(0, 127),
      market: market,
      limit: _limit,
      offerUri: offer.uri,
    };

    if (productCollection) {
      searchParams.productCollections = [productCollection];
    }
    if (offer.mpnCategories?.length > 0) {
      searchParams.categories = offer.mpnCategories.map((x) => x.key);
    }
    if (offer.brandKey) {
      searchParams.brands = [offer.brandKey];
    }

    const searchResults = await searchWithMongoRelationsExtra(searchParams);

    return Response.ok(searchResults);
  });

export const promoted: Route<
  Response.Ok<MpnOffer[]> | Response.BadRequest<string>
> = route
  .get("/promoted")
  .use(Parser.query(productCollectionAndLimitQueryParams))
  .handler(async (request) => {
    const { limit, productCollection, market } = request.query;

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
        market,
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
  | Response.Ok<{
      offer: MpnOffer;
      identical: MpnOfferRelation[];
      interchangeable: MpnOfferRelation[];
    }>
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
      const relQuantity = get(offerRelation, ["identical", "quantity"]);
      const relCategories = get(marketData, ["mpnCategories"]);
      const relNutrition = get(offerRelation, ["identical", "mpnNutrition"]);
      const relIngredients = get(offerRelation, [
        "identical",
        "mpnIngredients",
      ]);
      const relProperties = get(offerRelation, ["identical", "mpnProperties"]);

      offerRelation.quantity = relQuantity;
      offerRelation.mpnCategories = relCategories;
      offerRelation.mpnNutrition = relNutrition;
      offerRelation.mpnIngredients = relIngredients;
      offerRelation.mpnProperties = relProperties;
      offerRelation.relId = offerRelation.identical?._id;

      if (relQuantity?.size?.standard?.min && offerRelation.pricing?.price) {
        offerRelation.value = {
          size: {
            amount: {
              min:
                offerRelation.pricing.price / relQuantity?.size?.standard?.min,
              max:
                offerRelation.pricing.price / relQuantity?.size?.standard?.max,
            },
            standard: {
              min:
                offerRelation.pricing.price / relQuantity?.size?.standard?.min,
              max:
                offerRelation.pricing.price / relQuantity?.size?.standard?.max,
            },
            unit: relQuantity.size.unit,
          },
        };
      }

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
  const pricingHistory = await offerPricingHistoryCollection.findOne<{
    history: PricingHistoryObject[];
    updatedAt: string;
  }>({
    uri: request.routeParams.id,
  });
  if (!pricingHistory) {
    return Response.notFound();
  }

  const pricingObjects = getPricingHistoryV2({
    pricingHistory,
    endDate: addDays(new Date(pricingHistory.updatedAt), 7),
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
    let dealersArray = dealers.split(",").filter((x) => !!x);

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

    if (dealersArray.length === 0) {
      // Only use the most relevant dealers for some markets
      dealersArray = getDealersForMarket({
        market: request.query.market,
        productCollection: request.query.productCollection,
      });
    }

    const searchResponse = await searchWithMongoNoFacets({
      query: "",
      market: request.query.market,
      productCollections: [request.query.productCollection],
      sort: { [differencePercentageField]: sortDirection },
      limit: _limit,
      categories: categories ? categoriesArray : undefined,
      dealers: dealersArray.length > 0 ? dealersArray : undefined,
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
