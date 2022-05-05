const { MongoClient } = require("mongodb");

const { mongoUri, mongoDatabase } = require("./vars");

/**
 * @type {MongoClient}
 */
let client = null;

/**
 * @returns {Promise<MongoClient>}
 */
const connectToMongo = async () => {
  if (!client || !client.isConnected()) {
    console.log(`Connecting to: ${mongoUri}`);
    client = await MongoClient.connect(mongoUri, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
      keepAlive: true,
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
