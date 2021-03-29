import { getCollection } from "@/config/mongo";
import { ObjectID } from "bson";
import { offerReviewsCollectionName } from "../utils/constants";

export const addReview = async (
  review: OfferReview,
  reviewStatus: OfferReviewStatus,
) => {
  const reviewCollection = await getCollection(offerReviewsCollectionName);
  const mongoResult = await reviewCollection.insertOne({
    createdAt: new Date(),
    status: reviewStatus,
    ...review,
  });
  return mongoResult.result;
};

export const removeReview = async (reviewId: string) => {
  const reviewCollection = await getCollection(offerReviewsCollectionName);
  const mongoResult = await reviewCollection.updateOne(
    { _id: new ObjectID(reviewId) },
    {
      $set: {
        updatedAt: new Date(),
        status: "removed",
      },
    },
    { upsert: false },
  );
  return mongoResult.result;
};
