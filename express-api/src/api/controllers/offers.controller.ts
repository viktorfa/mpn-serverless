import { Parser, Response, Route, URL, route } from "typera-express";
import * as t from "io-ts";
import { getOffersCollection } from "@/api/services/offers";
import { search as searchElastic } from "@/api/services/search";

const searchQueryParams = t.type({ query: t.string });

export const list: Route<Response.Ok<MpnOffer[]>> = route
  .get("/")
  .handler(async (request) => {
    const offersCollection = await getOffersCollection();
    const offers = await offersCollection
      .find()
      .project({ title: 1, pricing: 1, dealer: 1, href: 1 })
      .limit(16)
      .toArray();
    return Response.ok(offers);
  });
export const search: Route<
  Response.Ok<MpnOffer[]> | Response.BadRequest<string>
> = route
  .get("/search")
  .use(Parser.query(searchQueryParams))
  .handler(async (request) => {
    const query = request.query.query;
    const searchResults = await searchElastic(query);
    return Response.ok(searchResults);
  });
