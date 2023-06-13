import * as t from "io-ts";
import { Parser, Response, Route, route } from "typera-express";
import { getOffersByUris } from "@/api/services/offers";
import {
  addTagToBiRelation,
  getBiRelationById,
  getBiRelationsForTags,
  getOfferBiRelations,
  getOfferBiRelationsCollection,
  getOfferGroupFromBirelation,
  getTagsForBiRelation,
  removeTagFromBiRelation,
} from "../services/offer-relations";
import { flatten, get } from "lodash";
import { marketQueryParams, getLimitFromQueryParam } from "./typera-types";
import { ObjectId } from "mongodb";
import { defaultOfferProjection } from "../models/mpnOffer.model";
import { Filter } from "mongodb";
import { getCollection } from "@/config/mongo";
import { offerCollectionName } from "../utils/constants";

const offerGroupsQueryParams = t.type({
  tags: t.union([t.string, t.undefined]),
  limit: t.union([t.string, t.undefined]),
  offset: t.union([t.string, t.undefined]),
  market: t.union([t.string, t.undefined]),
  dealer: t.union([t.string, t.undefined]),
});

export const getOfferGroups: Route<
  Response.Ok<ListResponse<SimilarOffersObject>> | Response.BadRequest<string>
> = route
  .get("/")
  .use(Parser.query(offerGroupsQueryParams))
  .handler(async (request) => {
    const { tags, limit, market, dealer, offset } = request.query;

    let biRelationIds: string[] = [];
    let biRelations = [];
    const biRelationCollection = await getOfferBiRelationsCollection();

    const _offset = getLimitFromQueryParam(offset, 0, 2 ** 10);

    const offerFilter: { market?: string } = {};
    const biRelationFilter: { offerSet?: object } = {};
    if (market) {
      offerFilter.market = market;
    }
    if (dealer) {
      biRelationFilter.offerSet = { $regex: dealer };
    }
    if (tags) {
      biRelationIds = await getBiRelationsForTags(
        tags.split(","),
        limit ? Number.parseInt(limit) : undefined,
      );
      biRelations = await biRelationCollection
        .find({
          ...biRelationFilter,
          _id: { $in: biRelationIds.map((x) => new ObjectId(x)) },
        })
        .skip(_offset)
        .limit(32)
        .toArray();
    } else {
      biRelations = await biRelationCollection
        .find({ ...biRelationFilter })
        .skip(_offset)
        .limit(32)
        .toArray();
    }
    const offerUris = flatten(biRelations.map((x) => x.offerSet));
    const offers = await getOffersByUris(
      offerUris,
      offerFilter,
      defaultOfferProjection,
    );
    const offerMap = {};
    offers.forEach((x) => {
      offerMap[x.uri] = x;
    });
    const result = [];
    biRelations.forEach((x) => {
      result.push(getOfferGroupFromBirelation(x, offerMap));
    });
    return Response.ok({
      items: result.filter((x) => x.offers.length > 0),
    });
  });

export const getOfferGroup: Route<
  | Response.Ok<SingleSimilarOffersObject>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route
  .get("/:id")
  .use(Parser.query(marketQueryParams))
  .handler(async (request) => {
    const biRelation = await getBiRelationById(request.routeParams.id);
    if (!biRelation) {
      return Response.notFound(
        `Cound not find offer relation with id ${request.routeParams.id}`,
      );
    }
    const { market } = request.query;
    const offerFilter: { market?: string } = {};
    if (market) {
      offerFilter.market = market;
    }
    const offers = await getOffersByUris(
      biRelation.offerSet,
      offerFilter,
      undefined,
      false,
    );

    return Response.ok(
      getOfferGroupFromBirelation(
        biRelation,
        offers.reduce((acc, x) => ({ ...acc, [x.uri]: x }), {}),
      ),
    );
  });

export const getOfferGroupsForOffer: Route<
  | Response.Ok<Record<string, IdenticalOfferRelation>>
  | Response.BadRequest<string>
> = route
  .get("/offer/:uri")
  .use(Parser.query(marketQueryParams))
  .handler(async (request) => {
    const biRelations = await getOfferBiRelations(request.routeParams.uri);
    return Response.ok(biRelations);
  });

export const getOfferGroupsForOfferWithOffer: Route<
  | Response.Ok<{
      identical: MpnOffer[];
      interchangeable: MpnOffer[];
      offer: MpnOffer;
    }>
  | Response.NotFound
  | Response.BadRequest<string>
> = route
  .get("/offer/:uri/with-offer")
  .use(Parser.query(marketQueryParams))
  .handler(async (request) => {
    const offerCollection = await getCollection(offerCollectionName);

    const now = new Date();

    try {
      const relationResults = await getOfferBiRelations(
        request.routeParams.uri,
      );
      const identicalUris = get(
        relationResults,
        ["identical", "offerSet"],
        [],
      ).filter((x) => x !== request.routeParams.uri);
      const interchangeableUris = get(
        relationResults,
        ["interchangeable", "offerSet"],
        [],
      ).filter((x) => x !== request.routeParams.uri);
      const offerFilter: Filter<OfferInstance> = {
        uri: {
          $in: [
            ...identicalUris,
            ...interchangeableUris,
            request.routeParams.uri,
          ],
        },
        $or: [{ uri: request.routeParams.uri }, { validThrough: { $gt: now } }],
      };
      if (request.query.market) {
        offerFilter.market = request.query.market;
      }
      const offers = await offerCollection
        .find(offerFilter)
        .project<MpnOffer>(defaultOfferProjection)
        .toArray();

      if (offers.length === 1) {
        return Response.ok({
          offer: offers[0],
          identical: [],
          interchangeable: [],
        });
      }

      const identical = offers.filter(
        (offer) =>
          identicalUris.includes(offer.uri) &&
          offer.uri !== request.routeParams.uri,
      );
      const interchangeable = offers.filter(
        (offer) =>
          interchangeableUris.includes(offer.uri) &&
          offer.uri !== request.routeParams.uri,
      );
      const offer = offers.find((x) => x.uri === request.routeParams.uri);

      return Response.ok({
        offer,
        identical,
        interchangeable,
      });
    } catch (e) {
      return Response.notFound();
    }
  });

const addTagToOffersBody = t.type({
  id: t.string,
  tag: t.string,
});

export const postAddTagToOfferGroup: Route<
  Response.NoContent<any> | Response.BadRequest<string>
> = route
  .post("/tags")
  .use(Parser.body(addTagToOffersBody))
  .handler(async (request) => {
    return Response.noContent(
      await addTagToBiRelation(request.body.id, request.body.tag),
    );
  });

export const putRemoveTagFromOfferGroup: Route<
  Response.NoContent<any> | Response.BadRequest<string>
> = route
  .put("/tags/remove")
  .use(Parser.body(addTagToOffersBody))
  .handler(async (request) => {
    return Response.noContent(
      await removeTagFromBiRelation(request.body.id, request.body.tag),
    );
  });

export const getTagsForOfferGroupHandler: Route<
  Response.Ok<OfferTag[]> | Response.BadRequest<string>
> = route.get("/:id/tags").handler(async (request) => {
  return Response.ok(await getTagsForBiRelation(request.routeParams.id));
});
