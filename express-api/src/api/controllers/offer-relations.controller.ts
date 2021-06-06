import { getCollection } from "@/config/mongo";
import * as t from "io-ts";
import { Parser, Response, Route, route, URL } from "typera-express";
import {
  addBiRelationalOffers,
  removeBiRelationalOffer,
  updateOfferBiRelation,
} from "../services/offer-relations";
import { findOne } from "../services/offers";
import { offerCollectionName, OfferRelation } from "../utils/constants";

const addOfferRelationBody = t.type({
  uri: t.string,
  targetUris: t.array(t.string),
  relationType: t.union([
    t.literal(OfferRelation.identical),
    t.literal(OfferRelation.interchangeable),
    t.literal(OfferRelation.identicaldifferentquantity),
    t.literal(OfferRelation.exchangeabledifferentquantity),
  ]),
});
const updateOfferRelationBody = t.type({
  id: t.string,
  title: t.string,
});

export const updateOfferRelation: Route<
  | Response.Ok<UpdateOfferRelationBody>
  | Response.NotFound<string>
  | Response.BadRequest<string>
> = route
  .put("/update")
  .use(Parser.body(updateOfferRelationBody))
  .handler(async (request) => {
    const result = await updateOfferBiRelation(request.body);
    if (!result) {
      return Response.notFound(
        `Offer relation with id ${request.body.id} not found.`,
      );
    }
    return Response.ok(result);
  });

export const addIdenticalOffers: Route<
  | Response.Ok<IdenticalOfferRelation>
  | Response.NotFound<string>
  | Response.BadRequest<string>
> = route
  .put("/")
  .use(Parser.body(addOfferRelationBody))
  .handler(async (request) => {
    const sourceOffer = await findOne(request.body.uri);
    if (!sourceOffer) {
      return Response.notFound(
        `Source offer with uri ${request.body.uri} not found.`,
      );
    }
    const offersCollection = await getCollection(offerCollectionName);
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
        request.body.relationType,
      );
      return Response.ok(dbResult);
    }
  });

export const removeOfferRelation: Route<
  | Response.Ok<IdenticalOfferRelation>
  | Response.NotFound<string>
  | Response.BadRequest<string>
> = route
  .put("/remove")
  .use(Parser.body(addOfferRelationBody))
  .handler(async (request) => {
    const sourceOffer = await findOne(request.body.uri);
    if (!sourceOffer) {
      return Response.notFound(
        `Source offer with uri ${request.body.uri} not found.`,
      );
    }

    if (
      [OfferRelation.identical, OfferRelation.interchangeable].includes(
        request.body.relationType,
      )
    ) {
      const dbResult = await removeBiRelationalOffer(
        sourceOffer,
        request.body.relationType,
      );
      return Response.ok(dbResult);
    }
  });
