import { Parser, Response, Route, route } from "typera-express";
import { spiderrunsCollectionName } from "../utils/constants";
import { groupBy } from "lodash";
import { getLimitFromQueryParam, limitQueryParams } from "./typera-types";
import { getCollection } from "@/config/mongo";

export const getGrouped: Route<Response.Ok<any> | Response.BadRequest<string>> =
  route
    .get("/grouped")
    .use(Parser.query(limitQueryParams))
    .handler(async (request) => {
      const { limit } = request.query;
      let _limit = getLimitFromQueryParam(limit, 256, 1024);

      const collection = await getCollection(spiderrunsCollectionName);

      const spiderruns = await collection
        .find({})
        .project({ example_items: 0, stats: 0 })
        .sort({ updatedAt: -1 })
        .limit(_limit)
        .toArray();

      const result = groupBy(spiderruns, "provenance");

      return Response.ok(result);
    });
