import mongodb, { Collection, MongoClient } from "mongodb";

import { mongoUri, mongoDatabase } from "./vars";

let client: MongoClient = null;

const connectToMongo = async (): Promise<MongoClient> => {
  if (!client || !client.isConnected()) {
    console.log(`Connecting to: ${mongoUri}`);
    client = await mongodb.MongoClient.connect(mongoUri, {
      useUnifiedTopology: true,
    });
  }
  return client;
};

export const getCollection = async (
  collectionName: string,
): Promise<Collection> => {
  const _client = await connectToMongo();
  const db = _client.db(mongoDatabase);
  const mongoCollection = db.collection(collectionName);
  return mongoCollection;
};
