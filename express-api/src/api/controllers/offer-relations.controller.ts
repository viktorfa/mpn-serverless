import {
  MongoSearchParamsRelationsExtra,
  searchWithMongoRelationsExtra,
} from "./../services/search";
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
import { defaultOfferProjection } from "../models/mpnOffer.model";
import { getBoolean } from "./request-param-parsing";
import { getLimitFromQueryParam } from "./typera-types";

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

const getByGtinParams = t.type({
  market: t.string,
  gtin: t.union([t.string, t.undefined]),
});
export const getByGtin: Route<
  | Response.Ok<{ product: MpnOfferRelation }>
  | Response.NotFound<string>
  | Response.BadRequest<string>
> = route
  .get("/gtin/:gtin")
  .use(Parser.query(getByGtinParams))
  .handler(async (request) => {
    const relationsCollection = await getCollection(
      offerBiRelationsCollectionName,
    );

    const { market, gtin: queryGtin } = request.query;

    const gtin = [queryGtin, request.routeParams.gtin].find((x) => !!x);

    const relationResponse = (
      await relationsCollection
        .aggregate<MpnOfferRelation>([
          {
            $match: {
              gtins: gtin,
              "gtins.0": { $exists: 1 },
              relationType: OfferRelation.identical,
            },
          },
          {
            $lookup: {
              from: "mpnoffers_with_context",
              localField: "offerSet",
              foreignField: "uri",
              as: "offers",
              pipeline: [
                {
                  $match: {
                    market,
                  },
                },
                {
                  $project: defaultOfferProjection,
                },
              ],
            },
          },
        ])
        .toArray()
    )[0];

    if (!relationResponse) {
      return Response.notFound(`Product with gtin ${gtin} not found`);
    }

    let marketData = relationResponse[`m:${market}`];

    if (!marketData) {
      const marketCandidates = Object.entries(relationResponse).filter(
        ([key, value]) => key.startsWith("m:") && value,
      );
      marketData = marketCandidates[0][1];
    }

    relationResponse.title = marketData.title;
    relationResponse.subtitle = marketData.subtitle;
    relationResponse.market = marketData.market;

    return Response.ok({ product: relationResponse });
  });

const getByIdParams = t.type({
  market: t.string,
  allMarkets: t.union([t.string, t.undefined]),
});
export const getById: Route<
  | Response.Ok<{ product: MpnOfferRelation }>
  | Response.NotFound<string>
  | Response.BadRequest<string>
> = route
  .get("/:id")
  .use(Parser.query(getByIdParams))
  .handler(async (request) => {
    const relationsCollection = await getCollection(
      offerBiRelationsCollectionName,
    );

    const { market, allMarkets } = request.query;
    const id = request.routeParams.id;

    const productMatch = getBoolean(allMarkets) ? {} : { market };

    const relationResponse = (
      await relationsCollection
        .aggregate<MpnOfferRelation>([
          {
            $match: {
              _id: new ObjectId(id),
            },
          },
          {
            $lookup: {
              from: "mpnoffers_with_context",
              localField: "offerSet",
              foreignField: "uri",
              as: "offers",
              pipeline: [
                {
                  $match: productMatch,
                },
                {
                  $project: defaultOfferProjection,
                },
              ],
            },
          },
        ])
        .toArray()
    )[0];

    if (!relationResponse) {
      return Response.notFound(`Product with gtin ${gtin} not found`);
    }

    let marketData = relationResponse[`m:${market}`];

    if (!marketData) {
      const marketCandidates = Object.entries(relationResponse).filter(
        ([key, value]) => key.startsWith("m:") && value,
      );
      marketData = marketCandidates[0][1];
    } else {
      relationResponse.priceMin = marketData.priceMin;
      relationResponse.priceMax = marketData.priceMax;
      relationResponse.valueMin = marketData.valueMin;
      relationResponse.valueMax = marketData.valueMax;
    }

    const localOffers = relationResponse.offers.filter(
      (x) => x.market === market,
    );
    const foreignOffers = relationResponse.offers.filter(
      (x) => x.market !== market,
    );

    relationResponse.offers = localOffers;
    relationResponse.foreignOffers = foreignOffers;

    relationResponse.title = marketData.title;
    relationResponse.market = marketData.market;

    return Response.ok({ product: relationResponse });
  });

const extraParams = t.type({
  market: t.string,
  limit: t.union([t.string, t.undefined]),
  productCollection: t.union([t.string, t.undefined]),
});
export const extraRelations: Route<
  | Response.Ok<Omit<MpnMongoRelationsSearchResponse, "facets">>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route
  .get("/extra/:id")
  .use(Parser.query(extraParams))
  .handler(async (request) => {
    const { limit, productCollection, market } = request.query;
    let _limit = getLimitFromQueryParam(limit, 5);

    const relationsCollection = await getCollection(
      offerBiRelationsCollectionName,
    );

    const relationResponse = await relationsCollection.findOne({
      _id: new ObjectId(request.routeParams.id),
    });
    if (!relationResponse) {
      return Response.notFound(
        `Could not find relation with id ${request.routeParams.id}`,
      );
    }

    let marketData = relationResponse[`m:${market}`];

    if (!marketData) {
      const marketCandidates = Object.entries(relationResponse).filter(
        ([key, value]) => key.startsWith("m:") && value,
      );
      marketData = marketCandidates[0][1];
    }

    const title = marketData.title;

    const searchParams: MongoSearchParamsRelationsExtra = {
      title: title.substring(0, 127),
      market: market,
      limit: _limit,
      relationId: request.routeParams.id,
    };

    if (productCollection) {
      searchParams.productCollections = [productCollection];
    }
    if (marketData.mpnCategories?.length > 0) {
      searchParams.categories = marketData.mpnCategories.map((x) => x.key);
    }
    if (relationResponse.brandKey) {
      searchParams.brands = [relationResponse.brandKey];
    }

    const searchResults = await searchWithMongoRelationsExtra(searchParams);

    return Response.ok(searchResults);
  });
