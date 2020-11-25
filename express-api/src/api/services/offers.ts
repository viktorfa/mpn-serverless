import { getCollection } from "@/config/mongo";
import { ObjectId, Collection } from "mongodb";
import { defaultOfferProjection } from "../models/mpnOffer.model";
import { getStrippedProductCollectionName } from "../models/utils";
import { isMongoUri } from "../utils/helpers";

export const getPromotionsCollection = async (
  collectionName: string,
): Promise<Collection> => {
  const promotionCollection = await getCollection(
    `${getStrippedProductCollectionName(collectionName)}promotions`,
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
  const offersCollection = await getCollection(collectionName);
  let filter = getFindOneFilter(id);
  return offersCollection.findOne<MpnOffer>(filter, {
    projection: defaultOfferProjection,
  });
};
export const findOneFull = async (
  id: string,
  collectionName: string,
): Promise<FullMpnOffer> => {
  const offersCollection = await getCollection(collectionName);
  let filter = getFindOneFilter(id);
  return offersCollection.findOne<FullMpnOffer>(filter);
};
