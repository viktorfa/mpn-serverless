import { Parser, Response, Route, route, URL } from "typera-express";
import * as t from "io-ts";
import { addReview } from "../services/reviews";
import { findOne } from "../services/offers";
import { getCollection } from "@/config/mongo";
import { offerReviewsCollectionName } from "../utils/constants";

const productCollectionQueryParams = t.type({
  productCollection: t.string,
});

const addOfferRelationBody = t.type({
  review: t.type({
    body: t.string,
    author: t.string,
    uri: t.string,
    rating: t.union([
      t.literal(1),
      t.literal(2),
      t.literal(3),
      t.literal(4),
      t.literal(5),
    ]),
  }),
});

export const add: Route<
  | Response.Created<any>
  | Response.NotFound<string>
  | Response.BadRequest<string>
> = route
  .post("/")
  .use(Parser.body(addOfferRelationBody))
  .handler(async (request) => {
    const offer = await findOne(request.body.review.uri);
    if (!offer) {
      return Response.notFound(
        `Offer with uri ${request.body.review.uri} not found.`,
      );
    }
    const createReviewResult = await addReview(request.body.review);

    return Response.created(createReviewResult);
  });

export const getReviews: Route<
  Response.Ok<OfferReview[]> | Response.BadRequest<string>
> = route.get("/", URL.str("uri")).handler(async (request) => {
  const reviewCollection = await getCollection(offerReviewsCollectionName);
  return Response.ok(
    await reviewCollection.find({ uri: request.routeParams.uri }).toArray(),
  );
});