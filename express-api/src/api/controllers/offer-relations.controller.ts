import ApiError from "@/api/utils/APIError";
import { getCollection, connectToMongo } from "@/config/mongo";
import * as t from "io-ts";
import { Parser, Response, Route, route } from "typera-express";
import {
  addBiRelationalOffers,
  removeBiRelationalOffer,
  updateOfferBiRelation,
} from "@/api/services/offer-relations";
import { findOne } from "@/api/services/offers";
import {
  offerBiRelationsCollectionName,
  offerCollectionName,
  OfferRelation,
} from "@/api/utils/constants";
import { ObjectId } from "mongodb";
import { getMongoSafeUri } from "@/api/utils/helpers";
import { intersection } from "lodash";

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

const mergeRelationsBody = t.type({
  sources: t.array(t.string),
  target: t.string,
  relationType: t.string,
});

export const mergeIdenticalRelations: Route<
  Response.Ok<
    | IdenticalOfferRelation
    | Response.NotFound<string>
    | Response.BadRequest<string>
  >
> = route
  .put("/merge-relations")
  .use(Parser.body(mergeRelationsBody))
  .handler(async (request) => {
    const { sources: sourceIds, target: targetId, relationType } = request.body;
    if (intersection(sourceIds, [targetId]).length > 0) {
      throw new ApiError({ message: "Target is in sources", status: 400 });
    }
    const [sourceOids, targetOid] = [
      sourceIds.map((x) => new ObjectId(x)),
      new ObjectId(targetId),
    ];

    const offerBiRelationsCollection = await getCollection(
      offerBiRelationsCollectionName,
    );
    const [sourceRelations, targetRelation] = (await Promise.all([
      offerBiRelationsCollection.find({ _id: { $in: sourceOids } }).toArray(),
      offerBiRelationsCollection.findOne({ _id: targetOid }),
    ])) as [IdenticalOfferRelation[], IdenticalOfferRelation];

    if (sourceRelations.length === 0 || !targetRelation) {
      throw new ApiError({ message: "Relation not found", status: 404 });
    }

    const sourceOfferUris: string[] = [];
    const sourceOfferGtins: string[] = [];
    sourceRelations.forEach(({ offerSet, gtins }) => {
      sourceOfferUris.push(...offerSet);
      sourceOfferGtins.push(...gtins);
    });
    const now = new Date();

    const targetUpdateSet = {};
    sourceOfferUris.forEach((uri) => {
      targetUpdateSet[`offerSetMeta.${getMongoSafeUri(uri)}.manual`] = {
        method: "manual",
        reason: "manual_add",
        updatedAt: now,
      };
    });

    // MongoDB transaction
    const dbClient = await connectToMongo();
    const session = dbClient.startSession();
    if (relationType === OfferRelation.identical) {
      try {
        await session.withTransaction(async () => {
          // Important:: You must pass the session to the operations
          await offerBiRelationsCollection.updateMany(
            { _id: { $in: sourceOids } },
            { $set: { isMerged: true, mergedTo: targetOid } },
            { session },
          );
          await offerBiRelationsCollection.updateOne(
            { _id: targetOid },
            {
              $addToSet: {
                offerSet: { $each: sourceOfferUris },
                gtins: { $each: sourceOfferGtins },
              },
              $set: { ...targetUpdateSet, updatedAt: now },
            },
            { session },
          );
        });
      } finally {
        await session.endSession();
      }
    } else {
      await addBiRelationalOffers(
        [...targetRelation.offerSet, ...sourceOfferUris],
        relationType,
      );
    }

    return Response.ok({ sourceRelations, targetRelation });
  });

export const unmergeIdenticalRelations: Route<
  Response.Ok<
    | IdenticalOfferRelation
    | Response.NotFound<string>
    | Response.BadRequest<string>
  >
> = route
  .put("/unmerge-relations")
  .use(Parser.body(mergeRelationsBody))
  .handler(async (request) => {
    const { sources: sourceIds, target: targetId, relationType } = request.body;
    if (intersection(sourceIds, [targetId]).length > 0) {
      throw new ApiError({ message: "Target is in sources", status: 400 });
    }
    const [sourceOids, targetOid] = [
      sourceIds.map((x) => new ObjectId(x)),
      new ObjectId(targetId),
    ];

    const offerBiRelationsCollection = await getCollection(
      offerBiRelationsCollectionName,
    );
    const [sourceRelations, targetRelation] = (await Promise.all([
      offerBiRelationsCollection.find({ _id: { $in: sourceOids } }).toArray(),
      offerBiRelationsCollection.findOne({ _id: targetOid }),
    ])) as [IdenticalOfferRelation[], IdenticalOfferRelation];

    if (sourceRelations.length === 0 || !targetRelation) {
      throw new ApiError({ message: "Relation not found", status: 404 });
    }

    const sourceOfferUris: string[] = [];
    const sourceOfferGtins: string[] = [];
    sourceRelations.forEach(({ offerSet, gtins }) => {
      sourceOfferUris.push(...offerSet);
      sourceOfferGtins.push(...gtins);
    });
    const now = new Date();

    const targetUpdateSet = {};
    sourceOfferUris.forEach((uri) => {
      targetUpdateSet[`offerSetMeta.${getMongoSafeUri(uri)}.manual`] = {
        method: "manual",
        reason: "manual_remove",
        updatedAt: now,
      };
    });
    sourceOfferGtins.forEach((gtin) => {
      targetUpdateSet[`gtinsMeta.${getMongoSafeUri(gtin)}.manual`] = {
        method: "manual",
        reason: "manual_remove",
        updatedAt: now,
      };
    });

    // MongoDB transaction
    const dbClient = await connectToMongo();
    const session = dbClient.startSession();

    if (relationType === OfferRelation.identical) {
      try {
        await session.withTransaction(async () => {
          // Important:: You must pass the session to the operations
          await offerBiRelationsCollection.updateOne(
            { _id: targetOid },
            {
              $pull: {
                offerSet: { $in: sourceOfferUris },
                gtins: { $in: sourceOfferGtins },
              },
              $set: { ...targetUpdateSet, updatedAt: now },
            },
            { session },
          );
          await offerBiRelationsCollection.updateMany(
            { _id: sourceOids },
            { $set: { isMerged: null, mergedTo: null } },
            { session },
          );
        });
      } finally {
        await session.endSession();
      }
    } else {
      await Promise.all(
        sourceOfferUris.map((x) => removeBiRelationalOffer(x, relationType)),
      );
    }

    return Response.ok({ sourceRelations, targetRelation });
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
      .find<MpnMongoOffer>({
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
      [
        OfferRelation.identical,
        OfferRelation.interchangeable,
        OfferRelation.identicaldifferentquantity,
        OfferRelation.exchangeabledifferentquantity,
      ].includes(request.body.relationType)
    ) {
      const dbResult = await addBiRelationalOffers(
        [sourceOffer, ...targetOffers].map((x) => x.uri),
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
        sourceOffer.uri,
        request.body.relationType,
      );
      return Response.ok(dbResult);
    }
  });
