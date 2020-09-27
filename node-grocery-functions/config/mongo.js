const mongodb = require("mongodb");

const { mongoUri, mongoDatabase } = require("./vars");

/**
 * @type {mongodb.MongoClient}
 */
let client = null;

/**
 * @returns {Promise<mongodb.MongoClient>}
 */
const connectToMongo = async () => {
  if (!client || !client.isConnected()) {
    console.log(`Connecting to: ${mongoUri}`);
    client = await mongodb.MongoClient.connect(mongoUri, {
      useUnifiedTopology: true,
    });
  }
  return client;
};

/**
 *
 * @param {string} collectionName
 * @returns {Promise<import("@/types").CollectionWithClose>}
 */
const getCollection = async (collectionName) => {
  const _client = await connectToMongo();
  const db = _client.db(mongoDatabase);
  /**@type {import("@/types").CollectionWithClose} */
  const mongoCollection = db.collection(collectionName);
  mongoCollection.close = _client.close.bind(_client);
  return mongoCollection;
};

module.exports = {
  getCollection,
};
