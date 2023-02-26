import { ObjectId } from "mongodb";
import { getCollection } from "@/config/mongo";
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
  return { _id: mongoResult.insertedId };
};

export const removeReview = async (reviewId: string) => {
  const reviewCollection = await getCollection(offerReviewsCollectionName);
  const mongoResult = await reviewCollection.updateOne(
    { _id: new ObjectId(reviewId) },
    {
      $set: {
        updatedAt: new Date(),
        status: "removed",
      },
    },
    { upsert: false },
  );
  return mongoResult.modifiedCount;
};

export const approveReview = async (reviewId: string) => {
  const reviewCollection = await getCollection(offerReviewsCollectionName);
  const mongoResult = await reviewCollection.updateOne(
    { _id: new ObjectId(reviewId) },
    {
      $set: {
        updatedAt: new Date(),
        status: "enabled",
      },
    },
    { upsert: false },
  );
  return mongoResult.modifiedCount;
};
