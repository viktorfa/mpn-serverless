const lunr = require("lunr");
const AWS = require("aws-sdk");

const { preprocessHeading, getTokens, getBigrams } = require("./tokens");

const cloudfront = new AWS.CloudFront();
const s3 = new AWS.S3();

const createProductObjects = (products, key = "uri") => {
  const result = {};
  products.forEach((product) => {
    result[product[key]] = product;
  });
  return result;
};

const saveToS3 = async (Bucket, Key, Body) => {
  try {
    const result = await s3
      .putObject({
        Bucket,
        Key,
        Body,
        ContentType: "application/json",
      })
      .promise();

    return {
      ok: true,
      data: result,
    };
  } catch (error) {
    return {
      ok: false,
      error,
    };
  }
};

const getLunrIndex = (products, fields = ["title"], ref = "uri") => {
  const index = lunr(function() {
    const lunrContext = this;
    lunrContext.pipeline.remove(lunr.stemmer);
    lunrContext.pipeline.remove(lunr.stopWordFilter);
    fields.forEach((field) => {
      lunrContext.field(field);
    });
    lunrContext.ref(ref);
    products.forEach((product) => {
      lunrContext.add({
        [ref]: product[ref],
        ...fields.reduce(
          (acc, field) => ({ ...acc, [field]: product[field] }),
          {},
        ),
      });
    });
  });

  return index;
};

const getAutocompleteData = (products) => {
  let heading_tokens = new Set();
  let heading_bigrams = new Set();
  const heading_fullgrams = new Set();
  products.forEach((product) => {
    const tokens = getTokens(preprocessHeading(product.title));
    tokens.forEach((x) => heading_tokens.add(x));
    getBigrams(tokens).forEach((x) => heading_bigrams.add(x));
    heading_fullgrams.add(tokens.join(" "));
  });

  return {
    heading_tokens: [...heading_tokens],
    heading_bigrams: [...heading_bigrams],
    heading_fullgrams: [...heading_fullgrams],
  };
};

const invalidateCloudFrontDistribution = async (paths, DistributionId) => {
  const params = {
    DistributionId,
    InvalidationBatch: {
      CallerReference: new Date().getTime().toString(),
      Paths: {
        Quantity: paths.length,
        Items: paths,
      },
    },
  };
  try {
    const response = await cloudfront.createInvalidation(params).promise();
    return {
      ok: true,
      data: response,
    };
  } catch (error) {
    return {
      ok: false,
      error,
    };
  }
};

module.exports = {
  createProductObjects,
  getLunrIndex,
  getAutocompleteData,
  saveToS3,
  invalidateCloudFrontDistribution,
};
