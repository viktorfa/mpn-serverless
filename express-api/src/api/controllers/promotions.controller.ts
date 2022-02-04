import * as t from "io-ts";
import { Parser, Response, Route, route } from "typera-express";
import {
  promotionsCollectionName,
  spiderrunsCollectionName,
} from "../utils/constants";
import { groupBy } from "lodash";
import { getLimitFromQueryParam, limitQueryParams } from "./typera-types";
import { getCollection } from "@/config/mongo";

export const promotionsQueryParams = t.type({
  limit: t.union([t.string, t.undefined]),
  market: t.string,
  productCollection: t.union([t.string, t.undefined]),
});

export const getPromotions: Route<
  Response.Ok<any> | Response.BadRequest<string>
> = route
  .get("/")
  .use(Parser.query(promotionsQueryParams))
  .handler(async (request) => {
    const { limit } = request.query;
    let _limit = getLimitFromQueryParam(limit, 2, 8);

    const collection = await getCollection(promotionsCollectionName);
    const selection = {
      market: request.query.market,
      promotionStatus: { $ne: "DISABLED" },
    };
    const itemCount = await collection.find(selection).count();
    const offset = Math.max(
      0,
      Math.floor(Math.random() * itemCount) - (_limit - 1),
    );

    const promotions = await collection
      .find(selection)
      .limit(_limit)
      .skip(offset)
      .toArray();

    return Response.ok(promotions);
  });
