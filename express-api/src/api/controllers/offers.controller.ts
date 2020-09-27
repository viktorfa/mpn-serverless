import { Response, Route, route } from "typera-express";
import { getOffersCollection } from "@/api/services/offers";

export const list: Route<Response.Ok<MpnOffer[]>> = route
  .get("/")
  .handler(async (request) => {
    const offersCollection = await getOffersCollection();
    const offers = await offersCollection
      .find()
      .project({ title: 1, pricing: 1, dealer: 1, href: 1 })
      .limit(16)
      .toArray();
    return Response.ok(offers);
  });
