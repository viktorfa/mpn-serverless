import * as t from "io-ts";
import { Parser, Response, Route, route } from "typera-express";
import { promotionsCollectionName } from "../utils/constants";
import { getLimitFromQueryParam } from "./typera-types";
import { getCollection } from "@/config/mongo";
import { getAdTractionCampaigns } from "../services/promotions";
import { take } from "lodash";
import { findSimilarPromoted, findSimilarPromotedV2 } from "../services/offers";

export const promotionsQueryParams = t.type({
  limit: t.union([t.string, t.undefined]),
  market: t.string,
  productCollection: t.union([t.string, t.undefined]),
  type: t.union([t.string, t.undefined]),
  uri: t.union([t.string, t.undefined]),
});

export const getPromotions: Route<
  Response.Ok<any> | Response.BadRequest<string>
> = route
  .get("/")
  .use(Parser.query(promotionsQueryParams))
  .handler(async (request) => {
    const { limit } = request.query;
    let _limit = getLimitFromQueryParam(limit, 2, 8);

    const type = request.query.type || "square";
    if (type === "horizontal" && request.query.uri && Math.random() > 0.25) {
      let similarOffers = await findSimilarPromoted({
        uri: request.query.uri,
        market: request.query.market,
        limit: _limit,
      });
      if (similarOffers) {
        similarOffers = similarOffers.filter((x) => x.score > 30 && x.ahref);
        const result: PromotionBanner[] = similarOffers.map((offer) => {
          return {
            text: offer.title,
            url: offer.ahref,
            image: offer.imageUrl,
            type: "offer",
            score: offer.score,
            offer,
          };
        });
        if (result.length > 0) {
          return Response.ok(result);
        }
      }
    }
    if (type === "horizontal" && Math.random() > 0.5) {
      const result = await getAdTractionCampaigns({
        market: request.query.market,
        productCollection: request.query.productCollection,
      });
      if (result.length > 0) {
        return Response.ok(take(result, _limit));
      }
    }

    const collection = await getCollection(promotionsCollectionName);
    const selection = {
      market: request.query.market,
      type,
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

export const getPromotionsV2: Route<
  Response.Ok<any> | Response.BadRequest<string>
> = route
  .get("/")
  .use(Parser.query(promotionsQueryParams))
  .handler(async (request) => {
    const { limit } = request.query;
    let _limit = getLimitFromQueryParam(limit, 2, 8);

    const type = request.query.type || "square";
    if (type === "horizontal" && request.query.uri && Math.random() > 0.25) {
      let similarOffers = await findSimilarPromotedV2({
        uri: request.query.uri,
        market: request.query.market,
        limit: _limit,
      });
      if (similarOffers) {
        similarOffers = similarOffers.filter((x) => x.score > 20 && x.ahref);
        const result: PromotionBanner[] = similarOffers.map((offer) => {
          return {
            text: offer.title,
            url: offer.ahref,
            image: offer.imageUrl,
            type: "offer",
            score: offer.score,
            offer,
          };
        });
        if (result.length > 0) {
          return Response.ok(result);
        }
      }
    }
    if (type === "horizontal" && Math.random() > 0.5) {
      const result = await getAdTractionCampaigns({
        market: request.query.market,
        productCollection: request.query.productCollection,
      });
      if (result.length > 0) {
        return Response.ok(take(result, _limit));
      }
    }

    const collection = await getCollection(promotionsCollectionName);
    const selection = {
      market: request.query.market,
      type,
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
