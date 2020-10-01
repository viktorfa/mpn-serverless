import _ from "lodash";
import * as t from "io-ts";
import { Parser, Response, Route, route, URL } from "typera-express";
import {
  findOne,
  findOneFull,
  getOffersCollection,
  getPromotionsCollection,
} from "@/api/services/offers";
import { search as searchElastic } from "@/api/services/search";
import { defaultOfferProjection } from "../models/mpnOffer.model";
import { getNowDate } from "../utils/helpers";
import { DEFAULT_PRODUCT_COLLECTION } from "../utils/constants";
import { getEngineName } from "@/api/controllers/search.controller";

const offersQueryParams = t.type({
  productCollection: t.union([t.string, t.undefined]),
});

export const list: Route<
  Response.Ok<MpnOffer[]> | Response.BadRequest<string>
> = route
  .get("/")
  .use(Parser.query(offersQueryParams))
  .handler(async (request) => {
    const { productCollection = DEFAULT_PRODUCT_COLLECTION } = request.query;

    const offersCollection = await getOffersCollection(productCollection);

    const now = getNowDate();
    const offers = await offersCollection
      .find<MpnOffer>({ validThrough: { $gte: now } })
      .project(defaultOfferProjection)
      .limit(16)
      .toArray();
    return Response.ok(offers);
  });

const similarOffersQueryParams = t.type({
  productCollection: t.union([t.string, t.undefined]),
  useSearch: t.union([t.string, t.undefined]),
});

export const similar: Route<
  | Response.Ok<MpnOffer[]>
  | Response.BadRequest<string>
  | Response.NotFound<string>
> = route
  .get("/similar/", URL.str("id"))
  .use(Parser.query(similarOffersQueryParams))
  .handler(async (request) => {
    const { productCollection = DEFAULT_PRODUCT_COLLECTION } = request.query;
    const useSearch = ["1", "true"].includes(request.query.useSearch);

    const offersCollection = await getOffersCollection(productCollection);

    let offer: FullMpnOffer;
    try {
      offer = await findOneFull(request.routeParams.id, productCollection);
      if (!offer) {
        throw new Error();
      }
    } catch (e) {
      return Response.notFound(
        `Could not find offer with id ${request.routeParams.id}`,
      );
    }

    const offerHasSimilarOffers =
      offer.similarOffers && offer.similarOffers.length > 0;

    if (!offerHasSimilarOffers) {
      console.warn(
        `Offer ${request.routeParams.id} did not have any similar offers.`,
      );
    }

    if (useSearch === true || !offerHasSimilarOffers) {
      return Response.ok(
        await searchElastic(offer.title, getEngineName(productCollection), 32),
      );
    }

    const now = getNowDate();
    const similarOffersUris = offer.similarOffers.map((x) => x.uri);
    const pipeline = [
      {
        $match: {
          _id: { $ne: offer._id },
          uri: { $in: similarOffersUris },
          validThrough: { $gte: now },
        },
      },
      {
        $addFields: { __order: { $indexOfArray: [similarOffersUris, "$uri"] } },
      },
      { $sort: { __order: 1 } },
      {
        $project: defaultOfferProjection,
      },
    ];
    const similarOffers = await offersCollection.aggregate(pipeline).toArray();

    if (similarOffers.length === 0) {
      console.warn(
        `Offer ${request.routeParams.id} did not have any time valid similar offers.`,
      );
      return Response.ok(
        await searchElastic(offer.title, getEngineName(productCollection), 32),
      );
    }
    const result = similarOffers.map((x, i) => ({
      ...x,
      score: offer.similarOffers[i].score,
    }));

    return Response.ok(result);
  });

export const promoted: Route<
  Response.Ok<MpnOffer[]> | Response.BadRequest<string>
> = route
  .get("/promoted")
  .use(Parser.query(offersQueryParams))
  .handler(async (request) => {
    const { productCollection = DEFAULT_PRODUCT_COLLECTION } = request.query;

    const promotionCollection = await getPromotionsCollection(
      productCollection,
    );
    const now = getNowDate();
    const promotions = await promotionCollection
      .find({
        validThrough: { $gte: now },
      })
      .sort({ select_method: -1 }) // Get offers with manual select method first
      .limit(32)
      .toArray();

    const strippedProductCollection = productCollection.endsWith("s")
      ? `${productCollection.substring(0, productCollection.length - 1)}`
      : productCollection;

    const promotionIds = promotions.map((x) => x[strippedProductCollection]);
    const manualPromotionIdStrings = promotions
      .filter((x) => x.select_method === "manual")
      .map((x) => x[strippedProductCollection].toString());

    const offerCollection = await getOffersCollection(productCollection);

    const promotedOffers = await offerCollection
      .find<MpnMongoOffer>({
        _id: { $in: promotionIds },
        validThrough: { $gte: now },
      })
      .project(defaultOfferProjection)
      .toArray();

    // Return sorted with manual promotions first
    const result = _.sortBy(promotedOffers, (offer) =>
      manualPromotionIdStrings.includes(offer._id.toString()) ? -1 : 1,
    );

    return Response.ok(result);
  });

export const find: Route<
  Response.Ok<MpnOffer> | Response.NotFound | Response.BadRequest<string>
> = route
  .get("/", URL.str("id"))
  .use(Parser.query(offersQueryParams))
  .handler(async (request) => {
    const { productCollection = DEFAULT_PRODUCT_COLLECTION } = request.query;

    try {
      const offer = await findOne(request.routeParams.id, productCollection);
      return Response.ok(offer);
    } catch (e) {
      return Response.notFound();
    }
  });
