const mongodb = require("mongodb");

const {
  mongoHost,
  mongoPort,
  mongoUser,
  mongoPassword,
  mongoDatabase,
} = require("./vars");

const getMongoUri = () => {
  if (!mongoHost || !mongoPort) throw "No mongo host";
  else if (!!mongoUser && mongoUser !== "undefined")
    return `mongodb://${mongoUser}:${mongoPassword}@${mongoHost}:${mongoPort}`;
  else return `mongodb://${mongoHost}:${mongoPort}`;
};
const mongoUri = getMongoUri();
console.log(`Connecting to: ${mongoUri}`);
const client = new mongodb.MongoClient(mongoUri);

module.exports.getCollection = async (collectionName) => {
  await client.connect();
  const db = client.db(mongoDatabase);
  return db.collection(collectionName);
};
