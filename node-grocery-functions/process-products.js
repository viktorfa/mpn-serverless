const { getCollection } = require("./config/mongo");

const { bucketName, cloudFrontDistributionId } = require("./config/vars");

const {
  createProductObjects,
  getLunrIndex,
  getAutocompleteData,
  saveToS3,
  invalidateCloudFrontDistribution,
} = require("./lib");

const processProducts = async () => {
  const groceryOffersCollection = await getCollection("groceryoffer");

  const allProducts = await groceryOffersCollection
    .find({
      run_till: {
        $gt: new Date(),
      },
    })
    .toArray();

  console.info(`Fetched ${allProducts.length} products from database`);

  const productMap = createProductObjects(allProducts);
  const lunrIndex = getLunrIndex(allProducts);
  const autocompleteData = getAutocompleteData(allProducts);

  const s3Files = [
    {
      path: "autocomplete-data-latest.json",
      data: JSON.stringify(autocompleteData),
    },
    {
      path: "product-lunr-index-latest.json",
      data: JSON.stringify(lunrIndex.toJSON()),
    },
    {
      path: "product-map-latest.json",
      data: JSON.stringify(productMap),
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

module.exports = {
  processProducts,
};
