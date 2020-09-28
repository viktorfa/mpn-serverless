const get = require("lodash/get");

const { reverseString } = require("../utils");
const { getCollection } = require("../config/mongo");
const { bucketName, cloudFrontDistributionId } = require("../config/vars");
const {
  getAutocompleteData,
  saveToS3,
  invalidateCloudFrontDistribution,
} = require("./lib");

const updateAutocompleteInMongo = async (
  autocompleteData,
  productCollectionName,
) => {
  const autocompleteCollection = await getCollection("autocompletedata");
  const autocompleteUpsertCursor = await autocompleteCollection.findOneAndUpdate(
    { productCollection: productCollectionName },
    { $set: { tokens: autocompleteData } },
    { upsert: true },
  );
  console.info("Updated autocomplete data in mongo");
  console.info(autocompleteUpsertCursor);
  return autocompleteUpsertCursor;
};
const updateAutocompleteTermsInMongo = async (
  autocompleteData,
  productCollectionName,
) => {
  const now = new Date();
  const collection = await getCollection("autocompleteterms");
  console.info("Updating autocomplete terms in mongo");
  const termUpserts = get(autocompleteData, ["heading_tokens"], []).map(
    (term) => {
      return {
        updateOne: {
          filter: {
            term,
            tokenType: "headingToken",
            productCollection: productCollectionName,
          },
          update: {
            $set: {
              term,
              reverseTerm: reverseString(term),
              tokenType: "headingToken",
              productCollection: productCollectionName,
              updatedAt: now,
            },
          },
          upsert: true,
        },
      };
    },
  );

  const bulkWriteResult = await collection.bulkWrite(termUpserts);
  console.info("Updated autocomplete terms in mongo");
  console.info(bulkWriteResult);
  return bulkWriteResult;
};

const updateAutocompleteInS3 = async (autocompleteData, prefix) => {
  console.info("Updating autocomplete data in S3");
  const s3Files = [
    {
      path: `${prefix}/autocomplete-data-latest.json`,
      data: JSON.stringify(autocompleteData),
    },
  ];

  const s3Promises = s3Files.map(({ path, data }) => ({
    path,
    promise: saveToS3(bucketName, path, data),
  }));

  const promiseResults = await Promise.all(
    s3Promises.map(({ promise }) => promise),
  );

  const invalidateCloudFrontResult = await invalidateCloudFrontDistribution(
    s3Files.map(({ path }) => `/${path}`),
    cloudFrontDistributionId,
  );
  promiseResults.push(invalidateCloudFrontResult);
  return promiseResults;
};

const processProducts = async (
  productCollectionName,
  prefix,
  storeInS3 = false,
  limit = 2 ** 20,
) => {
  console.info(`Processing ${productCollectionName} with prefix ${prefix}`);
  const productCollection = await getCollection(productCollectionName);

  const allProducts = await productCollection
    .find({
      validThrough: {
        $gt: new Date(),
      },
    })
    .limit(limit)
    .toArray();

  console.info(`Fetched ${allProducts.length} products from database`);

  const autocompleteData = getAutocompleteData(allProducts);
  const mongoUpdatePromise = updateAutocompleteInMongo(
    autocompleteData,
    productCollectionName,
  );
  const mongoUpdateTermsPromise = updateAutocompleteTermsInMongo(
    autocompleteData,
    productCollectionName,
  );
  const promises = [mongoUpdatePromise, mongoUpdateTermsPromise];
  if (storeInS3 === true) {
    promises.push(updateAutocompleteInS3(autocompleteData, prefix));
  }
  const fulfilledPromises = await Promise.all(promises);
  await productCollection.close();
  console.info("Promises fulfilled");
  console.info(promises);
  return fulfilledPromises;
};

module.exports = {
  processProducts,
};
