const { getCollection } = require("./config/mongo");

const { bucketName, cloudFrontDistributionId } = require("./config/vars");

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
};

const updateAutocompleteInS3 = async (autocompleteData, prefix) => {
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
) => {
  console.info(`Processing ${productCollectionName} with prefix ${prefix}`);
  const productCollection = await getCollection(productCollectionName);

  const allProducts = await productCollection
    .find({
      validThrough: {
        $gt: new Date(),
      },
    })
    .toArray();

  console.info(`Fetched ${allProducts.length} products from database`);

  const autocompleteData = getAutocompleteData(allProducts);
  const mongoUpdatePromise = updateAutocompleteInMongo(
    autocompleteData,
    productCollectionName,
  );
  if (storeInS3 === true) {
    return Promise.all([
      updateAutocompleteInS3(autocompleteData, prefix),
      mongoUpdatePromise,
    ]);
  }
  return mongoUpdatePromise;
};

module.exports = {
  processProducts,
};
