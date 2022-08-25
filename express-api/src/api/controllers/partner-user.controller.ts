import { nanoid } from "nanoid";
import slugify from "slugify";
import { ObjectId } from "mongodb";
import { offerCollectionName } from "./../utils/constants";
import { Parser, Response, Route, route } from "typera-express";
import { getCollection } from "@/config/mongo";
import * as t from "io-ts";
import { addDays } from "date-fns";

type PartnerProduct = {
  title: string;
  description: string;
  price: number;
  stockAmount: number;
};
type PartnerProductMongo = PartnerProduct & {
  _id: string;
  status: string;
};
type MpnMongoOfferPartner = MpnMongoOffer & {
  stockAmount: number;
};
type StorePartner = {
  _id: string;
  name: string;
  description: string;
  location?: Object;
  cognitoId: string;
  email: string;
  phoneNumber: string;
};

const makeNewMpnOfferFromPartnerProduct = ({
  partnerProduct,
  partner,
}: {
  partnerProduct: PartnerProduct;
  partner: StorePartner;
}) => {
  const offerId = nanoid();
  const uri = `partner:product:${offerId}`;
  const now = new Date();
  const dealerSlug = slugify(partner.name, {
    lower: true,
    replacement: "_",
    locale: "nb",
  });
  const imageUrl = new URL("https://link.sharizard.com/v1/create");
  imageUrl.searchParams.set("backgroundColor", "#eec643");
  imageUrl.searchParams.set("color", "#111111");
  imageUrl.searchParams.set("title", partner.name);
  imageUrl.searchParams.set("subtitle", partnerProduct.title);

  return {
    pricing: { price: partnerProduct.price },
    title: partnerProduct.title,
    description: partnerProduct.description,
    stockAmount: partnerProduct.stockAmount,
    dealer: dealerSlug,
    uri,
    href: "",
    imageUrl: imageUrl.toString(),
    partnerId: partner.cognitoId,
    status: "ACTIVE",
    validThrough: addDays(now, 28),
    validFrom: new Date(),
    siteCollection: "groceryoffers",
    market: "no",
    isPartner: true,
  };
};
const makeUpdateSetMpnOfferFromPartnerProduct = ({
  partnerProduct,
  partner,
}: {
  partnerProduct: PartnerProduct;
  partner: StorePartner;
}) => {
  const now = new Date();
  const imageUrl = new URL("https://link.sharizard.com/v1/create");
  imageUrl.searchParams.set("backgroundColor", "#eec643");
  imageUrl.searchParams.set("color", "#111111");
  imageUrl.searchParams.set("title", partner.name);
  imageUrl.searchParams.set("subtitle", partnerProduct.title);

  return {
    pricing: { price: partnerProduct.price },
    title: partnerProduct.title,
    description: partnerProduct.description,
    stockAmount: partnerProduct.stockAmount,
    imageUrl: imageUrl.toString(),
    validThrough: addDays(now, 28),
  };
};
const makePartnerProductFromMpnOffer = ({
  mpnOffer,
}: {
  mpnOffer: MpnMongoOfferPartner;
}) => {
  return {
    _id: mpnOffer._id,
    price: mpnOffer.pricing.price,
    title: mpnOffer.title,
    description: mpnOffer.description,
    stockAmount: mpnOffer.stockAmount,
    status: "ACTIVE",
  };
};

export const getProducts: Route<
  Response.Ok<{ items: PartnerProductMongo[] }> | Response.BadRequest<string>
> = route.get("/products").handler(async (request) => {
  const partnerId = request.req["user"].sub;
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
    const partnerId = request.req["user"].sub;

    const response = await partnerCollection.findOne({ cognitoId: partnerId });

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
    const partnerStoreCollection = await getCollection("partnerstores");
    const partnerId = request.req["user"].sub;

    const partner = await partnerStoreCollection.findOne({
      cognitoId: partnerId,
    });

    if (!partner) {
      return Response.internalServerError(
        `Not found partner with id ${partnerId}`,
      );
    }

    const mpnOffer = makeNewMpnOfferFromPartnerProduct({
      partnerProduct: request.body,
      partner,
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
    const partnerStoreCollection = await getCollection("partnerstores");
    const partnerId = request.req["user"].sub;

    const partner = await partnerStoreCollection.findOne({
      cognitoId: partnerId,
    });

    const mpnOffer = makeUpdateSetMpnOfferFromPartnerProduct({
      partnerProduct: request.body,
      partner,
    });

    const response = await offerCollection.updateOne(
      {
        _id: ObjectId(request.body._id),
        partnerId,
      },
      { $set: { ...mpnOffer } },
    );

    return Response.ok(response);
  });

export const deletePartnerProduct: Route<
  | Response.Ok<any>
  | Response.BadRequest<string>
  | Response.InternalServerError<string>
> = route.delete("/products/:id").handler(async (request) => {
  const offerCollection = await getCollection(offerCollectionName);
  const partnerId = request.req["user"].sub;

  const now = new Date();

  const response = await offerCollection.updateOne(
    {
      _id: ObjectId(request.routeParams.id),
      partnerId,
    },
    { $set: { status: "DISABLED", validThrough: now } },
  );

  return Response.ok({ _id: request.routeParams.id });
});
