import { getCollection } from "@/config/mongo";
import { offerReviewsCollectionName } from "../utils/constants";

export const addReview = async (review: OfferReview) => {
  const reviewCollection = await getCollection(offerReviewsCollectionName);
  const mongoResult = await reviewCollection.insertOne({
    createdAt: new Date(),
    ...review,
  });
  return mongoResult.result;
};
