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

export const addBiRelationalOffers = async (
  offers: MpnMongoOffer[],
  relationType: OfferRelationType,
): Promise<IdenticalOfferRelation> => {
  const biRelationsOffersCollection = await getCollection(
    offerBiRelationsCollectionName,
  );

  const offerUris = Array.from(new Set(offers.map((x) => x.uri)));

  const existingRelation = await biRelationsOffersCollection.findOne({
    offerSet: { $in: offerUris },
    relationType: relationType,
  });
  let mongoResult = null;
  if (existingRelation) {
    mongoResult = await biRelationsOffersCollection.updateOne(
      {
        _id: new ObjectId(existingRelation._id),
      },
      {
        $addToSet: {
          offerSet: { $each: [...offerUris, ...existingRelation.offerSet] },
        },
      },
    );
  } else {
    mongoResult = await biRelationsOffersCollection.insertOne({
      offerSet: offerUris,
      relationType: relationType,
    });
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
      mongoResult = await biRelationsOffersCollection.updateOne(
        {
          _id: new ObjectId(existingRelation._id),
        },
        { $pull: { offerSet: offer.uri } },
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
    .find({
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
): Promise<UriOfferGroup[]> => {
  const biRelationsOffersCollection = await getCollection(
    offerBiRelationsCollectionName,
  );
  const biRelations: IdenticalOfferRelation[] =
    await biRelationsOffersCollection
      .find({
        offerSet: { $in: uris },
      })
      .toArray();

  return biRelations.map((x) => ({ uris: x.offerSet, title: x.title }));
};

export const getBiRelationById = async (
  id: string,
): Promise<IdenticalOfferRelation> => {
  const biRelationsOffersCollection = await getCollection(
    offerBiRelationsCollectionName,
  );
  const result: IdenticalOfferRelation =
    await biRelationsOffersCollection.findOne({
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
): Promise<string[]> => {
  const tagsCollection = await getCollection(offerBiRelationTagsCollectionName);

  const now = getNowDate();

  return tagsCollection
    .find({
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
