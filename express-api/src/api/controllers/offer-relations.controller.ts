import { getCollection } from "@/config/mongo";
import * as t from "io-ts";
import { Parser, Response, Route, route, URL } from "typera-express";
import { addBiRelationalOffers } from "../services/offer-relations";
import { findOne } from "../services/offers";
import { DEFAULT_PRODUCT_COLLECTION, OfferRelation } from "../utils/constants";

const productCollectionQueryParams = t.type({
  productCollection: t.union([t.string, t.undefined]),
});

const addOfferRelationBody = t.type({
  uri: t.string,
  targetUris: t.array(t.string),
  relationType: t.union([
    t.literal(OfferRelation.identical),
    t.literal(OfferRelation.interchangeable),
  ]),
});

export const addIdenticalOffers: Route<
  | Response.Ok<IdenticalOfferRelation>
  | Response.NotFound<string>
  | Response.BadRequest<string>
> = route
  .put("/")
  .use(Parser.query(productCollectionQueryParams))
  .use(Parser.body(addOfferRelationBody))
  .handler(async (request) => {
    const { productCollection = DEFAULT_PRODUCT_COLLECTION } = request.query;

    const sourceOffer = await findOne(request.body.uri, productCollection);
    if (!sourceOffer) {
      return Response.notFound(
        `Source offer with uri ${request.body.uri} not found.`,
      );
    }
    const offersCollection = await getCollection(productCollection);
    const targetOffers = await offersCollection
      .find({
        uri: { $in: request.body.targetUris },
      })
      .toArray();
    if (targetOffers.length === 0) {
      return Response.notFound(
        `Target offers with uris ${request.body.targetUris.join(
          ", ",
        )} not found.`,
      );
    }
    if (
      [OfferRelation.identical, OfferRelation.interchangeable].includes(
        request.body.relationType,
      )
    ) {
      const dbResult = await addBiRelationalOffers(
        [sourceOffer, ...targetOffers],
        productCollection,
        request.body.relationType,
      );
      return Response.ok(dbResult);
    }
  });
