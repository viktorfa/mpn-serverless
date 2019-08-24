module.exports = {
  mongoHost: process.env.MONGO_HOST,
  mongoPort: process.env.MONGO_PORT,
  mongoUser: process.env.MONGO_USER,
  mongoPassword: process.env.MONGO_PASSWORD,
  mongoDatabase: process.env.MONGO_DATABASE,
  mongoCollection: process.env.MONGO_COLLECTION,
  bucketName: process.env.BUCKET_NAME,
  cloudFrontDistributionId: process.env.CLOUD_FRONT_DISTRIBUTION_ID,
};
