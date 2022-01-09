import * as t from "io-ts";
import { Response, Route, route, Parser } from "typera-express";
import { getCollection } from "@/config/mongo";
import {
  mpnCategoriesCollectionName,
  mpnCategoryMappingsCollectionName,
  offerCollectionName,
} from "../utils/constants";
import { Filter } from "mongodb";

const categoriesQueryParams = t.type({
  level: t.union([t.string, t.undefined]),
  parent: t.union([t.string, t.undefined]),
  context: t.union([t.string, t.undefined]),
});

export const list: Route<
  Response.Ok<MpnCategory[]> | Response.BadRequest<string>
> = route
  .get("/")
  .use(Parser.query(categoriesQueryParams))
  .handler(async (request) => {
    const { level, parent, context } = request.query;

    const categoriesCollection = await getCollection(
      mpnCategoriesCollectionName,
    );
    const filter: Filter<MpnCategory> = {};
    if (level) {
      filter.level = Number.parseInt(level);
    }
    if (parent) {
      filter.parent = parent;
    }
    if (context) {
      filter.context = context;
    }
    const result = await categoriesCollection
      .find<MpnCategory>(filter)
      .toArray();

    return Response.ok(result);
  });

export const getAllCategoriesForDealer: Route<
  Response.Ok<string[][]> | Response.BadRequest<string>
> = route.get("/dealer/:dealer").handler(async (request) => {
  const offerCollection = await getCollection(offerCollectionName);

  const now = new Date();

  const offers = await offerCollection
    .find({
      validThrough: { $gt: now },
      dealer: request.routeParams.dealer,
    })
    .project({ categories: 1 })
    .toArray();
  const categories: string[] = offers
    .map((x) => {
      if (x.categories && x.categories.length > 0) {
        return JSON.stringify(x.categories);
      } else {
        return null;
      }
    })
    .filter((x) => !!x);
  const categoriesSet = new Set(categories);

  const result = Array.from(categoriesSet).map((x) => JSON.parse(x));

  return Response.ok(result);
});

export const getCategoryMappingsForDealer: Route<
  Response.Ok<any[]> | Response.BadRequest<string>
> = route.get("/dealer-map/:dealer").handler(async (request) => {
  const collection = await getCollection(mpnCategoryMappingsCollectionName);

  const result = await collection
    .find({
      dealer: request.routeParams.dealer,
    })
    .toArray();

  return Response.ok(result);
});

export const getByKey: Route<
  Response.Ok<MpnCategoryInTree> | Response.BadRequest<string>
> = route.get("/:key").handler(async (request) => {
  const categoriesCollection = await getCollection(mpnCategoriesCollectionName);

  const category = await categoriesCollection.findOne<MpnCategory>({
    key: request.routeParams.key,
  });
  let parentObject = null;
  if (category.parent) {
    parentObject = await categoriesCollection.findOne<MpnCategory>({
      key: category.parent,
    });
  }
  const children = await categoriesCollection
    .find<MpnCategory>({
      parent: request.routeParams.key,
    })
    .toArray();

  return Response.ok({ ...category, children, parentObject });
});

const putDealerMappingBody = t.type({
  source: t.string,
  target: t.string,
  context: t.string,
  dealer: t.string,
});

export const setMapping: Route<
  Response.Ok<any> | Response.Created<any> | Response.BadRequest<string>
> = route
  .put("/dealer-map")
  .use(Parser.body(putDealerMappingBody))
  .handler(async (request) => {
    const categoriesCollection = await getCollection(
      mpnCategoryMappingsCollectionName,
    );

    const mapping = {
      source: request.body.source,
      context: request.body.context,
      dealer: request.body.dealer,
    };

    const cursor = await categoriesCollection.updateOne(
      {
        source: request.body.source,
        target: request.body.target,
        context: request.body.context,
        dealer: request.body.dealer,
      },
      {
        $set: mapping,
      },
      { upsert: true },
    );

    if (cursor.upsertedCount === 1) {
      return Response.created(mapping);
    }
    return Response.ok(mapping);
  });
