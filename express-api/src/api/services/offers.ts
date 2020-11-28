import { getCollection } from "@/config/mongo";
import { flatten } from "lodash";
import { ObjectId, Collection, FindOneOptions, FilterQuery } from "mongodb";
import { defaultOfferProjection } from "../models/mpnOffer.model";
import { getStrippedProductCollectionName } from "../models/utils";
import { getDaysAhead, getNowDate, isMongoUri } from "../utils/helpers";
import { getBiRelationsForOfferUris } from "./offer-relations";

export const getPromotionsCollection = async (
  collectionName: string,
): Promise<Collection> => {
  const promotionCollection = await getCollection(
    `${getStrippedProductCollectionName(collectionName)}promotions`,
  );
  return promotionCollection;
};

const getFindOneFilter = (
  id: string,
): Record<"_id", ObjectId> | Record<"uri", string> => {
  if (isMongoUri(id)) {
    return { _id: new ObjectId(id) };
  } else {
    return { uri: id };
  }
};

export const findOne = async (
  id: string,
  collectionName: string,
): Promise<MpnOffer> => {
  const offersCollection = await getCollection(collectionName);
  let filter = getFindOneFilter(id);
  return offersCollection.findOne<MpnOffer>(filter, {
    projection: defaultOfferProjection,
  });
};
export const findOneFull = async (
  id: string,
  collectionName: string,
): Promise<FullMpnOffer> => {
  const offersCollection = await getCollection(collectionName);
  let filter = getFindOneFilter(id);
  return offersCollection.findOne<FullMpnOffer>(filter);
};

export const getOffers = async (
  collectionName: string,
  selection: FilterQuery<FullMpnOffer> = {},
  projection: FindOneOptions<FullMpnOffer> = defaultOfferProjection,
  limit: number = 30,
): Promise<MpnOffer[]> => {
  const offersCollection = await getCollection(collectionName);
  const now = getNowDate();
  selection.validThrough = { $gte: now };
  return offersCollection.find(selection, projection).limit(limit).toArray();
};
export const getOffersByUris = async (
  uris: string[],
  collectionName: string,
  projection: FindOneOptions<FullMpnOffer> = defaultOfferProjection,
): Promise<MpnOffer[]> => {
  const selection = {
    uri: { $in: uris },
  };
  return getOffers(collectionName, selection, projection, uris.length);
};

export const getOfferUrisForTags = async (
  tags: string[],
  limit: number = 128,
): Promise<string[]> => {
  const tagsCollection = await getCollection("offertags");

  const now = getNowDate();
  const tagObjects = await tagsCollection
    .find({
      tag: { $in: tags },
      $or: [
        { validThrough: { $gte: now } },
        { validThrough: { $exists: false } },
      ],
    })
    .limit(limit)
    .toArray();
  console.log("getOfferUrisForTags");
  console.log(tagObjects);
  return tagObjects.map((x) => x.uri);
};

export const getOffersWithTags = async (
  tags: string[],
  collectionName: string,
): Promise<MpnOffer[]> => {
  return getOffersByUris(await getOfferUrisForTags(tags), collectionName);
};

export const addTagToOffers = async (offerUris: string[], tag: string) => {
  const tagsCollection = await getCollection("offertags");

  const writeOperations = offerUris.map((uri) => {
    const update: Record<string, any> = {
      $set: {
        tag,
        uri,
        selectionType: "manual",
      },
    };
    if (tag === "promoted") {
      update.$set.validThrough = getDaysAhead(14);
    }
    return {
      updateOne: {
        filter: {
          tag,
          uri,
        },
        update,
        upsert: true,
      },
    };
  });

  return tagsCollection.bulkWrite(writeOperations);
};

export const getTagsForOffer = async (uri: string): Promise<string[]> => {
  const tagsCollection = await getCollection("offertags");

  const now = getNowDate();

  return tagsCollection
    .find({
      uri,
      $or: [
        { validThrough: { $gte: now } },
        { validThrough: { $exists: false } },
      ],
    })
    .toArray();
};

export const getOffersInUriGroups = async (
  uriGroups: string[][],
  collectionName: string,
): Promise<SimilarOffersObject[]> => {
  const uris = flatten(uriGroups);

  const offers = await getOffersByUris(uris, collectionName);

  const uriToOfferMap = offers.reduce((acc, offer) => {
    return { ...acc, [offer.uri]: offer };
  }, {});

  const result: SimilarOffersObject[] = [];
  uriGroups.forEach((uris) => {
    const offers = uris
      .filter((uri) => !!uriToOfferMap[uri])
      .map((uri) => uriToOfferMap[uri]);
    if (offers.length > 0) {
      result.push({ offers, title: offers[0].title });
    }
  });
  return result;
};

export const getSimilarGroupedOffersFromOfferUris = async (
  uris: string[],
  collectionName: string,
): Promise<SimilarOffersObject[]> => {
  const biRelationGroups = await getBiRelationsForOfferUris(
    uris,
    collectionName,
  );
  console.log("uris");
  console.log(uris);

  console.log("biRelationGroups");
  console.log(biRelationGroups);

  const offerGroups = [...biRelationGroups];

  // Add offers that don't have any stored bi relations as belonging to a group of their own
  uris.forEach((uri) => {
    if (!biRelationGroups.some((group) => group.includes(uri))) {
      offerGroups.push([uri]);
    }
  });

  console.log("offerGroups");
  console.log(offerGroups);

  return getOffersInUriGroups(offerGroups, collectionName);
};
