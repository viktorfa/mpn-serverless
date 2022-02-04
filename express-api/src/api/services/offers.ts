import { getCollection } from "@/config/mongo";
import { flatten } from "lodash";
import { ObjectId, Filter } from "mongodb";
import { defaultOfferProjection } from "@/api/models/mpnOffer.model";
import {
  offerCollectionName,
  offerTagsCollectionName,
} from "@/api/utils/constants";
import { getDaysAhead, getNowDate, isMongoUri } from "@/api/utils/helpers";
import { getBiRelationsForOfferUris } from "@/api/services/offer-relations";

const getFindOneFilter = (
  id: string,
): Record<"_id", ObjectId> | Record<"uri", string> => {
  if (isMongoUri(id)) {
    return { _id: new ObjectId(id) };
  } else {
    return { uri: id };
  }
};

export const findOne = async (id: string): Promise<MpnMongoOffer> => {
  const offersCollection = await getCollection(offerCollectionName);
  let filter = getFindOneFilter(id);
  const offer = await offersCollection.findOne<MpnMongoOffer>(filter, {
    projection: defaultOfferProjection,
  });
  const offerWithDealer = await addDealerToOffers({ offers: [offer] });
  return offerWithDealer[0];
};
export const findOneFull = async (id: string): Promise<FullMpnOffer> => {
  const offersCollection = await getCollection(offerCollectionName);
  let filter = getFindOneFilter(id);
  const offer = await offersCollection.findOne<FullMpnOffer>(filter);
  const offerWithDealer = await addDealerToOffers({ offers: [offer] });
  return offerWithDealer[0] as FullMpnOffer;
};

export const getOffersForSiteCollection = async (
  siteCollection: string,
  selection: Filter<MpnOffer> = {},
  projection = defaultOfferProjection,
  limit: number = 30,
): Promise<MpnOffer[]> => {
  const now = getNowDate();
  selection.validThrough = { $gte: now };
  selection.siteCollection = siteCollection;
  return getOffers(selection, projection, limit);
};

export const getOffers = async (
  selection: Filter<MpnMongoOffer> = {},
  projection = defaultOfferProjection,
  limit = 30,
  includeExpired = false,
): Promise<MpnOffer[]> => {
  const offersCollection = await getCollection(offerCollectionName);
  if (!includeExpired) {
    const now = getNowDate();
    selection.validThrough = { $gte: now };
  }
  return offersCollection
    .find(selection)
    .project<MpnOffer>(projection)
    .limit(limit)
    .toArray();
};

export const getOffersByUris = async (
  uris: string[],
  filter: object = {},
  projection: any = defaultOfferProjection,
  includeExpired = false,
): Promise<MpnOffer[]> => {
  const selection = {
    ...filter,
    uri: { $in: uris },
  };
  return getOffers(selection, projection, uris.length, includeExpired);
};

export const getOfferUrisForTags = async (
  tags: string[],
  limit: number = 128,
): Promise<string[]> => {
  const tagsCollection = await getCollection(offerTagsCollectionName);

  const now = getNowDate();
  const tagObjects = await tagsCollection
    .find({
      tag: { $in: tags },
      $or: [{ validThrough: { $gte: now } }],
    })
    .limit(limit)
    .toArray();
  return tagObjects.map((x) => x.uri);
};

export const getOffersWithTags = async (
  tags: string[],
): Promise<MpnOffer[]> => {
  return getOffersByUris(await getOfferUrisForTags(tags));
};

