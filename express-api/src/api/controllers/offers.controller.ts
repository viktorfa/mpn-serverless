import _ from "lodash";
import * as t from "io-ts";
import { Parser, Response, Route, route } from "typera-express";
import {
  addTagToOffers,
  findOne,
  findOneFull,
  getOfferUrisForTags,
  getSimilarGroupedOffersFromOfferUris,
  getTagsForOffer,
  removeTagFromOffers,
} from "@/api/services/offers";
import { search as searchElastic } from "@/api/services/search";
import { defaultOfferProjection } from "../models/mpnOffer.model";
import { getNowDate } from "../utils/helpers";
import { getEngineName } from "@/api/controllers/search.controller";
import { indexDocuments } from "../services/elastic";
import { getCollection } from "@/config/mongo";
import { getOfferBiRelations } from "../services/offer-relations";
import { getBoolean, getStringList } from "./request-param-parsing";
import { FilterQuery } from "mongodb";
import { offerCollectionName } from "../utils/constants";
import {
  getLimitFromQueryParam,
  limitQueryParams,
  marketQueryParams,
  productCollectionAndLimitQueryParams,
  productCollectionQueryParams,
} from "./typera-types";
import { getQuantityObject, getValueObject } from "../utils/quantity";

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

    const selection: FilterQuery<FullMpnOffer> = {
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

    const result = await offerCollection
      .find(selection, defaultOfferProjection)
      .sort({ pageviews: -1, url_fingerprint: 1 })
      .limit(_limit)
      .toArray();

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
    return Response.ok(
      await searchElastic(
        offer.title.substring(0, 127),
        getEngineName(productCollection),
        32,
      ),
    );
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
  const similarOffers = await offersCollection.aggregate(pipeline).toArray();

  if (similarOffers.length === 0) {
    console.warn(
      `Offer ${request.routeParams.id} did not have any time valid similar offers.`,
    );
    return Response.ok(
      await searchElastic(
        offer.title.substring(0, 127),
        getEngineName(productCollection),
        32,
      ),
    );
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

const extraOffersQueryParams = t.type({
  productCollection: t.union([t.string, t.undefined]),
  limit: t.union([t.string, t.undefined]),
});

export const extra: Route<
  | Response.Ok<MpnResultOffer[]>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route
  .get("/extra/:id")
  .use(Parser.query(extraOffersQueryParams))
  .handler(async (request) => {
    const { limit, productCollection = "extraoffers" } = request.query;
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

    const searchResults = await searchElastic(query, productCollection, _limit);
    return Response.ok(searchResults.filter((offer) => offer.score > 20));
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

    const searchResults = await searchElastic(query, "extraoffers", _limit);
    return Response.ok(searchResults.filter((offer) => offer.score > 20));
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

    const searchResults = await searchElastic(
      query,
      getEngineName(productCollection),
      _limit,
    );

    return Response.ok(searchResults.filter((offer) => offer.score > 10));
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
      .find(selection, defaultOfferProjection)
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
        .project(defaultOfferProjection)
        .sort({ pageviews: -1 })
        .limit(_limit - promotedOffers.length)
        .toArray();
      result.push(...extraOffers);
    }

    return Response.ok(_.take(result, _limit));
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
      const offerFilter: FilterQuery<OfferInstance> = {
        uri: { $in: [...identicalUris, ...interchangeableUris] },
      };
      if (request.query.market) {
        offerFilter.market = request.query.market;
      }
      const offers = await offerCollection
        .find(offerFilter)
        .project(defaultOfferProjection)
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
  Response.Ok<string[]> | Response.BadRequest<string>
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
    const offer: MpnMongoOffer = await offerCollection.findOne({
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
        { relationType: { $in: ["identical", "identicaldifferentsize"] } },
      ),
    });
  });
