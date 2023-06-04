const _ = require("lodash");

const { getElasticClient } = require("../config/elastic");
const { getCollection } = require("../config/mongo");
const { mpnOfferToElasticOffer } = require("./helpers");
const { stage } = require("../config/vars");
const { getMessageFromSnsEvent } = require("../utils");
const { defaultOfferCollection } = require("../utils/constants");

const Sentry = require("@sentry/serverless");

Sentry.AWSLambda.init({
  tracesSampleRate: 0.1,
});

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
  "mpnProperties",
  "mpnCategories",
  "mpnIngredients",
  "mpnNutrition",

  "market",
  "isPartner",
  "siteCollection",
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
  } else if (engineName.startsWith("beauty")) {
    result = "beautyoffers";
  } else if (engineName.startsWith("extra")) {
    result = "extraoffers";
  } else if (engineName.startsWith("sebygg")) {
    result = "sebyggoffers";
  } else if (engineName.startsWith("segrocery")) {
    result = "segroceryoffers";
  } else if (engineName.startsWith("sebeauty")) {
    result = "sebeautyoffers";
  } else if (engineName.startsWith("seextra")) {
    result = "seextraoffers";
  } else if (engineName.startsWith("degrocery")) {
    result = "degroceryoffers";
  } else if (engineName.startsWith("debygg")) {
    result = "debyggoffers";
  } else if (engineName.startsWith("debeauty")) {
    result = "debeautyoffers";
  } else if (engineName.startsWith("deextra")) {
    result = "deextraoffers";
  } else if (engineName.startsWith("ukgrocery")) {
    result = "ukgroceryoffers";
  } else if (engineName.startsWith("ukbygg")) {
    result = "ukbyggoffers";
  } else if (engineName.startsWith("ukbeauty")) {
    result = "ukbeautyoffers";
  } else if (engineName.startsWith("ukextra")) {
    result = "ukextraoffers";
  } else if (engineName.startsWith("dkgrocery")) {
    result = "dkgroceryoffers";
  } else if (engineName.startsWith("dkbygg")) {
    result = "dkbyggoffers";
  } else if (engineName.startsWith("dkbeauty")) {
    result = "dkbeautyoffers";
  } else if (engineName.startsWith("dkextra")) {
    result = "dkextraoffers";
  } else if (engineName.startsWith("usgrocery")) {
    result = "usgroceryoffers";
  } else if (engineName.startsWith("usbygg")) {
    result = "usbyggoffers";
  } else if (engineName.startsWith("usbeauty")) {
    result = "usbeautyoffers";
  } else if (engineName.startsWith("usextra")) {
    result = "usextraoffers";
  } else if (engineName.startsWith("figrocery")) {
    result = "figroceryoffers";
  } else if (engineName.startsWith("fibygg")) {
    result = "fibyggoffers";
  } else if (engineName.startsWith("fibeauty")) {
    result = "fibeautyoffers";
  } else if (engineName.startsWith("fiextra")) {
    result = "fiextraoffers";
  } else if (engineName.startsWith("sggrocery")) {
    result = "sggroceryoffers";
  } else if (engineName.startsWith("sgbygg")) {
    result = "sgbyggoffers";
  } else if (engineName.startsWith("sgbeauty")) {
    result = "sgbeautyoffers";
  } else if (engineName.startsWith("sgextra")) {
    result = "sgextraoffers";
  } else if (engineName.startsWith("thgrocery")) {
    result = "thgroceryoffers";
  } else if (engineName.startsWith("thbygg")) {
    result = "thbyggoffers";
  } else if (engineName.startsWith("thbeauty")) {
    result = "thbeautyoffers";
  } else if (engineName.startsWith("thextra")) {
    result = "thextraoffers";
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
  console.info("snsMessage");
  console.info(snsMessage);
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
 * @param {string} siteCollection
 * @param {string} engineName
 * @param {number} limit
 * @param {object} mongoFilter
 * @param {number} chunkSize
 */
const migrateOffersToElastic = async (
  siteCollection,
  engineName,
  limit,
  mongoFilter = {},
  chunkSize = UPLOAD_TO_ELASTIC_OFFERS_CHUNK_SIZE,
) => {
  const mongoCollection = await getCollection(defaultOfferCollection);

  const now = new Date();

  /** @var {import("@/types/offers").MpnOffer[]} */
  const offers = await mongoCollection
    .find({ validThrough: { $gte: now }, siteCollection, ...mongoFilter })
    .project(
      includeFields.reduce((acc, current) => ({ ...acc, [current]: true }), {}),
    )
    .limit(limit)
    .toArray();

  console.info(`Found ${offers.length} offers in mongo.`);

  const elasticClient = await getElasticClient();

  const engines = [];
  let page = 1;
  let response;
  while (true) {
    response = await elasticClient.listEngines({ page: { current: page } });
    console.log(`Elastic engines response for page ${page}:`);
    console.log(response);
    engines.push(...response.results);
    page++;
    if (engines.length >= response.meta.page.total_results || page === 20) {
      break;
    }
  }

  console.log("Existing elastic engines:");
  console.log(engines);
  if (!engines.find(({ name }) => name === engineName)) {
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

const getRandomLetter = (letterSet = "abcdefghijklmnopqrstuvwxyz") => {
  return letterSet[Math.floor(Math.random() * letterSet.length)];
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

  console.info(`Deleting up to ${limit} old offers from ${engineName}`);

  const { results: offers } = await elasticClient.search(
    engineName,
    getRandomLetter(),
    {
      page: { size: limit },
      filters: { valid_through: { to: now } },
    },
  );

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
  handleSnsMigrateEvent: Sentry.AWSLambda.wrapHandler(handleSnsMigrateEvent),
  handleTriggerMigrateEvent: Sentry.AWSLambda.wrapHandler(
    handleTriggerMigrateEvent,
  ),
  handleTriggerDeleteEvent: Sentry.AWSLambda.wrapHandler(
    handleTriggerDeleteEvent,
  ),
};
