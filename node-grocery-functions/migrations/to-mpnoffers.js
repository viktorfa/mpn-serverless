const { defaultOfferCollection } = require("../utils/constants");
const { getCollection } = require("../config/mongo");

const migrateCollectionToMpnOffers = async (
  sourceCollectionName,
  market,
  limit = 128,
) => {
  if (!sourceCollectionName) {
    throw Error("Need sourceCollection as first arg");
  }
  if (!market) {
    throw Error("Need market as second arg");
  }
  const sourceCollection = await getCollection(sourceCollectionName);
  const targetCollection = await getCollection(defaultOfferCollection);

  const siteCollection = sourceCollectionName.endsWith("s")
    ? sourceCollectionName
    : sourceCollectionName + "s";

  const _limit = typeof limit === "string" ? Number.parseInt(limit) : limit;

  const allSourceOffers = await sourceCollection
    .find({})
    .limit(_limit)
    .project({ _id: 0 })
    .toArray();

  const upsertOperations = allSourceOffers.map((offer) => {
    return {
      updateOne: {
        filter: { uri: offer.uri },
        update: { $set: { ...offer, market, siteCollection } },
        upsert: true,
      },
    };
  });

  const bulkWriteResult = await targetCollection.bulkWrite(upsertOperations);

  console.log("bulkWriteResult");
  console.log(bulkWriteResult);
  console.log(
    `MIGRATION FROM ${sourceCollectionName} TO ${defaultOfferCollection} WITH ${allSourceOffers.length} OFFERS FINISHED`,
  );
};

const commandsArgs = process.argv.slice(2);

const argLimit = Number.parseInt(commandsArgs[2]) || undefined;

migrateCollectionToMpnOffers(commandsArgs[0], commandsArgs[1], argLimit)
  .then(() => {
    process.exit(0);
  })
  .catch((e) => {
    console.error(e);
    process.exit(-1);
  });