export const addTagToOffers = async (offerUris: string[], tag: string) => {
  const tagsCollection = await getCollection(offerTagsCollectionName);

  const writeOperations = offerUris.map((uri) => {
    const update: Record<string, any> = {
      $set: {
        tag,
        uri,
        selectionType: "manual",
        status: "enabled",
      },
    };
    if (["promotion_good-offer", "promoted"].includes(tag)) {
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
export const removeTagFromOffers = async (offerUris: string[], tag: string) => {
  const tagsCollection = await getCollection(offerTagsCollectionName);

  const writeOperations = offerUris.map((uri) => {
    const update: Record<string, any> = {
      $set: {
        tag,
        uri,
        selectionType: "manual",
        status: "disabled",
      },
    };
    return {
      updateOne: {
        filter: {
          tag,
          uri,
        },
        update,
      },
    };
  });

  return tagsCollection.bulkWrite(writeOperations);
};

export const getTagsForOffer = async (uri: string): Promise<OfferTag[]> => {
  const tagsCollection = await getCollection(offerTagsCollectionName);

  const now = getNowDate();

  return tagsCollection
    .find<OfferTag>({
      uri,
      $or: [
        { validThrough: { $gte: now } },
        { validThrough: { $exists: false } },
      ],
    })
    .toArray();
};

export const getOffersInUriGroups = async (
  offerGroups: UriOfferGroup[],
  filter: object = {},
): Promise<SimilarOffersObject[]> => {
  const uris = flatten(offerGroups.map((x) => x.uris));

  const offers = await getOffersByUris(uris, filter, defaultOfferProjection);

  const offersWithDealer = await addDealerToOffers({ offers });

  const uriToOfferMap = offersWithDealer.reduce((acc, offer) => {
    return { ...acc, [offer.uri]: offer };
  }, {});

  const result: SimilarOffersObject[] = [];
  offerGroups.forEach((offerGroup) => {
    const groupOffers = offerGroup.uris
      .filter((uri) => !!uriToOfferMap[uri])
      .map((uri) => uriToOfferMap[uri]);
    if (groupOffers.length > 0) {
      result.push({
        offers: groupOffers,
        title: offerGroup.title ?? groupOffers[0].title,
        _id: offerGroup._id,
        relationType: offerGroup.relationType,
      });
    }
  });
  return result;
};

export const getSimilarGroupedOffersFromOfferUris = async (
  uris: string[],
  filter: object = {},
  biRelationFilter = {},
): Promise<SimilarOffersObject[]> => {
  const biRelationGroups = await getBiRelationsForOfferUris(
    uris,
    biRelationFilter,
  );

  const offerGroups = [...biRelationGroups];

  // Add offers that don't have any stored bi relations as belonging to a group of their own
  uris.forEach((uri) => {
    if (!biRelationGroups.some((group) => group.uris.includes(uri))) {
      offerGroups.push({ uris: [uri] });
    }
  });

  return getOffersInUriGroups(offerGroups, filter);
};

export const defaultDealerProjection = { key: 1, text: 1, logoUrl: 1, url: 1 };

export const getOffersWithDealer = async ({
  selection,
  projection = defaultOfferProjection,
  sort = {},
  limit = 30,
}) => {
  console.time();
  const offersCollection = await getCollection(offerCollectionName);
  console.timeEnd();
  console.time();
  const offers = await offersCollection
    .find(selection)
    .project(projection)
    .sort(sort)
    .limit(limit)
    .toArray();
  console.timeEnd();

  const dealerKeys = Array.from(new Set(offers.map((offer) => offer.dealer)));
  console.time();
  const dealerCollection = await getCollection("dealers");
  const dealers = await dealerCollection
    .find({ key: { $in: dealerKeys } })
    .project(defaultDealerProjection)
    .toArray();
  console.timeEnd();
  const dealerMap = {};
  dealers.forEach((dealer) => {
    dealerMap[dealer.key] = dealer;
  });

  const result = offers.map((offer) => {
    return { ...offer, dealerObject: dealerMap[offer.dealer] };
  });

  return result;
};

export const addDealerToOffers = async <T = MpnOffer>({ offers }) => {
  const dealerKeys = Array.from(new Set(offers.map((offer) => offer.dealer)));
  const dealerCollection = await getCollection("dealers");
  const dealers = await dealerCollection
    .find({ key: { $in: dealerKeys } })
    .project(defaultDealerProjection)
    .toArray();
  const dealerMap = {};
  dealers.forEach((dealer) => {
    dealerMap[dealer.key] = dealer;
  });

  const result = offers.map((offer) => {
    return {
      ...offer,
      dealerObject: dealerMap[offer.dealer] || { key: offer.dealer },
    };
  });

  return result;
};
