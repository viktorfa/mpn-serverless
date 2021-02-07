const path = require("path");
const dotenv = require("dotenv-safe");

let dotenvFileName = ".env.development";
switch (process.env.NODE_ENV) {
  case "production":
    dotenvFileName = ".env.production";
    break;
  case "test":
    dotenvFileName = ".env.test";
    break;
}
dotenv.config({
  path: dotenvFileName,
});

module.exports = {
  mongoUri: process.env.MONGO_URI,
  mongoDatabase: process.env.MONGO_DATABASE,
  bucketName: process.env.BUCKET_NAME,
  cloudFrontDistributionId: process.env.CLOUD_FRONT_DISTRIBUTION_ID,
  stage: process.env.STAGE,

  elasticUrl: process.env.ELASTIC_URL,
  elasticApiKey: process.env.ELASTIC_API_KEY,
};
