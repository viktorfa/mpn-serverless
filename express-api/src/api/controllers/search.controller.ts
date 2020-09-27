import { Parser, Response, Route, route } from "typera-express";
import * as t from "io-ts";
import {
  search as searchElastic,
  querySuggestion as querySuggestionElastic,
  registerClick as registerClickElastic,
} from "@/api/services/search";

const searchQueryParams = t.type({ query: t.string });

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

export const querySuggestion: Route<
  Response.Ok<string[]> | Response.BadRequest<string>
> = route
  .get("/search/hint")
  .use(Parser.query(searchQueryParams))
  .handler(async (request) => {
    const query = request.query.query;
    const searchResults = await querySuggestionElastic(query);
    return Response.ok(searchResults);
  });

const registerClickBody = t.type({
  query: t.string,
  document_id: t.string,
  request_id: t.string,
  tags: t.union([t.array(t.string), t.undefined]),
});

type RegisterClickBody = t.TypeOf<typeof registerClickBody>;

export const registerClick: Route<
  Response.NoContent | Response.BadRequest<string>
> = route
  .post("/search/click")
  .use(Parser.body(registerClickBody))
  .handler(async (request) => {
    try {
      const elasticResponse = await registerClickElastic(request.body);
      return Response.noContent();
    } catch (e) {
      console.error(e);
      console.error(`Could not register click for ${request.body.request_id}`);
      return Response.badRequest();
    }
  });
