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
  path: path.join(__dirname, `${dotenvFileName}`),
});

module.exports = () => {
  return {
    stage: process.env.NODE_ENV === "production" ? "prod" : "dev",
    logRetentionInDays: process.env.NODE_ENV === "production" ? 30 : 1,
    bucketName:
      process.env.NODE_ENV === "production"
        ? "grocery-prices"
        : "grocery-prices-dev",
    cloudfrontDistributionId: "EJ3SPZ8KPRUKZ",
    mongoCollection: "groceryoffer",
  };
};
