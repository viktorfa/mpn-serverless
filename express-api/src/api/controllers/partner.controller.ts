import { ObjectId } from "mongodb";
import { offerCollectionName } from "./../utils/constants";
import { Response, Route, route } from "typera-express";
import { getCollection } from "@/config/mongo";

export const getPartnerProducts: Route<
  Response.Ok<{ items: PartnerProductMongo[] }> | Response.BadRequest<string>
> = route.get("/:partnerId/products").handler(async (request) => {
  const offerCollection = await getCollection(offerCollectionName);
  const now = new Date();

  const response = await offerCollection
    .find({
      partnerId: new ObjectId(request.routeParams.partnerId),
      validThrough: { $gt: now },
      status: "ACTIVE",
    })
    .toArray();

  return Response.ok({ items: response });
});

export const getProducts: Route<
  Response.Ok<{ items: PartnerProductMongo[] }> | Response.BadRequest<string>
> = route.get("/products").handler(async (request) => {
  const offerCollection = await getCollection(offerCollectionName);
  const now = new Date();

  const response = await offerCollection
    .find({
      partnerId: { $exists: 1 },
      validThrough: { $gt: now },
      status: "ACTIVE",
    })
    .limit(12)
    .toArray();

  return Response.ok({ items: response });
});

export const getPartner: Route<Response.Ok<any> | Response.BadRequest<string>> =
  route.get("/:partnerId").handler(async (request) => {
    const partnerCollection = await getCollection("partnerstores");

    const response = await partnerCollection.findOne({
      _id: new ObjectId(request.routeParams.partnerId),
    });

    return Response.ok(response);
  });

export const getPartnerShopWithProducts: Route<
  | Response.Ok<{ partner: StorePartner; products: MpnMongoOffer[] }>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route.get("/with-products/:partnerId").handler(async (request) => {
  const [partnerCollection, offerCollection] = await Promise.all([
    getCollection("partnerstores"),
    getCollection(offerCollectionName),
  ]);
  const now = new Date();

  const partnerShopResponse = await partnerCollection.findOne({
    _id: new ObjectId(request.routeParams.partnerId),
  });

  if (!partnerShopResponse) {
    return Response.notFound();
  }

  const partnerProductsResponse = await offerCollection
    .find({
      partnerId: new ObjectId(request.routeParams.partnerId),
      validThrough: { $gt: now },
      status: "ACTIVE",
    })
    .toArray();

  return Response.ok({
    partner: partnerShopResponse,
    products: partnerProductsResponse,
  });
});

export const getPartners: Route<
  Response.Ok<{ items: StorePartner[] }> | Response.BadRequest<string>
> = route.get("/").handler(async (request) => {
  const partnerCollection = await getCollection("partnerstores");

  const response = await partnerCollection.find().limit(12).toArray();

  return Response.ok({ items: response });
});
