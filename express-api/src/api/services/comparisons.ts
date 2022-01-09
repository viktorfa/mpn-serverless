import _ from "lodash";

import {
  categoryComparisonsCollectionName,
  offerCollectionName,
} from "@/api/utils/constants";
import { getCollection } from "@/config/mongo";
import { defaultOfferProjection } from "@/api/models/mpnOffer.model";

export const getComparisonConfig = async (
  categories?: string[],
): Promise<ComparisonConfig[]> => {
  const borsCollection = await getCollection(categoryComparisonsCollectionName);
  if (categories) {
    return borsCollection
      .find<ComparisonConfig>({ category: { $in: categories } })
      .toArray();
  } else {
    return borsCollection.find<ComparisonConfig>({}).toArray();
  }
};
export const getComparisonInstance = async (
  categories: string[],
): Promise<ComparisonInstance[]> => {
  const now = new Date();

  const comparisonConfig = await getComparisonConfig(categories);

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

  const offerMap: { [key: string]: MpnOffer } = {};
  offers.forEach((offer) => {
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
