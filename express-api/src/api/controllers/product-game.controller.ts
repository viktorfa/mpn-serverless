import { searchWithMongoRelationsNoFacets } from "./../services/search";
import * as t from "io-ts";
import { Parser, Response, Route, route } from "typera-express";
import { getCollection } from "@/config/mongo";
import { ObjectId } from "mongodb";

export const productGameRandomQueryParams = t.type({
  dealer: t.string,
  market: t.string,
});

export const getRandomOffer: Route<
  Response.Ok<any> | Response.BadRequest<string>
> = route
  .get("/random")
  .use(Parser.query(productGameRandomQueryParams))
  .handler(async (request) => {
    const { dealer, market } = request.query;
    const relationsCollection = await getCollection(
      `relations_with_offers_${market}`,
    );
    const productGameData = await getCollection("productgamedata");

    const allProductGameData = await productGameData
      .find({})
      .project({ relId: 1 })
      .toArray();

    const randomOfferResponse = await relationsCollection
      .aggregate([
        {
          $search: {
            compound: {
              filter: [
                {
                  text: {
                    path: "offers.dealerKey",
                    query: dealer,
                  },
                },
              ],
            },
          },
        },
        {
          $match: {
            "gtins.0": { $exists: false },
            _id: { $nin: allProductGameData.map((x) => x.relId) },
          },
        },
        {
          $facet: {
            items: [{ $limit: 100 }],
            meta: [{ $replaceWith: "$$SEARCH_META" }, { $limit: 1 }],
          },
        },
        {
          $set: {
            offer: {
              $arrayElemAt: [
                "$items",
                {
                  $toInt: {
                    $multiply: [{ $size: "$items" }, { $rand: {} }],
                  },
                },
              ],
            },
          },
        },
        { $unset: ["items"] },
      ])
      .toArray();

    const randomOffer = randomOfferResponse[0].offer;

    const similarOffers = await searchWithMongoRelationsNoFacets({
      query: randomOffer.title,
      market,
      includeOutdated: true,
    });

    const eligibleSimilarOffers = similarOffers.items.filter(
      (x) => x._id.toString() !== randomOffer._id.toString(),
    );

    return Response.ok({
      offer: randomOffer,
      candidates: eligibleSimilarOffers,
    });
  });

export const registerSkipOffer: Route<
  Response.NoContent<any> | Response.BadRequest<string>
> = route.put("/skip/:id").handler(async (request) => {
  const now = new Date();
  const productGameData = await getCollection("productgamedata");

  const mongoResponse = await productGameData.updateOne(
    { relId: new ObjectId(request.routeParams.id) },
    {
      $set: {
        updatedAt: now,
        updatedBy: request.req["userId"],
      },
    },
    { upsert: true },
  );
  return Response.noContent();
});
