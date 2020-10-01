import { getCollection } from "@/config/mongo";
import { ObjectId, Collection } from "mongodb";
import { defaultOfferProjection } from "../models/mpnOffer.model";
import { isMongoUri } from "../utils/helpers";

const DEFAULT_COLLECTION_NAME = "groceryoffer";

export const getOffersCollection = async (
  collectionName: string = DEFAULT_COLLECTION_NAME,
): Promise<Collection> => {
  const collection = await getCollection(collectionName);
  return collection;
};

export const getPromotionsCollection = async (
  collectionName: string = DEFAULT_COLLECTION_NAME,
): Promise<Collection> => {
  const strippedProductCollection = collectionName.endsWith("s")
    ? `${collectionName.substring(0, collectionName.length - 1)}`
    : collectionName;
  const promotionCollection = await getOffersCollection(
    `${strippedProductCollection}promotions`,
  );
  return promotionCollection;
};

const getFindOneFilter = (
  id: string,
): Record<"_id", ObjectId> | Record<"uri", string> => {
  if (isMongoUri(id)) {
    return { _id: new ObjectId(id) };
  } else {
    return { uri: id };
  }
};

export const findOne = async (
  id: string,
  collectionName: string,
): Promise<MpnOffer> => {
  const offersCollection = await getOffersCollection(collectionName);
  let filter = getFindOneFilter(id);
  return offersCollection.findOne<MpnOffer>(filter, {
    projection: defaultOfferProjection,
  });
};
export const findOneFull = async (
  id: string,
  collectionName: string,
): Promise<FullMpnOffer> => {
  const offersCollection = await getOffersCollection(collectionName);
  let filter = getFindOneFilter(id);
  return offersCollection.findOne<FullMpnOffer>(filter);
};
