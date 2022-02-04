import { Collection, MongoClient } from "mongodb";

import { mongoUri, mongoDatabase } from "./vars";

let client: MongoClient = new MongoClient();

const connectToMongo = async (): Promise<MongoClient> => {
  if (!client || !client.isConnected()) {
    client = await MongoClient.connect(mongoUri, {
      keepAlive: true,
      useNewUrlParser: true,
      useUnifiedTopology: true,
    });
  } else {
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
