module.exports = {
  mongoUri: process.env.MONGO_URI,
  mongoDatabase: process.env.MONGO_DATABASE,
  bucketName: process.env.BUCKET_NAME,
  cloudFrontDistributionId: process.env.CLOUD_FRONT_DISTRIBUTION_ID,
  stage: process.env.STAGE,

  elasticUrl: process.env.ELASTIC_URL,
  elasticApiKey: process.env.ELASTIC_API_KEY,
};
