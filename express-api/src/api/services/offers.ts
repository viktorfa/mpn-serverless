import { getCollection } from "@/config/mongo";
import { flatten, uniqBy } from "lodash";
import { ObjectId, Filter } from "mongodb";
import { defaultOfferProjection } from "@/api/models/mpnOffer.model";
import {
  offerCollectionName,
  offerTagsCollectionName,
} from "@/api/utils/constants";
import { getDaysAhead, getNowDate, isMongoUri } from "@/api/utils/helpers";
import { getBiRelationsForOfferUris } from "@/api/services/offer-relations";
import { searchWithMongo } from "./search";

const getFindOneFilter = (
  id: string,
): Record<"_id", ObjectId> | Record<"uri", { $in: string[] }> => {
  if (isMongoUri(id)) {
    return { _id: new ObjectId(id) };
  } else {
    const [dealer, type, provenanceId] = id.split(":");
    const capitalizedProvenanceId = provenanceId.toUpperCase();
    const uriWithCapitalizedProvenanceId = [
      dealer,
      type,
      capitalizedProvenanceId,
    ].join(":");
    return { uri: { $in: [id, uriWithCapitalizedProvenanceId] } };
  }
};

export const findOne = async (id: string): Promise<MpnMongoOffer> => {
  const offersCollection = await getCollection(offerCollectionName);
  let filter = getFindOneFilter(id);
  const offer = await offersCollection.findOne<MpnMongoOffer>(filter, {
    projection: defaultOfferProjection,
  });
  if (!offer) {
    return null;
  }
  const offerWithDealer = await addDealerToOffers({ offers: [offer] });
  return offerWithDealer[0];
};
export const findOneFull = async (id: string): Promise<FullMpnOffer> => {
  const offersCollection = await getCollection(offerCollectionName);
  let filter = getFindOneFilter(id);
  const offer = await offersCollection.findOne<FullMpnOffer>(filter);
  if (!offer) {
    return null;
  }
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
  const offersCollection = await getCollection(offerCollectionName);
  const offers = await offersCollection
    .find(selection)
    .project(projection)
    .sort(sort)
    .limit(limit)
    .toArray();

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
export const addPricingToOffers = async <T = MpnOffer>({ offers }) => {
  const offerUris = offers.map((x) => x.uri);
  const pricingHistoriesCollection = await getCollection(
    "offerpricinghistories",
  );
  const pricingHistories = await pricingHistoriesCollection
    .find({ uri: { $in: offerUris } })
    .toArray();
  const pricingHistoriesMap = {};
  pricingHistories.forEach((x) => {
    pricingHistoriesMap[x.uri] = x;
  });

  const result = offers.map((offer) => {
    return {
      ...offer,
      pricingHistory: pricingHistoriesMap[offer.uri],
    };
  });

  return result;
};

export const findSimilarPromoted = async ({
  uri,
  limit,
  market,
}: {
  uri: string;
  market: string;
  limit: number;
}): Promise<MpnResultOffer[] | null> => {
  let offer: FullMpnOffer;
  try {
    offer = await findOneFull(uri);
    if (!offer) {
      throw new Error();
    }
  } catch (e) {
    return null;
  }
  const mongoSearchResponse = await searchWithMongo({
    query: offer.title.substring(0, 127),
    markets: [market],
    limit,
    isPartner: true,
  });
  mongoSearchResponse.items = mongoSearchResponse.items.filter(
    (x) => x.uri !== uri,
  );
  const resultWithDealer = await addDealerToOffers({
    offers: mongoSearchResponse.items,
  });
  return resultWithDealer;
};

export const filterIdenticalOffers = ({
  offers,
  excludeUris = [],
}: {
  offers: MpnResultOffer[];
  excludeUris?: string[];
}): MpnResultOffer[] => {
  const uniqueOffers = uniqBy(
    offers,
    (offer) => offer.title + offer.dealer + offer.pricing.price,
  );
  if (excludeUris.length > 0) {
    return uniqueOffers.filter((offer) => !excludeUris.includes(offer.uri));
  } else {
    return uniqueOffers;
  }
};
