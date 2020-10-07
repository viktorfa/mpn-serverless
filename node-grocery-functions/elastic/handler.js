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
 * @param {import("@/types").MigrateElasticEvent} event
 */
const handleTriggerMigrateEvent = (event) => {
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
    console.log(`Indexed ${elasticChunkResult.length} objects to elastic.`);
  }

  const errors = _.flatten(elasticResult.map(({ errors }) => errors));
  console.info(`Errors from elastic indexing: ${errors.length}`);
  console.info(`Indexed documents to elastic: ${elasticResult.length}`);

  await mongoCollection.close();
  return {
    result: elasticResult.length,
  };
};

const indexElasticDocuments = async (documents, engineName, client) => {
  return client.indexDocuments(engineName, documents);
};

module.exports = { handleSnsMigrateEvent, handleTriggerMigrateEvent };
