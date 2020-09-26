import { Parser, Response, Route, URL, route } from "typera-express";
import * as t from "io-ts";

interface Offer {
  title: string;
  [key: string]: any;
}

const searchQueryParams = t.type({ query: t.string });

export const list: Route<Response.Ok<Offer[]>> = route
  .get("/")
  .handler(async (request) => {
    return Response.ok([{ title: "per" }]);
  });
export const search: Route<
  Response.Ok<Offer[]> | Response.BadRequest<string>
> = route
  .get("/search")
  .use(Parser.query(searchQueryParams))
  .handler(async (request) => {
    return Response.ok([{ title: "per" }]);
  });
