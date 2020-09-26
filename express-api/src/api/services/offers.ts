import { getCollection } from "@/config/mongo";

const DEFAULT_COLLECTION_NAME = "groceryoffer";

export const getOffersCollection = async (
  collectionName: string = DEFAULT_COLLECTION_NAME,
) => {
  const collection = await getCollection(collectionName);
  return collection;
};
