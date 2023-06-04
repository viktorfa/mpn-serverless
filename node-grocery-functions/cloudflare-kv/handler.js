const _ = require("lodash");

const WorkersKVREST = require("@sagi.io/workers-kv");
const { getCollection } = require("../config/mongo");
const { stage } = require("../config/vars");
const { getMessageFromSnsEvent } = require("../utils");
const { defaultOfferCollection } = require("../utils/constants");

const Sentry = require("@sentry/serverless");

const cfAccountId = process.env.CLOUDFLARE_ACCOUNT_ID;
const cfAuthToken = process.env.CLOUDFLARE_AUTH_TOKEN;
const cloudflareKvNamespaceId = process.env.CLOUDFLARE_KV_NAMESPACE_ID;

Sentry.AWSLambda.init({
  tracesSampleRate: 0.1,
});

const UPLOAD_TO_ELASTIC_OFFERS_CHUNK_SIZE = 1000;

const includeFields = [
  "title",
  "subtitle",
  "shortDescription",
  "description",
  "brand",

  "href",
  "ahref",
  "imageUrl",
  "uri",

  "validFrom",
  "validThrough",
  "mpnStock",

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
  "siteCollection",
];

/**
 *
 * @param {import("@/types").MigrateElasticEvent} event
 */
const handleTriggerMigrateEvent = (event) => {
  console.info("event");
  console.info(event);
  const { mongoCollection, limit = 2 ** 20, mongoFilter = {} } = event;

  if (!mongoCollection) {
    throw new Error(`Need mongoCollection input. Was ${mongoCollection}`);
  }

  return migrateOffersToCloudflare(mongoCollection, limit, mongoFilter);
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

  return migrateOffersToCloudflare(mongoCollection, 2 ** 20, mongoFilter);
};

/**
 *
 * @param {string} siteCollection
 * @param {number} limit
 * @param {object} mongoFilter
 * @param {number} chunkSize
 */
const migrateOffersToCloudflare = async (
  siteCollection,
  limit,
  mongoFilter = {},
  chunkSize = UPLOAD_TO_ELASTIC_OFFERS_CHUNK_SIZE,
) => {
  return;
  const mongoCollection = await getCollection(defaultOfferCollection);

  const now = new Date();

  /** @var {import("@/types/offers").MpnOffer[]} */
  const offers = await mongoCollection
    .find({
      validThrough: { $gte: now },
      siteCollection,
      isRecent: true,
      pageviews: { $gt: 100 }, // Avoid making too many writes to Cloudflare with pageviews filter
      ...mongoFilter,
    })
    .project(
      includeFields.reduce((acc, current) => ({ ...acc, [current]: true }), {}),
    )
    .limit(limit)
    .toArray();

  console.info(`Found ${offers.length} offers in mongo.`);

  const WorkersKV = new WorkersKVREST({ cfAccountId, cfAuthToken });

  const elasticPromises = _.chain(offers).chunk(chunkSize).value();

  const elasticResult = [];

  for (const chunk of elasticPromises) {
    const elasticChunkResult = await updateCloudflareObjects(
      chunk,
      cloudflareKvNamespaceId,
      WorkersKV,
      "uri",
    );
    elasticResult.push(elasticChunkResult);

    if (elasticChunkResult.success) {
      console.log(
        `Stored objects to Cloudflare in kv namespace id ${cloudflareKvNamespaceId}.`,
      );
    } else {
      console.error(`Error when storing offers to Cloudflare`);
      console.error(elasticChunkResult.errors);
    }
  }

  await mongoCollection.close();
  return {
    result: elasticResult,
  };
};
const migrateDealersToCloudflare = async (event) => {
  const mongoCollection = await getCollection("dealers");

  const dealers = await mongoCollection
    .find({})
    .project({
      updated_by: false,
      created_by: false,
      createdAt: false,
      updatedAt: false,
      isPartner: false,
      _id: false,
      __v: false,
    })
    .toArray();

  console.info(`Found ${dealers.length} dealers in mongo.`);

  const WorkersKV = new WorkersKVREST({ cfAccountId, cfAuthToken });

  const elasticPromises = _.chain(dealers)
    .chunk(UPLOAD_TO_ELASTIC_OFFERS_CHUNK_SIZE)
    .value();

  const elasticResult = [];

  for (const chunk of elasticPromises) {
    const elasticChunkResult = await updateCloudflareObjects(
      chunk,
      cloudflareKvNamespaceId,
      WorkersKV,
      "key",
    );
    elasticResult.push(elasticChunkResult);

    if (elasticChunkResult.success) {
      console.log(
        `Stored objects to Cloudflare in kv namespace id ${cloudflareKvNamespaceId}.`,
      );
    } else {
      console.error(`Error when storing dealers to Cloudflare`);
      console.error(elasticChunkResult.errors);
    }
  }

  await mongoCollection.close();
  return {
    result: elasticResult,
  };
};

const updateCloudflareObjects = async (
  documents,
  namespaceId,
  client,
  keyField,
) => {
  const keyValueMap = {};
  documents.forEach((x) => {
    keyValueMap[x[keyField]] = encodeURIComponent(JSON.stringify(x));
  });
  const result = await client.writeMultipleKeys({
    keyValueMap,
    namespaceId,
  });
  return result;
};

module.exports = {
  migrateDealersToCloudflare: Sentry.AWSLambda.wrapHandler(
    migrateDealersToCloudflare,
  ),
  handleSnsMigrateEvent: Sentry.AWSLambda.wrapHandler(handleSnsMigrateEvent),
  handleTriggerMigrateEvent: Sentry.AWSLambda.wrapHandler(
    handleTriggerMigrateEvent,
  ),
};
