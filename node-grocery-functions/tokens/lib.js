const lunr = require("lunr");
const { S3Client, PutObjectCommand } = require("@aws-sdk/client-s3");
const {
  CloudFrontClient,
  CreateInvalidationCommand,
} = require("@aws-sdk/client-cloudfront");

const { preprocessHeading, getTokens, getBigrams } = require("./tokens");

const s3 = new S3Client(); // specify your AWS region
const cloudfront = new CloudFrontClient(); // specify your AWS region

const createProductObjects = (products, key = "uri") => {
  const result = {};
  products.forEach((product) => {
    result[product[key]] = product;
  });
  return result;
};

const saveToS3 = async (Bucket, Key, Body) => {
  const command = new PutObjectCommand({
    Bucket,
    Key,
    Body,
    ContentType: "application/json",
  });

  try {
    const result = await s3.send(command);
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
  return lunr(function () {
    this.pipeline.remove(lunr.stemmer);
    this.pipeline.remove(lunr.stopWordFilter);
    fields.forEach((field) => {
      this.field(field);
    });
    this.ref(ref);
    products.forEach((product) => {
      this.add({
        [ref]: product[ref],
        ...fields.reduce(
          (acc, field) => ({ ...acc, [field]: product[field] }),
          {},
        ),
      });
    });
  });
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
  const command = new CreateInvalidationCommand({
    DistributionId,
    InvalidationBatch: {
      CallerReference: new Date().getTime().toString(),
      Paths: {
        Quantity: paths.length,
        Items: paths,
      },
    },
  });

  try {
    const response = await cloudfront.send(command);
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
