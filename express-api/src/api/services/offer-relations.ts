import { flatten, get, sortBy } from "lodash";
import { getCollection } from "@/config/mongo";
import { Collection, ObjectId } from "mongodb";
import {
  offerBiRelationsCollectionName,
  offerRelationsCollectionName,
  OfferRelation,
  offerBiRelationTagsCollectionName,
} from "@/api/utils/constants";
import { getDaysAhead, getNowDate } from "../utils/helpers";

export const getOfferRelationsCollection = async (): Promise<Collection> => {
  const promotionCollection = await getCollection(offerRelationsCollectionName);
  return promotionCollection;
};
export const getOfferBiRelationsCollection = async (): Promise<Collection> => {
  const promotionCollection = await getCollection(
    offerBiRelationsCollectionName,
  );
  return promotionCollection;
};

export const updateOfferBiRelation = async (
  offerRelation: UpdateOfferRelationBody,
): Promise<UpdateOfferRelationBody> => {
  const biRelationsOffersCollection = await getCollection(
    offerBiRelationsCollectionName,
  );

  const mongoResult = await biRelationsOffersCollection.updateOne(
    {
      _id: new ObjectId(offerRelation.id),
    },
    {
      $set: {
        title: offerRelation.title,
      },
    },
  );
  return offerRelation;
};

const getMongoSafeUri = (uri: string): string => {
  return uri.replaceAll(".", "\uff0E");
};

export const addBiRelationalOffers = async (
  offers: MpnMongoOffer[],
  relationType: OfferRelationType,
): Promise<IdenticalOfferRelation> => {
  const biRelationsOffersCollection = await getCollection(
    offerBiRelationsCollectionName,
  );

  const offerUris = Array.from(new Set(offers.map((x) => x.uri)));
  const now = new Date();

  const existingRelations: IdenticalOfferRelation[] =
    await biRelationsOffersCollection
      .find({
        offerSet: { $in: offerUris },
        relationType,
      })
      .toArray();
  let mongoResult = null;

  const existingRelation = sortBy(
    existingRelations,
    (x) => x.offerSet.length,
  )[0];

  if (existingRelation) {
    const newUris = flatten(
      existingRelations
        .filter((x) => x._id !== existingRelation._id)
        .map((x) => x.offerSet),
    );

    const updateSet = {};

    newUris.forEach((uri) => {
      updateSet[`offerSetMeta.${getMongoSafeUri(uri)}.auto`] = {
        method: "auto",
        reason: "merged_together_with_manual",
        updatedAt: now,
      };
    });
    offerUris.forEach((uri) => {
      updateSet[`offerSetMeta.${getMongoSafeUri(uri)}.manual`] = {
        method: "manual",
        reason: "manual_add",
        updatedAt: now,
      };
    });

    const operations = [];

    // Delete offer relations with overlapping offers
    existingRelations
      .filter((x) => x._id !== existingRelation._id)
      .forEach((x) => {
        operations.push({ deleteOne: { filter: { _id: ObjectId(x._id) } } });
      });

    operations.push({
      updateOne: {
        filter: { _id: new ObjectId(existingRelation._id) },
        update: {
          $addToSet: {
            offerSet: { $each: [...offerUris, ...newUris] },
          },
          $set: { ...updateSet, updatedAt: now },
        },
      },
    });

    mongoResult = await biRelationsOffersCollection.bulkWrite(operations);
  } else {
    const updateSet = {};
    offerUris.forEach((uri) => {
      updateSet[`offerSetMeta.${getMongoSafeUri(uri)}.manual`] = {
        method: "manual",
        reason: "initial_add",
        updatedAt: now,
      };
    });
    mongoResult = await biRelationsOffersCollection.updateOne(
      { offerSet: offerUris, relationType: relationType },
      {
        $setOnInsert: {
          ...updateSet,
          createdAt: now,
          updatedAt: now,
        },
      },
      { upsert: true },
    );
  }
  return mongoResult.result;
};
export const removeBiRelationalOffer = async (
  offer: MpnMongoOffer,
  relationType: OfferRelationType,
): Promise<IdenticalOfferRelation> => {
  const biRelationsOffersCollection = await getCollection(
    offerBiRelationsCollectionName,
  );

  const existingRelation = await biRelationsOffersCollection.findOne({
    offerSet: offer.uri,
    relationType: relationType,
  });
  let mongoResult = null;
  if (existingRelation) {
    const newOfferSet = existingRelation.offerSet.filter(
      (x) => x.uri !== offer.uri,
    );
    if (newOfferSet.length === 0) {
      mongoResult = await biRelationsOffersCollection.deleteOne({
        _id: new ObjectId(existingRelation._id),
      });
    } else {
      const updateSet = {
        [`offerSetMeta.${getMongoSafeUri(offer.uri)}.manual`]: {
          method: "manual",
          reason: "manual_remove",
          updatedAt: new Date(),
        },
      };
      mongoResult = await biRelationsOffersCollection.updateOne(
        {
          _id: new ObjectId(existingRelation._id),
        },
        { $pull: { offerSet: offer.uri }, $set: { ...updateSet } },
      );
    }
  } else {
    return null;
  }
  return mongoResult.result;
};

