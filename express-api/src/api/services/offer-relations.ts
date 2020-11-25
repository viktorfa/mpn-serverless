import { getCollection } from "@/config/mongo";
import { Collection, ObjectId } from "mongodb";
import { getStrippedProductCollectionName } from "../models/utils";
import { OfferRelation } from "../utils/constants";

export const getOfferRelationsCollection = async (
  collectionName: string,
): Promise<Collection> => {
  const promotionCollection = await getCollection(
    `${getStrippedProductCollectionName(collectionName)}relations`,
  );
  return promotionCollection;
};

export const addBiRelationalOffers = async (
  offers: MpnMongoOffer[],
  collectionName: string,
  relationType: OfferRelationType,
): Promise<IdenticalOfferRelation> => {
  const biRelationsOffersCollection = await getCollection(
    `${getStrippedProductCollectionName(collectionName)}birelations`,
  );

  const offerUris = Array.from(new Set(offers.map((x) => x.uri)));

  const existingRelation = await biRelationsOffersCollection.findOne({
    offerSet: { $in: offerUris },
    relationType: relationType,
  });
  console.log("existingRelation");
  console.log(existingRelation);
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
  collectionName: string,
  relationType: OfferRelationType,
): Promise<IdenticalOfferRelation> => {
  const biRelationsOffersCollection = await getCollection(
    `${getStrippedProductCollectionName(collectionName)}birelations`,
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
  collectionName: string,
): Promise<Record<string, IdenticalOfferRelation>> => {
  const biRelationsOffersCollection = await getCollection(
    `${getStrippedProductCollectionName(collectionName)}birelations`,
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
