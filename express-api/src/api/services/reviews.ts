import { getCollection } from "@/config/mongo";
import { Collection } from "mongodb";
import { getStrippedProductCollectionName } from "../models/utils";

export const getReviewsCollection = async (
  collectionName: string,
): Promise<Collection> => {
  const promotionCollection = await getCollection(
    `${getStrippedProductCollectionName(collectionName)}reviews`,
  );
  return promotionCollection;
};

export const addReview = async (review: OfferReview, productCollection) => {
  const reviewCollection = await getReviewsCollection(productCollection);
  const mongoResult = await reviewCollection.insertOne({
    createdAt: new Date(),
    ...review,
  });
  console.log("mongoResult");
  console.log(mongoResult);
  return mongoResult.result;
};
