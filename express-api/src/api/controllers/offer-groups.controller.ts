import * as t from "io-ts";
import { Parser, Response, Route, route } from "typera-express";
import {
  getOfferUrisForTags,
  getSimilarGroupedOffersFromOfferUris,
} from "@/api/services/offers";

const offerGroupsQueryParams = t.type({
  tags: t.string,
  limit: t.union([t.string, t.undefined]),
});

export const getOfferGroups: Route<
  Response.Ok<ListResponse<SimilarOffersObject>> | Response.BadRequest<string>
> = route
  .get("/")
  .use(Parser.query(offerGroupsQueryParams))
  .handler(async (request) => {
    const { tags, limit } = request.query;

    const offerUris = await getOfferUrisForTags(
      tags.split(","),
      limit ? Number.parseInt(limit) : undefined,
    );

    return Response.ok({
      items: await getSimilarGroupedOffersFromOfferUris(offerUris),
    });
  });
