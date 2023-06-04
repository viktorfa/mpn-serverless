import * as t from "io-ts";
import { Response, Route, route, Parser } from "typera-express";
import { getCollection } from "@/config/mongo";
import {
  mpnCategoriesCollectionName,
  mpnCategoryMappingsCollectionName,
  offerCollectionName,
} from "../utils/constants";
import { Filter } from "mongodb";
import { groupBy, take } from "lodash";

const categoriesQueryParams = t.type({
  level: t.union([t.string, t.undefined]),
  parent: t.union([t.string, t.undefined]),
  context: t.union([t.string, t.undefined]),
  includeInactive: t.union([t.string, t.undefined]),
});

export const list: Route<
  Response.Ok<MpnCategory[]> | Response.BadRequest<string>
> = route
  .get("/")
  .use(Parser.query(categoriesQueryParams))
  .handler(async (request) => {
    const {
      level,
      parent,
      context,
      includeInactive: includeInactiveString = "false",
    } = request.query;
    const includeInactive = includeInactiveString === "true";

    const categoriesCollection = await getCollection(
      mpnCategoriesCollectionName,
    );
    const filter: Filter<MpnCategory> = { active: { $ne: false } };
    if (includeInactive) {
      delete filter.active;
    }
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

const dealerCategoriesQueryParams = t.type({
  level: t.union([t.string, t.undefined]),
});

export const getAllCategoriesForDealer: Route<
  | Response.Ok<{ categories: string[]; count: number }[]>
  | Response.BadRequest<string>
> = route
  .get("/dealer/:dealer")
  .use(Parser.query(dealerCategoriesQueryParams))
  .handler(async (request) => {
    const offerCollection = await getCollection(offerCollectionName);
    const level = request.query.level
      ? Number.parseInt(request.query.level)
      : null;
    const now = new Date();

    const offers = await offerCollection
      .find({
        validThrough: { $gt: now },
        isRecent: true,
        dealer: request.routeParams.dealer,
      })
      .project({ categories: 1 })
      .toArray();
    const offersWithJsonCategories = offers
      .map((x) => {
        if (x.categories && x.categories.length > 0) {
          const categories = Number.isInteger(level)
            ? take(x.categories, level + 1)
            : x.categories;
          return { categories: JSON.stringify(categories) };
        } else {
          return { categories: null };
        }
      })
      .filter((x) => !!x.categories);
    const categoryGroupedOffers = groupBy(
      offersWithJsonCategories,
      "categories",
    );
    const result: { categories: string[]; count: number }[] = [];
    Object.entries(categoryGroupedOffers).forEach(
      ([categoriesString, offers]) => {
        result.push({
          categories: JSON.parse(categoriesString),
          count: offers.length,
        });
      },
    );

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

export const getDealersForContext: Route<
  Response.Ok<any[]> | Response.BadRequest<string>
> = route.get("/dealers/:siteCollection").handler(async (request) => {
  const collection = await getCollection(offerCollectionName);

  const offers = await collection
    .find({
      validThrough: { $gt: new Date() },
      isRecent: true,
      siteCollection: request.routeParams.siteCollection,
    })
    .project({ dealer: 1 })
    .limit(100000)
    .toArray();

  const result = new Set([]);

  offers.forEach((x) => {
    result.add(x.dealer);
  });

  return Response.ok(Array.from(result));
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
  source: t.array(t.string),
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
