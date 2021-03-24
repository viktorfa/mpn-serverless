const _ = require("lodash");
const { defaultOfferCollection } = require("../utils/constants");
const { getCollection } = require("../config/mongo");

const Sentry = require("@sentry/serverless");

Sentry.AWSLambda.init({
  tracesSampleRate: 1.0,
});

const secretValue = "mrworldwidemrworldwidemrworldwide";

const handleFeed = async (event) => {
  const secret = event.headers["x-mpn-secret"];
  if (secret !== secretValue) {
    return {
      statusCode: 401,
    };
  }

  const { collectionName } = event.queryStringParameters;
  if (!collectionName) {
    return {
      statusCode: 400,
    };
  }
  const analData = JSON.parse(event.body);
  const offerCollection = await getCollection(defaultOfferCollection);

  const updates = Object.entries(analData).map(([path, data]) => {
    return {
      updateOne: {
        filter: {
          uri: decodeURIComponent(_.last(path.split("/").filter((x) => !!x))),
        },
        update: {
          $set: { pageviews: Number.parseInt(data.Pageviews) },
        },
        upsert: false,
      },
    };
  });
  const result = await offerCollection.bulkWrite(updates);
  return { body: JSON.stringify(result), statusCode: 200 };
};

module.exports = {
  handleFeed: Sentry.AWSLambda.wrapHandler(handleFeed),
};
