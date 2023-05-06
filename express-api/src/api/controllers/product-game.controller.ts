import * as t from "io-ts";
import { Parser, Response, Route, route } from "typera-express";
import { offerCollectionName } from "../utils/constants";
import { getCollection } from "@/config/mongo";
import { searchWithMongo } from "../services/search";
import { addDays } from "date-fns";

export const productGameRandomQueryParams = t.type({
  provenance: t.string,
  market: t.union([t.string, t.undefined]),
});

export const getRandomOffer: Route<
  Response.Ok<any> | Response.BadRequest<string>
> = route
  .get("/random")
  .use(Parser.query(productGameRandomQueryParams))
  .handler(async (request) => {
    const now = new Date();
    const { provenance, market } = request.query;
    const offerCollection = await getCollection(offerCollectionName);
    const productGameData = await getCollection("productgamedata");

    const allProductGameData = await productGameData
      .find({ updatedAt: { $gt: addDays(now, -365) } })
      .project({ uri: 1 })
      .toArray();

    const findOneFilter = {
      provenance: provenance,
      "gtins.ean": { $exists: false },
      "gtins.gtin13": { $exists: false },
      validThrough: { $gt: now },
      uri: { $nin: allProductGameData.map((x) => x.uri) },
    };
    const nDocs = await offerCollection.count(findOneFilter);
    const offer = (
      await offerCollection
        .find(findOneFilter)
        .limit(1)
        .skip(Math.floor(Math.random() * nDocs))
        .toArray()
    )[0];

    const similarOffers = await searchWithMongo({
      query: offer.title,
      markets: [market],
      includeOutdated: true,
    });

    const eligibleSimilarOffers = similarOffers.items.filter(
      (x) => x.gtins && (!!x.gtins.ean || !!x.gtins.gtin13),
    );

    return Response.ok({ offer, candidates: eligibleSimilarOffers });
  });

export const registerSkipOffer: Route<
  Response.NoContent<any> | Response.BadRequest<string>
> = route.put("/skip/:id").handler(async (request) => {
  const now = new Date();
  const productGameData = await getCollection("productgamedata");

  const mongoResponse = await productGameData.updateOne(
    { uri: request.routeParams.id },
    {
      $set: {
        updatedAt: now,
        updatedBy: request["user"],
      },
    },
    { upsert: true },
  );
  return Response.noContent();
});
