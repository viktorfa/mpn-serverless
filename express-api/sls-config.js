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
    MONGO_DATABASE: process.env.MONGO_DATABASE,
    MONGO_URI: process.env.MONGO_URI,
    ELASTIC_API_KEY: process.env.ELASTIC_API_KEY,
    ELASTIC_URL: process.env.ELASTIC_URL,
    SENTRY_DSN: process.env.SENTRY_DSN,
  };
};
