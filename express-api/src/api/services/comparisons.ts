import _ from "lodash";

import {
  categoryComparisonsCollectionName,
  offerCollectionName,
} from "@/api/utils/constants";
import { getCollection } from "@/config/mongo";
import { defaultOfferProjection } from "@/api/models/mpnOffer.model";

export const getComparisonConfig = async (
  categories?: string[],
): Promise<ComparisonConfig> => {
  const borsCollection = await getCollection(categoryComparisonsCollectionName);
  if (categories) {
    return borsCollection.find({ category: { $in: categories } }).toArray();
  } else {
    return borsCollection.find().toArray();
  }
};
export const getComparisonInstance = async (
  categories: string[],
): Promise<ComparisonInstance> => {
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
    .find(selection, defaultOfferProjection)
    .toArray();

  const offerMap = offers.reduce(
    (acc, offer) => ({ ...acc, [offer.uri]: offer }),
    {},
  );

  const result = [];

  for (const productConfig of comparisonConfig) {
    for (const dealerConfig of Object.values(
      productConfig.dealers,
    ) as DealerInstance[]) {
      const uri = _.get(dealerConfig, "uri");
      if (uri) {
        dealerConfig.product = offerMap[uri];
      }
    }
    result.push(productConfig);
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
