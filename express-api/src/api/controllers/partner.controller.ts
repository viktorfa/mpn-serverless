import { findOne } from "./../services/categories";
import { Parser, Response, Route, route } from "typera-express";
import { handlerunsCollectionName } from "../utils/constants";
import { groupBy } from "lodash";
import { getLimitFromQueryParam, limitQueryParams } from "./typera-types";
import { getCollection } from "@/config/mongo";

const partnerProducts = [
  {
    title: "Egg 12pk",
    price: 30,
    description: "Egg fra frittgående høner",
    stockAmount: 14,
    _id: 0,
  },
  {
    title: "Halv gris",
    price: 1200,
    description: "Vakumpakket halv gris",
    stockAmount: 4,
    _id: 1,
  },
  {
    title: "Solbærsyltetøy 400g",
    price: 50,
    description: "Hjemmelaget solbærsyltetøy",
    stockAmount: 22,
    _id: 2,
  },
];

export const getPartnerProducts: Route<
  Response.Ok<any> | Response.BadRequest<string>
> = route.get("/:partnerId").handler(async (request) => {
  const result = partnerProducts;

  return Response.ok(result);
});

export const getPartner: Route<Response.Ok<any> | Response.BadRequest<string>> =
  route.get("/:partnerId").handler(async (request) => {
    const partnerCollection = await getCollection("storepartners");

    const response = await partnerCollection.findOne({ cognitoId: "" });

    return Response.ok(response);
  });
