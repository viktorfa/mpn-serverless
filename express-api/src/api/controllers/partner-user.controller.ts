import {
  makeNewMpnOfferFromPartnerProduct,
  makePartnerProductFromMpnOffer,
  makeUpdateSetMpnOfferFromPartnerProduct,
} from "./../utils/partners";
import { ObjectId } from "mongodb";
import { offerCollectionName } from "./../utils/constants";
import { Parser, Response, Route, route } from "typera-express";
import { getCollection } from "@/config/mongo";
import * as t from "io-ts";

export const getProducts: Route<
  Response.Ok<{ items: PartnerProductMongo[] }> | Response.BadRequest<string>
> = route.get("/products").handler(async (request) => {
  const partnerId = new ObjectId(request.req["mongoUser"]._id);
  const offerCollection = await getCollection(offerCollectionName);

  const response = await offerCollection
    .find({
      partnerId,
      status: "ACTIVE",
    })
    .toArray();

  const resultProducts = response.map((mpnOffer) =>
    makePartnerProductFromMpnOffer({ mpnOffer }),
  );

  return Response.ok({ items: resultProducts });
});

export const getPartner: Route<Response.Ok<any> | Response.NotFound<string>> =
  route.get("/me").handler(async (request) => {
    const partnerCollection = await getCollection("partnerstores");
    const partnerId = new ObjectId(request.req["mongoUser"]._id);

    const response = await partnerCollection.findOne({ _id: partnerId });

    if (!response) {
      return Response.notFound();
    }

    return Response.ok(response);
  });

const createPartnerProductBody = t.type({
  title: t.string,
  description: t.string,
  price: t.number,
  stockAmount: t.number,
});

export const createPartnerProduct: Route<
  | Response.Ok<any>
  | Response.BadRequest<string>
  | Response.InternalServerError<string>
> = route
  .post("/products")
  .use(Parser.body(createPartnerProductBody))
  .handler(async (request) => {
    const offerCollection = await getCollection(offerCollectionName);

    const mpnOffer = makeNewMpnOfferFromPartnerProduct({
      partnerProduct: request.body,
      partner: request.req["mongoUser"],
    });

    const response = await offerCollection.insertOne(mpnOffer);

    return Response.ok(response);
  });

const updatePartnerProductBody = t.type({
  title: t.string,
  description: t.string,
  price: t.number,
  stockAmount: t.number,
  _id: t.string,
});

export const updatePartnerProduct: Route<
  | Response.Ok<any>
  | Response.BadRequest<string>
  | Response.InternalServerError<string>
> = route
  .put("/products")
  .use(Parser.body(updatePartnerProductBody))
  .handler(async (request) => {
    const offerCollection = await getCollection(offerCollectionName);
    const partnerId = new ObjectId(request.req["mongoUser"]._id);

    const mpnOffer = makeUpdateSetMpnOfferFromPartnerProduct({
      partnerProduct: request.body,
      partner: request.req["mongoUser"],
    });

    const response = await offerCollection.updateOne(
      {
        _id: new ObjectId(request.body._id),
        partnerId,
      },
      { $set: { ...mpnOffer } },
    );

    return Response.ok(response);
  });
const updatePartnerStoreBody = t.type({
  name: t.string,
  description: t.string,
  email: t.string,
  phoneNumber: t.string,
});

export const updatePartnerStore: Route<
  | Response.Ok<any>
  | Response.BadRequest<string>
  | Response.InternalServerError<string>
> = route
  .put("/me")
  .use(Parser.body(updatePartnerStoreBody))
  .handler(async (request) => {
    const partnerStoresCollection = await getCollection("partnerstores");
    const partnerId = new ObjectId(request.req["mongoUser"]._id);

    const response = await partnerStoresCollection.updateOne(
      {
        _id: partnerId,
      },
      { $set: { ...request.body } },
    );

    return Response.ok(response);
  });

export const deletePartnerProduct: Route<
  | Response.Ok<any>
  | Response.BadRequest<string>
  | Response.InternalServerError<string>
> = route.delete("/products/:id").handler(async (request) => {
  const offerCollection = await getCollection(offerCollectionName);
  const partnerId = new ObjectId(request.req["mongoUser"]._id);

  const now = new Date();

  const response = await offerCollection.updateOne(
    {
      _id: new ObjectId(request.routeParams.id),
      partnerId,
    },
    { $set: { status: "DISABLED", validThrough: now } },
  );

  return Response.ok({ _id: request.routeParams.id });
});
