import _ from "lodash";
import * as t from "io-ts";
import { Parser, Response, Route, route, URL } from "typera-express";
import {
  addTagToOffers,
  findOne,
  findOneFull,
  getOfferUrisForTags,
  getTagsForOffer,
} from "@/api/services/offers";
import { search as searchElastic } from "@/api/services/search";
import { defaultOfferProjection } from "../models/mpnOffer.model";
import { getNowDate } from "../utils/helpers";
import { DEFAULT_PRODUCT_COLLECTION } from "../utils/constants";
import { getEngineName } from "@/api/controllers/search.controller";
import { indexDocuments } from "../services/elastic";
import { getCollection } from "@/config/mongo";
import { getOfferBiRelations } from "../services/offer-relations";
import { getBoolean, getStringList } from "./request-param-parsing";
import { FilterQuery, QuerySelector } from "mongodb";

const offersQueryParams = t.type({
  productCollection: t.union([t.string, t.undefined]),
  tags: t.union([t.string, t.undefined]),
  limit: t.union([t.string, t.undefined]),
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
    const {
      productCollection = DEFAULT_PRODUCT_COLLECTION,
      tags,
      limit,
    } = request.query;

    let _limit = Number.parseInt(limit)
      ? 32
      : Math.min(128, Number.parseInt(limit));

    const offersCollection = await getCollection(productCollection);

    const now = getNowDate();
    const selection: FilterQuery<FullMpnOffer> = {
      validThrough: { $gte: now },
    };
    if (tags) {
      selection.uri = { $in: await getOfferUrisForTags(getStringList(tags)) };
    }
    console.log("GET list");
    console.log(selection);
    const offers = await offersCollection
      .find<MpnOffer>(selection)
      .project(defaultOfferProjection)
      .limit(_limit)
      .toArray();
    return Response.ok({ items: offers });
  });

export const addToElastic: Route<
  Response.NoContent | Response.NotFound<string> | Response.BadRequest<string>
> = route
  .put("/elastic/", URL.str("id"))
  .use(Parser.query(offersQueryParams))
  .handler(async (request) => {
    const { productCollection = DEFAULT_PRODUCT_COLLECTION } = request.query;

    let offer: FullMpnOffer;
    try {
      offer = await findOneFull(request.routeParams.id, productCollection);
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
    console.log("indexResult");
    console.log(indexResult);
    return Response.noContent();
  });

const similarOffersQueryParams = t.type({
  productCollection: t.union([t.string, t.undefined]),
  useSearch: t.union([t.string, t.undefined]),
});

export const similar: Route<
  | Response.Ok<MpnOffer[]>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route
  .get("/similar/", URL.str("id"))
  .use(Parser.query(similarOffersQueryParams))
  .handler(async (request) => {
    const { productCollection = DEFAULT_PRODUCT_COLLECTION } = request.query;
    const useSearch = getBoolean(request.query.useSearch);

    const offersCollection = await getCollection(productCollection);

    let offer: FullMpnOffer;
    try {
      offer = await findOneFull(request.routeParams.id, productCollection);
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
        await searchElastic(offer.title, getEngineName(productCollection), 32),
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
        await searchElastic(offer.title, getEngineName(productCollection), 32),
      );
    }
    const result = similarOffers.map((x, i) => ({
      ...x,
      score: offer.similarOffers[i].score,
    }));

    return Response.ok(result);
  });

export const promoted: Route<
  Response.Ok<MpnOffer[]> | Response.BadRequest<string>
> = route
  .get("/promoted")
  .use(Parser.query(offersQueryParams))
  .handler(async (request) => {
    const PROMOTED_OFFERS_LIMIT = 32;
    const {
      productCollection = DEFAULT_PRODUCT_COLLECTION,
      limit,
    } = request.query;

    const _limit = Number.parseInt(limit)
      ? Number.parseInt(limit)
      : PROMOTED_OFFERS_LIMIT;

    const promotedOfferUris = await getOfferUrisForTags(["promoted"]);

    const now = getNowDate();
    const selection: Record<string, any> = {
      validThrough: { $gte: now },
      uri: { $in: promotedOfferUris },
    };

    const offerCollection = await getCollection(productCollection);

    const promotedOffers = await offerCollection
      .find(selection, defaultOfferProjection)
      .limit(_limit)
      .toArray();

    const result = [...promotedOffers];

    if (promotedOffers.length < _limit) {
      const extraOffers = await offerCollection
        .find({ validThrough: { $gte: now } })
        .project(defaultOfferProjection)
        .sort({ pageviews: -1 })
        .limit(_limit - promotedOffers.length)
        .toArray();
      result.push(...extraOffers);
    }

    return Response.ok(_.take(result, _limit));
  });

export const find: Route<
  Response.Ok<MpnOffer> | Response.NotFound | Response.BadRequest<string>
> = route
  .get("/", URL.str("id"))
  .use(Parser.query(offersQueryParams))
  .handler(async (request) => {
    const { productCollection = DEFAULT_PRODUCT_COLLECTION } = request.query;

    try {
      const offer = await findOne(request.routeParams.id, productCollection);
      return Response.ok(offer);
    } catch (e) {
      return Response.notFound();
    }
  });

export const relatedOffers: Route<
  | Response.Ok<{ identical: MpnOffer[]; interchangeable: MpnOffer[] }>
  | Response.NotFound
  | Response.BadRequest<string>
> = route
  .get("/", URL.str("id"), "/related")
  .use(Parser.query(offersQueryParams))
  .handler(async (request) => {
    const { productCollection = DEFAULT_PRODUCT_COLLECTION } = request.query;

    const offerCollection = await getCollection(productCollection);

    try {
      const relationResults = await getOfferBiRelations(
        request.routeParams.id,
        productCollection,
      );
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
      const offers = await offerCollection
        .find({
          uri: { $in: [...identicalUris, ...interchangeableUris] },
        })
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

export const getTagsForOfferHandler: Route<
  Response.Ok<string[]> | Response.BadRequest<string>
> = route.get("/", URL.str("id"), "/tags").handler(async (request) => {
  return Response.ok(await getTagsForOffer(request.routeParams.id));
});