export const getOfferBiRelations = async (
  uri: string,
): Promise<Record<string, IdenticalOfferRelation>> => {
  const biRelationsOffersCollection = await getCollection(
    offerBiRelationsCollectionName,
  );
  const relationObjects = await biRelationsOffersCollection
    .find<IdenticalOfferRelation>({
      offerSet: uri,
    })
    .toArray();
  return {
    [OfferRelation.identical]: relationObjects.find(
      (x) => x.relationType === OfferRelation.identical,
    ),
    [OfferRelation.interchangeable]: relationObjects.find(
      (x) => x.relationType === OfferRelation.interchangeable,
    ),
  };
};

export const getBiRelationsForOfferUris = async (
  uris: string[],
  filter = {},
): Promise<UriOfferGroup[]> => {
  const biRelationsOffersCollection = await getCollection(
    offerBiRelationsCollectionName,
  );
  const biRelations: IdenticalOfferRelation[] =
    await biRelationsOffersCollection
      .find<IdenticalOfferRelation>({
        offerSet: { $in: uris },
        ...filter,
      })
      .toArray();

  return biRelations.map((x) => ({
    uris: x.offerSet,
    title: x.title,
    relationType: x.relationType,
    _id: x._id,
  }));
};

export const getBiRelationById = async (
  id: string,
): Promise<IdenticalOfferRelation> => {
  const biRelationsOffersCollection = await getCollection(
    offerBiRelationsCollectionName,
  );
  const result: IdenticalOfferRelation =
    await biRelationsOffersCollection.findOne<IdenticalOfferRelation>({
      _id: new ObjectId(id),
    });

  return result;
};

export const addTagToBiRelation = async (biRelationId: string, tag: string) => {
  const tagsCollection = await getCollection(offerBiRelationTagsCollectionName);

  const tagUpdate: Record<string, any> = {
    $set: { tag, biRelationId, selectionType: "manual", status: "enabled" },
  };
  if (["promotion_good-offer", "promoted"].includes(tag)) {
    tagUpdate.$set.validThrough = getDaysAhead(14);
  }

  return tagsCollection.updateOne({ tag, biRelationId }, tagUpdate, {
    upsert: true,
  });
};
export const removeTagFromBiRelation = async (
  biRelationId: string,
  tag: string,
) => {
  const tagsCollection = await getCollection(offerBiRelationTagsCollectionName);

  const tagUpdate: Record<string, any> = {
    $set: { status: "disabled" },
  };

  return tagsCollection.updateOne({ tag, biRelationId }, tagUpdate);
};

export const getTagsForBiRelation = async (
  biRelationId: string,
): Promise<OfferTag[]> => {
  const tagsCollection = await getCollection(offerBiRelationTagsCollectionName);

  const now = getNowDate();

  return tagsCollection
    .find<OfferTag>({
      biRelationId,
      $or: [
        { validThrough: { $gte: now } },
        { validThrough: { $exists: false } },
      ],
    })
    .toArray();
};

export const getBiRelationsForTags = async (
  tags: string[],
  limit: number = 128,
): Promise<string[]> => {
  const tagsCollection = await getCollection(offerBiRelationTagsCollectionName);

  const now = getNowDate();
  const tagObjects = await tagsCollection
    .find({
      tag: { $in: tags },
      $or: [
        { validThrough: { $gte: now } },
        { validThrough: { $exists: false } },
      ],
    })
    .limit(limit)
    .toArray();
  return tagObjects.map((x) => x.biRelationId);
};

export const getOfferGroupFromBirelation = (
  biRelation: IdenticalOfferRelation,
  offerMap: { [key: string]: MpnMongoOffer },
) => {
  const offers = biRelation.offerSet.map((x) => offerMap[x]).filter((x) => !!x);
  return {
    _id: biRelation._id,
    offers,
    relationType: biRelation.relationType,
    title: biRelation.title ?? get(offers, [0, "title"]),
    description: get(offers, [0, "description"]),
    subtitle: get(offers, [0, "subtitle"]),
    shortDescription: get(offers, [0, "shortDescription"]),
    imageUrl: get(offers, [0, "imageUrl"]),
  };
};
