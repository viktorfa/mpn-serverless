const _ = require("lodash");

const { getElasticClient } = require("../config/elastic");
const { getCollection } = require("../config/mongo");
const { mpnOfferToElasticOffer } = require("./helpers");
const { stage } = require("../config/vars");
const { getMessageFromSnsEvent } = require("../utils");

const UPLOAD_TO_ELASTIC_OFFERS_CHUNK_SIZE = 100;

const includeFields = [
  "title",
  "subtitle",
  "shortDescription",
  "description",
  "brand",

  "href",
  "imageUrl",
  "uri",

  "validFrom",
  "validThrough",

  "pricing",
  "quantity",
  "value",

  "categories",
  "dealer",
  "gtins",
  "provenance",
  "mpnStock",
];

/**
 * Gets a valid engine name or an empty string.
 *
 * @param {string} engineName
 * @returns {string}
 */
const getEngineName = (engineName) => {
  let result = "";
  if (engineName.startsWith("grocery")) {
    result = "groceryoffers";
  } else if (engineName.startsWith("bygg")) {
    result = "byggoffers";
  } else if (engineName.startsWith("sebygg")) {
    result = "sebyggoffers";
  } else if (engineName.startsWith("segrocery")) {
    result = "segroceryoffers";
  } else {
    return "";
  }
  if (stage === "prod") {
    return result;
  } else {
    return `${result}-dev`;
  }
};

/**
 *
 * @param {import("@/types").DeleteElasticEvent} event
 */
const handleTriggerDeleteEvent = (event) => {
  console.info("event");
  console.info(event);
  const { engineName: _engineName, limit = 1000 } = event;

  const engineName = getEngineName(_engineName);
  if (!engineName) {
    throw new Error(`Need engineName input. Was ${engineName}`);
  }
  return deleteOldElasticOffers(engineName, limit);
};
/**
 *
 * @param {import("@/types").MigrateElasticEvent} event
 */
const handleTriggerMigrateEvent = (event) => {
  console.info("event");
  console.info(event);
  const {
    mongoCollection,
    engineName: _engineName,
    limit = 2 ** 20,
    mongoFilter = {},
  } = event;

  if (!mongoCollection) {
    throw new Error(`Need mongoCollection input. Was ${mongoCollection}`);
  }
  const engineName = getEngineName(_engineName);
  if (!engineName) {
    throw new Error(`Need engineName input. Was ${engineName}`);
  }
  return migrateOffersToElastic(
    mongoCollection,
    engineName,
    limit,
    mongoFilter,
  );
};
/**
 *
 * @param {import("@/types").SnsEvent<{provenance: string, collection_name: string}>} event
 */
const handleSnsMigrateEvent = (event) => {
  console.info("event");
  console.info(event);
  const snsMessage = getMessageFromSnsEvent(event);
  const { collection_name: mongoCollection, provenance } = snsMessage;

  if (!mongoCollection) {
    throw new Error(`Need mongoCollection input. Was ${mongoCollection}`);
  }
  if (!provenance) {
    throw new Error(`Need provenance input. Was ${provenance}`);
  }
  const mongoFilter = { provenance };
  const engineName = getEngineName(mongoCollection);
  if (!engineName) {
    throw new Error(`Need engineName input. Was ${engineName}`);
  }
  return migrateOffersToElastic(
    mongoCollection,
    engineName,
    2 ** 20,
    mongoFilter,
  );
};

/**
 *
 * @param {string} mongoCollectionName
 * @param {string} engineName
 * @param {number} limit
 * @param {object} mongoFilter
 * @param {number} chunkSize
 */
const migrateOffersToElastic = async (
  mongoCollectionName,
  engineName,
  limit,
  mongoFilter = {},
  chunkSize = UPLOAD_TO_ELASTIC_OFFERS_CHUNK_SIZE,
) => {
  const mongoCollection = await getCollection(mongoCollectionName);

  const now = new Date();

  /** @var {import("@/types/offers").MpnOffer[]} */
  const offers = await mongoCollection
    .find({ validThrough: { $gte: now }, ...mongoFilter })
    .project(
      includeFields.reduce((acc, current) => ({ ...acc, [current]: true }), {}),
    )
    .limit(limit)
    .toArray();

  console.info(`Found ${offers.length} offers in mongo.`);

  const elasticClient = await getElasticClient();

  const { results: elasticEngines } = await elasticClient.listEngines();
  console.log("Existing elastic engines:");
  console.log(elasticEngines);
  if (!elasticEngines.find(({ name }) => name === engineName)) {
    console.info(`Did not find existing engine ${engineName}. Creating it.`);
    const createEngineResponse = await elasticClient.createEngine(engineName, {
      language: null,
    });
    console.info(createEngineResponse);
  } else {
    console.info(`Found existing engine ${engineName}.`);
  }
  const elasticPromises = _.chain(offers)
    .map(mpnOfferToElasticOffer)
    .chunk(chunkSize)
    .value();

  const elasticResult = [];

  for (const chunk of elasticPromises) {
    const elasticChunkResult = await indexElasticDocuments(
      chunk,
      engineName,
      elasticClient,
    );
    elasticResult.push(...elasticChunkResult);
    console.log(
      `Indexed ${elasticChunkResult.length} objects to elastic in engine ${engineName}.`,
    );
  }

  const errors = _.flatten(elasticResult.map(({ errors }) => errors));
  console.info(`Errors from elastic indexing: ${errors.length}`);
  console.info(`Indexed documents to elastic: ${elasticResult.length}`);

  await mongoCollection.close();
  return {
    result: elasticResult.length,
  };
};
/**
 *
 * @param {string} engineName
 * @param {number} limit
 * @param {number} chunkSize
 */
const deleteOldElasticOffers = async (
  engineName,
  limit,
  chunkSize = UPLOAD_TO_ELASTIC_OFFERS_CHUNK_SIZE,
) => {
  const now = new Date();
  const elasticClient = await getElasticClient();

  const { results: offers } = await elasticClient.search(engineName, "a", {
    page: { size: limit },
    filters: { valid_through: { to: now } },
  });

  console.info(
    `Found ${offers.length} offers to be removed from engine ${engineName}.`,
  );

  const elasticPromises = _.chain(offers)
    .map((offer) => offer.id.raw)
    .chunk(chunkSize)
    .value();

  const elasticResult = [];

  for (const chunk of elasticPromises) {
    const elasticChunkResult = await deleteElasticDocuments(
      chunk,
      engineName,
      elasticClient,
    );
    elasticResult.push(...elasticChunkResult);
    console.log(`Deleted ${elasticChunkResult.length} objects from elastic.`);
  }

  const errors = _.flatten(elasticResult.map(({ errors }) => errors));
  console.info(`Errors from elastic deletion: ${errors.length}`);
  console.info(`Deleted documents from elastic: ${elasticResult.length}`);

  return {
    result: elasticResult.length,
  };
};

const indexElasticDocuments = async (documents, engineName, client) => {
  return client.indexDocuments(engineName, documents);
};
const deleteElasticDocuments = async (documentIds, engineName, client) => {
  return client.destroyDocuments(engineName, documentIds);
};

module.exports = {
  handleSnsMigrateEvent,
  handleTriggerMigrateEvent,
  handleTriggerDeleteEvent,
};
