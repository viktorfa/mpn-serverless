import { getCollection } from "../config/mongo";

const offersWithRelationsCollections = [
  "relations_with_offers_au",
  "relations_with_offers_de",
  "relations_with_offers_dk",
  "relations_with_offers_es",
  "relations_with_offers_fi",
  "relations_with_offers_fr",
  "relations_with_offers_it",
  "relations_with_offers_nl",
  "relations_with_offers_no",
  "relations_with_offers_pl",
  "relations_with_offers_se",
  "relations_with_offers_sg",
  "relations_with_offers_th",
  "relations_with_offers_uk",
  "relations_with_offers_us",
];

const createUpdatedAtTtlIndexes = async () => {
  const promises = [];
  for (const collectionName of offersWithRelationsCollections) {
    const collection = await getCollection(collectionName);
    promises.push(
      collection.createIndex(
        { updatedAt: 1 },
        { expireAfterSeconds: 60 * 60 * 24 * 14, name: "updatedAt_1_ttl" },
      ),
    );
  }
  const result = await Promise.all(promises);
  return result;
};

const createValidThroughTtlIndexes = async () => {
  const promises = [];
  for (const collectionName of offersWithRelationsCollections) {
    const collection = await getCollection(collectionName);
    promises.push(
      collection.createIndex(
        { validThrough: 1 },
        { expireAfterSeconds: 1, name: "validThrough_1_ttl", sparse: true },
      ),
    );
  }
  const result = await Promise.all(promises);
  return result;
};

createValidThroughTtlIndexes()
  .then((indexes) => {
    console.log(indexes);
    process.exit(0);
  })
  .catch((e) => console.error(e));
