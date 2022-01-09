import { Parser, Response, Route, route, URL } from "typera-express";
import * as t from "io-ts";
import { addReview, approveReview, removeReview } from "../services/reviews";
import { findOne } from "../services/offers";
import { getCollection } from "@/config/mongo";
import {
  offerCollectionName,
  offerReviewsCollectionName,
} from "../utils/constants";
import { NotFound } from "typera-common/response";
import { get } from "lodash";
import { defaultOfferProjection } from "../models/mpnOffer.model";

const productCollectionQueryParams = t.type({
  productCollection: t.string,
});

const addOfferReviewBody = t.type({
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
  .use(Parser.body(addOfferReviewBody))
  .handler(async (request) => {
    const offer = await findOne(request.body.review.uri);
    if (!offer) {
      return Response.notFound(
        `Offer with uri ${request.body.review.uri} not found.`,
      );
    }
    const createReviewResult = await addReview(
      request.body.review,
      get(request, ["user", "role"]) === "admin" ? "enabled" : "pending",
    );

    return Response.created(createReviewResult);
  });

export const remove: Route<
  Response.NoContent<any> | Response.BadRequest<string> | NotFound<string>
> = route.delete("/:id").handler(async (request) => {
  const createReviewResult = await removeReview(request.routeParams.id);

  if (createReviewResult > 0) {
    return Response.noContent();
  } else {
    return Response.notFound(
      `Could not remove review with id ${request.routeParams.id}`,
    );
  }
});
export const approve: Route<
  Response.NoContent<any> | Response.BadRequest<string> | NotFound<string>
> = route.put("/:id/approve").handler(async (request) => {
  const createReviewResult = await approveReview(request.routeParams.id);

  if (createReviewResult > 0) {
    return Response.noContent();
  } else {
    return Response.notFound(
      `Could not approve review with id ${request.routeParams.id}`,
    );
  }
});

export const getReviews: Route<
  Response.Ok<OfferReview[]> | Response.BadRequest<string>
> = route.get("/:uri").handler(async (request) => {
  const reviewCollection = await getCollection(offerReviewsCollectionName);
  if (get(request, ["user", "role"]) === "admin") {
    return Response.ok(
      await reviewCollection
        .find<OfferReview>({ uri: request.routeParams.uri })
        .toArray(),
    );
  } else {
    return Response.ok(
      await reviewCollection
        .find<OfferReview>({ uri: request.routeParams.uri, status: "enabled" })
        .toArray(),
    );
  }
});

export const listReviewsWithOffers: Route<
  Response.Ok<OfferReview[]> | Response.BadRequest<string>
> = route.get("/offers").handler(async (request) => {
  const reviewCollection = await getCollection(offerReviewsCollectionName);
  const offerCollection = await getCollection(offerCollectionName);
  const reviews = await reviewCollection.find({}).toArray();
  const uris = Array.from(new Set(reviews.map((x) => x.uri)));
  const offers = await offerCollection
    .find({ uri: { $in: uris } }, defaultOfferProjection)
    .toArray();

  const offersMap = {};
  offers.forEach((offer) => (offersMap[offer.uri] = { ...offer, reviews: [] }));

  reviews.forEach((review) => {
    offersMap[review.uri].reviews.push(review);
  });

  return Response.ok(Object.values(offersMap));
});
