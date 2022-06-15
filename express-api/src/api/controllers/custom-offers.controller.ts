import * as t from "io-ts";
import { Parser, Response, Route, route } from "typera-express";
import { getCollection } from "@/config/mongo";
import { offerCollectionName } from "../utils/constants";
import { addDays } from "date-fns";
import { nanoid } from "nanoid";

const customOfferPostBody = t.type({
  productCollection: t.string,
  market: t.string,
  title: t.string,
  price: t.union([t.number, t.undefined]),
  priceText: t.union([t.string, t.undefined]),
  dealer: t.union([t.string, t.undefined]),
  description: t.union([t.string, t.undefined]),
  validThrough: t.union([t.string, t.null, t.undefined]),
  validFrom: t.union([t.string, t.null, t.undefined]),
  imageUrl: t.string,
  identity_id: t.string,
  location: t.union([t.undefined, t.null, t.UnknownRecord]),
});

export const postCustomOffer: Route<
  | Response.Created<CustomOffer>
  | Response.BadRequest<string>
  | Response.Conflict<string>
> = route
  .post("/")
  .use(Parser.body(customOfferPostBody))
  .handler(async (request) => {
    const priceText = request.body.priceText;
    const price =
      request.body.price && request.body.price > 0 ? request.body.price : null;
    if ((!price && !priceText) || price < 0) {
      return Response.badRequest("Need price or priceText");
    }

    const now = new Date();
    let validThrough = new Date(request.body.validThrough);
    const oneDayAhead = addDays(now, 1);
    if (validThrough.toString() === "Invalid Date") {
      validThrough = addDays(now, 3);
    }
    if (validThrough < now) {
      validThrough = oneDayAhead;
    } else if (validThrough > addDays(now, 7)) {
      validThrough = addDays(now, 7);
    }

    let validFrom = new Date(request.body.validFrom);
    if (validFrom.toString() === "Invalid Date") {
      validFrom = now;
    }

    const pricing = { price, text: priceText, currency: "NOK" };

    const id = nanoid();
    const uri = `custom:product:${id}`;

    const customOffer = {
      siteCollection: request.body.productCollection,
      market: request.body.market,
      title: request.body.title,
      pricing,
      dealer: request.body.dealer,
      description: request.body.description,
      validFrom,
      validThrough,
      imageUrl: request.body.imageUrl,
      identity_id: request.body.identity_id,
      uri,
      provenance: "custom",
      location: request.body.location,
    };

    const offersCollection = await getCollection(offerCollectionName);

    // Check for duplicate upload
    const existingOffersForIdentityId = await offersCollection
      .find({
        provenance: "custom",
        identity_id: request.body.identity_id,
        title: request.body.title,
        validThrough: { $gt: now },
      })
      .toArray();

    if (existingOffersForIdentityId.length) {
      return Response.conflict("Offer with same title and user already exists");
    }

    const mongoResult = await offersCollection.insert(customOffer);

    return Response.created(customOffer);
  });
