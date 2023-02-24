import { Parser, Response, Route, route } from "typera-express";
import * as t from "io-ts";
import {
  addOfferToComparisons,
  createOrUpdateComparisonConfig,
  getComparisonConfig,
  getComparisonInstance,
} from "../services/comparisons";

const comparisonDataQueryParams = t.type({
  categories: t.union([t.string, t.undefined]),
});
const comparisonQueryParams = t.type({
  categories: t.string,
  dealers: t.union([t.string, t.undefined]),
  productCollection: t.union([t.string, t.undefined]),
  market: t.union([t.string, t.undefined]),
});

export const getData: Route<
  Response.Ok<ComparisonConfig[]> | Response.BadRequest<string>
> = route
  .get("/data")
  .use(Parser.query(comparisonDataQueryParams))
  .handler(async (request) => {
    const categories = request.query.categories
      ? request.query.categories.split(",").filter((x) => !!x)
      : null;
    return Response.ok(await getComparisonConfig({ categories }));
  });

export const getBors: Route<
  Response.Ok<ComparisonInstance[]> | Response.BadRequest<string>
> = route
  .get("/")
  .use(Parser.query(comparisonQueryParams))
  .handler(async (request) => {
    const { categories, dealers, productCollection, market } = request.query;
    const categoriesList = categories
      ? categories
          .toString()
          .split(",")
          .filter((x) => !!x)
      : null;
    const dealersList = dealers
      ? dealers
          .toString()
          .split(",")
          .filter((x) => !!x)
      : null;
    return Response.ok(
      await getComparisonInstance({
        categories: categoriesList,
        dealers: dealersList,
        productCollection,
        market,
      }),
    );
  });

const putComparisonRequestBody = t.type({
  category: t.string,
  name: t.string,
  dealer: t.string,
  dealerConfig: t.type({
    uri: t.string,
    quantityValue: t.number,
  }),
});

export const putOffer: Route<
  | Response.NoContent<any>
  | Response.BadRequest<string>
  | Response.InternalServerError<string>
> = route
  .put("/")
  .use(Parser.body(putComparisonRequestBody))
  .handler(async (request) => {
    const result = await addOfferToComparisons(request.body);
    if (result.modifiedCount > 0) {
      return Response.noContent();
    }
    return Response.internalServerError(`Could not add offer to comparison.`);
  });

const putComparisonConfigRequestBody = t.type({
  category: t.string,
  name: t.string,
  title: t.string,
  productCollection: t.string,
  useUnitPrice: t.boolean,
  quantityUnit: t.union([t.string, t.undefined]),
  quantityValue: t.union([t.number, t.undefined]),
});

export const putConfig: Route<
  | Response.NoContent<any>
  | Response.BadRequest<string>
  | Response.InternalServerError<string>
> = route
  .put("/data")
  .use(Parser.body(putComparisonConfigRequestBody))
  .handler(async (request) => {
    const result = await createOrUpdateComparisonConfig(request.body);
    if (result["modifiedCount"]) {
      return Response.noContent();
    } else if (result["insertedId"]) {
      return Response.noContent();
    }
    return Response.internalServerError(`Could not add offer to comparison.`);
  });
