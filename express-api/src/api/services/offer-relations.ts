import { getCollection } from "@/config/mongo";
import { Collection, ObjectId } from "mongodb";
import {
  offerBiRelationsCollectionName,
  offerRelationsCollectionName,
  OfferRelation,
} from "@/api/utils/constants";

export const getOfferRelationsCollection = async (): Promise<Collection> => {
  const promotionCollection = await getCollection(offerRelationsCollectionName);
  return promotionCollection;
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
): Promise<string[][]> => {
  const biRelationsOffersCollection = await getCollection(
    offerBiRelationsCollectionName,
  );
  const biRelations: IdenticalOfferRelation[] = await biRelationsOffersCollection
    .find({
      offerSet: { $in: uris },
    })
    .toArray();

  return biRelations.map((x) => x.offerSet);
};
