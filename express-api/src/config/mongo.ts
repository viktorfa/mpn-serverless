import { Collection, MongoClient } from "mongodb";

import { mongoUri, mongoDatabase } from "./vars";

const clientPromise: MongoClient = MongoClient.connect(mongoUri, {});

export const connectToMongo = async (): Promise<MongoClient> => {
  const client = await clientPromise;
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
