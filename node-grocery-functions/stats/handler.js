const _ = require("lodash");
const { getCollection } = require("../config/mongo");
const secretValue = "mrworldwidemrworldwidemrworldwide";

module.exports.handleFeed = async (event) => {
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
  const offerCollection = await getCollection(collectionName);

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
