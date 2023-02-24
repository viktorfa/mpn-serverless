import _ from "lodash";

import {
  categoryComparisonsCollectionName,
  offerCollectionName,
} from "@/api/utils/constants";
import { getCollection } from "@/config/mongo";
import { defaultOfferProjection } from "@/api/models/mpnOffer.model";
import { addDealerToOffers } from "@/api/services/offers";

export const getComparisonConfig = async ({
  categories,
  dealers,
  market,
  productCollection,
}: ComparisonInstanceParams): Promise<ComparisonConfig[]> => {
  const borsCollection = await getCollection(categoryComparisonsCollectionName);

  const projection: Record<string, number | boolean | Record<number, boolean>> =
    {
      title: 1,
      category: 1,
      dealers: 1,
      name: 1,
      quantityValue: 1,
      useUnitPrice: 1,
      quantityUnit: 1,
    };

  if (dealers) {
    let dealerProjection = {};
    dealers.forEach((dealerKey) => {
      dealerProjection[dealerKey] = 1;
    });
    projection.dealers = dealerProjection;
  }

  if (categories) {
    return borsCollection
      .find<ComparisonConfig>({ category: { $in: categories } })
      .project<ComparisonConfig>(projection)
      .toArray();
  } else {
    return borsCollection
      .find<ComparisonConfig>({})
      .project<ComparisonConfig>(projection)
      .toArray();
  }
};

type ComparisonInstanceParams = {
  categories: string[];
  dealers?: string[];
  market?: string;
  productCollection?: string;
};

export const getComparisonInstance = async ({
  categories,
  dealers,
  productCollection,
  market,
}: ComparisonInstanceParams): Promise<ComparisonInstance[]> => {
  const now = new Date();

  const comparisonConfig = await getComparisonConfig({ categories, dealers });

  const uris = _.flattenDeep(
    comparisonConfig.map((productConfig) => {
      return Object.values(productConfig.dealers)
        .map((dealerConfig) => _.get(dealerConfig, "uri"))
        .filter(_.identity);
    }),
  );
  const selection = {
    uri: { $in: uris },
    validThrough: {
      $gt: now,
    },
  };
  const collection = await getCollection(offerCollectionName);
  const offers = await collection
    .find(selection)
    .project<MpnOffer>(defaultOfferProjection)
    .toArray();

  const offersWithDealer = await addDealerToOffers({ offers });

  const offerMap: { [key: string]: MpnOffer } = {};
  offersWithDealer.forEach((offer) => {
    offerMap[offer.uri] = offer;
  });
  const result: ComparisonInstance[] = [];

  for (const productConfig of comparisonConfig) {
    const comparisonInstance: ComparisonInstance = {
      category: productConfig.category,
      name: productConfig.name,
      productCollection: productConfig.productCollection,
      quantityUnit: productConfig.quantityUnit,
      quantityValue: productConfig.quantityValue,
      title: productConfig.title,
      useUnitPrice: productConfig.useUnitPrice,
      dealers: {},
    };
    for (const [dealerKey, dealerConfig] of Object.entries(
      productConfig.dealers,
    )) {
      const dealerInstance = { ...dealerConfig, product: null };
      const uri = _.get(dealerConfig, "uri");
      if (uri) {
        dealerInstance.product = offerMap[uri];
      }
      comparisonInstance.dealers[dealerKey] = dealerInstance;
    }
    result.push(comparisonInstance);
  }

  return result;
};

interface OfferConfigPutParameters {
  category: string;
  name: string;
  dealer: string;
  dealerConfig: DealerConfig;
}
export const addOfferToComparisons = async (
  config: OfferConfigPutParameters,
) => {
  const borsCollection = await getCollection(categoryComparisonsCollectionName);

  return borsCollection.updateOne(
    { category: config.category, name: config.name },
    { $set: { [`dealers.${config.dealer}`]: config.dealerConfig } },
  );
};

export const createOrUpdateComparisonConfig = async (
  config: PutOfferConfig,
) => {
  const borsCollection = await getCollection(categoryComparisonsCollectionName);

  const existingConfig = await borsCollection.findOne({
    category: config.category,
    name: config.name,
  });

  if (existingConfig) {
    return borsCollection.updateOne(
      { category: config.category, name: config.name },
      { $set: { ...config } },
    );
  } else {
    return borsCollection.insertOne({ ...config, dealers: {} });
  }
};
