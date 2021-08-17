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
import { get, flatten } from "lodash";
import { marketQueryParams } from "./typera-types";
import { ObjectId } from "bson";

const offerGroupsQueryParams = t.type({
  tags: t.union([t.string, t.undefined]),
  limit: t.union([t.string, t.undefined]),
  market: t.union([t.string, t.undefined]),
});

export const getOfferGroups: Route<
  Response.Ok<ListResponse<SimilarOffersObject>> | Response.BadRequest<string>
> = route
  .get("/")
  .use(Parser.query(offerGroupsQueryParams))
  .handler(async (request) => {
    const { tags, limit, market } = request.query;

    let biRelationIds: string[] = [];
    let biRelations = [];
    const biRelationCollection = await getOfferBiRelationsCollection();

    const offerFilter: { market?: string } = {};
    if (market) {
      offerFilter.market = market;
    }
    if (tags) {
      biRelationIds = await getBiRelationsForTags(
        tags.split(","),
        limit ? Number.parseInt(limit) : undefined,
      );
      biRelations = await biRelationCollection
        .find({ _id: { $in: biRelationIds.map((x) => new ObjectId(x)) } })
        .limit(32)
        .toArray();
    } else {
      biRelations = await biRelationCollection.find({}).limit(32).toArray();
    }
    const offerUris = flatten(biRelations.map((x) => x.offerSet));
    const offers = await getOffersByUris(offerUris, offerFilter, null);
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
      null,
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
  Response.Ok<string[]> | Response.BadRequest<string>
> = route.get("/:id/tags").handler(async (request) => {
  return Response.ok(await getTagsForBiRelation(request.routeParams.id));
});
