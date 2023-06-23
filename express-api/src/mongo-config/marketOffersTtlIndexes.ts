import { getCollection } from "../config/mongo";
const marketOffersCollections = [
  "mpnoffers_au",
  "mpnoffers_de",
  "mpnoffers_dk",
  "mpnoffers_es",
  "mpnoffers_fi",
  "mpnoffers_fr",
  "mpnoffers_it",
  "mpnoffers_nl",
  "mpnoffers_no",
  "mpnoffers_pl",
  "mpnoffers_se",
  "mpnoffers_sg",
  "mpnoffers_th",
  "mpnoffers_uk",
  "mpnoffers_us",
];

const createValidThroughTtlIndexes = async () => {
  const promises = [];
  for (const collectionName of marketOffersCollections) {
    const collection = await getCollection(collectionName);
    promises.push(
      collection.createIndex(
        { validThrough: 1 },
        { expireAfterSeconds: 60 * 60, name: "validThrough_1_ttl" },
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
