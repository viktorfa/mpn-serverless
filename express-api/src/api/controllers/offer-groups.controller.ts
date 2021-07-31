import * as t from "io-ts";
import { Parser, Response, Route, route } from "typera-express";
import {
  getOfferUrisForTags,
  getSimilarGroupedOffersFromOfferUris,
  getOffersByUris,
} from "@/api/services/offers";
import {
  getBiRelationById,
  getOfferBiRelationsCollection,
} from "../services/offer-relations";
import { get, flatten } from "lodash";

const getOfferGroupFromBirelation = (
  biRelation: IdenticalOfferRelation,
  offerMap: { [key: string]: MpnMongoOffer },
) => {
  const offers = biRelation.offerSet.map((x) => offerMap[x]).filter((x) => !!x);
  return {
    _id: biRelation._id,
    offers,
    relationType: biRelation.relationType,
    title: biRelation.title ?? get(offers, [0, "title"]),
    description: get(offers, [0, "description"]),
    subtitle: get(offers, [0, "subtitle"]),
    shortDescription: get(offers, [0, "shortDescription"]),
    imageUrl: get(offers, [0, "imageUrl"]),
  };
};

const offerGroupsQueryParams = t.type({
  tags: t.union([t.string, t.undefined]),
  limit: t.union([t.string, t.undefined]),
});

export const getOfferGroups: Route<
  Response.Ok<ListResponse<SimilarOffersObject>> | Response.BadRequest<string>
> = route
  .get("/")
  .use(Parser.query(offerGroupsQueryParams))
  .handler(async (request) => {
    const { tags, limit } = request.query;

    let offerUris = [];

    if (tags) {
      offerUris = await getOfferUrisForTags(
        tags.split(","),
        limit ? Number.parseInt(limit) : undefined,
      );
    } else {
      const biRelationCollection = await getOfferBiRelationsCollection();
      const biRelations = await biRelationCollection
        .find({})
        .limit(32)
        .toArray();
      offerUris = flatten(biRelations.map((x) => x.offerSet));
      const offers = await getOffersByUris(offerUris, null, true);
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
    }

    return Response.ok({
      items: await getSimilarGroupedOffersFromOfferUris(offerUris),
    });
  });

export const getOfferGroup: Route<
  | Response.Ok<SingleSimilarOffersObject>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route.get("/:id").handler(async (request) => {
  const biRelation = await getBiRelationById(request.routeParams.id);
  if (!biRelation) {
    return Response.notFound(
      `Cound not find offer relation with id ${request.routeParams.id}`,
    );
  }
  const offers = await getOffersByUris(biRelation.offerSet, null, true);

  return Response.ok(
    getOfferGroupFromBirelation(
      biRelation,
      offers.reduce((acc, x) => ({ ...acc, [x.uri]: x }), {}),
    ),
  );
});
