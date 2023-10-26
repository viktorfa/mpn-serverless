import { getCollection, connectToMongo } from "@/config/mongo";

const deleteAll = async ({ collectionName }: { collectionName: string }) => {
  const collection = await getCollection(collectionName);

  const deleteResult = await collection.deleteMany({
    updatedAt: { $gt: new Date("2023-07-09") },
    items_scraped: { $lt: 200 },
  });

  return deleteResult;
};
const updateMany = async ({ collectionName }: { collectionName: string }) => {
  const collection = await getCollection(collectionName);

  const deleteResult = await collection.updateMany(
    {
      enabled: { $ne: false },
    },
    { $set: { enabled: true } },
  );

  return deleteResult;
};

deleteAll({ collectionName: "spiderruns" })
  .then((res) => console.log(res))
  .catch((e) => console.error(e))
  .finally(() => {
    connectToMongo().then((client) => client.close());
  });
