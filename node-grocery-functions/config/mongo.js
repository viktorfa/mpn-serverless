const mongodb = require("mongodb");

const { mongoUri, mongoDatabase } = require("./vars");

console.log(`Connecting to: ${mongoUri}`);
const client = new mongodb.MongoClient(mongoUri, { useUnifiedTopology: true });

module.exports.getCollection = async (collectionName) => {
  await client.connect();
  const db = client.db(mongoDatabase);
  return db.collection(collectionName);
};
