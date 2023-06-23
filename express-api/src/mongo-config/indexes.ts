import { getCollection } from "../config/mongo";

const listIndexes = async ({ collectionName }: { collectionName: string }) => {
  console.log(`Listing indexes for ${collectionName}`);
  const collection = await getCollection(collectionName);
  return collection.listIndexes().toArray();
};

listIndexes({ collectionName: "relations_with_offers_no" })
  .then((indexes) => {
    console.log(indexes);
    process.exit(0);
  })
  .catch((e) => console.error(e));
