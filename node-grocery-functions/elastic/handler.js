const { getElasticClient } = require("../config/elastic");
const { getCollection } = require("../config/mongo");
const snakeCase = require("lodash/snakeCase");
const _ = require("lodash");

const defaultEngineName = "byggoffers";

const search = async (event) => {
  const { query, engineName = defaultEngineName } = event;
  console.log(`Searching for ${query}`);

  const client = await getElasticClient();
  const result = await client.search(engineName, query);

  console.log(`Results`);
  return { result };
};

const includeFields = [
  "title",
  "subtitle",
  "shortDescription",
  "description",
  "validFrom",
  "validThrough",
  "categories",
  "brand",
  "dealer",
  "provenance",
  "pricing",
  "quantity",
  "value",
  "gtins",
  "href",
  "imageUrl",
];
const mongoOfferToElasticOffer = (offer) => {
  const result = {};
  includeFields.forEach((key) => {
    result[snakeCase(key)] = offer[key];
  });
  result["id"] = offer.uri;
  return result;
};

/**
 *
 * @param {import("@/types").MigrateElasticEvent} event
 */
const migrateOffersToElastic = async (event) => {
  const ELASTIC_INDEX_CHUNK_SIZE = 32;
  const { mongoCollection, engineName, limit = 2 ** 20 } = event;

  if (!mongoCollection) {
    throw new Error(`Need mongoCollection input. Was ${mongoCollection}`);
  }
  if (!engineName) {
    throw new Error(`Need engineName input. Was ${engineName}`);
  }

  const _mongoCollection = await getCollection(mongoCollection);

  const now = new Date();

  const offers = await _mongoCollection
    .find({ validThrough: { $gte: now } })
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
    .map(mongoOfferToElasticOffer)
    .chunk(ELASTIC_INDEX_CHUNK_SIZE)
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

  await _mongoCollection.close();
  return {
    result: elasticResult.length,
  };
};

const indexElasticDocuments = async (documents, engineName, client) => {
  return client.indexDocuments(engineName, documents);
};

module.exports = { search, migrateOffersToElastic };
