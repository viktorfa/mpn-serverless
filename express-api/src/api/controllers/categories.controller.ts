import * as t from "io-ts";
import { Response, Route, route, Parser } from "typera-express";
import { getCollection } from "@/config/mongo";
import { mpnCategoriesCollectionName } from "../utils/constants";
import { FilterQuery } from "mongodb";

const categoriesQueryParams = t.type({
  level: t.union([t.string, t.undefined]),
  parent: t.union([t.string, t.undefined]),
});

export const list: Route<
  Response.Ok<MpnCategory[]> | Response.BadRequest<string>
> = route
  .get("/")
  .use(Parser.query(categoriesQueryParams))
  .handler(async (request) => {
    const { level, parent } = request.query;

    const categoriesCollection = await getCollection(
      mpnCategoriesCollectionName,
    );
    const filter: FilterQuery<MpnCategory> = {};
    if (level) {
      filter.level = Number.parseInt(level);
    }
    if (parent) {
      filter.parent = parent;
    }
    const result = await categoriesCollection.find(filter).toArray();

    return Response.ok(result);
  });

export const getByKey: Route<
  Response.Ok<MpnCategory[]> | Response.BadRequest<string>
> = route.get("/:key").handler(async (request) => {
  const categoriesCollection = await getCollection(mpnCategoriesCollectionName);

  const category = await categoriesCollection.findOne({
    key: request.routeParams.key,
  });
  let parentObject = null;
  if (category.parent) {
    parentObject = await categoriesCollection.findOne({
      key: category.parent,
    });
  }
  const children = await categoriesCollection
    .find({
      parent: request.routeParams.key,
    })
    .toArray();

  return Response.ok({ ...category, children, parentObject });
});
