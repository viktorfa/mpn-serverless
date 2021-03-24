const { processProducts } = require("./process-products");

const { stage } = require("../config/vars");
const { getMessageFromSnsEvent } = require("../utils");

const Sentry = require("@sentry/serverless");

Sentry.AWSLambda.init({
  tracesSampleRate: 1.0,
});

/**
 *
 * @param {import("@/types").HandleOffersEvent} event
 */
const processGroceryOffers = async (event) => {
  try {
    const { mongoCollection, storeInS3 = true, limit = 2 ** 20 } = event;
    if (!mongoCollection || typeof mongoCollection !== "string") {
      throw new Error(
        `mongoCollection argument has to be a string. Was ${mongoCollection}`,
      );
    }
    const result = await processProducts(
      mongoCollection,
      `${stage}-${mongoCollection}`,
      storeInS3,
      limit,
    );
    return {
      message: "Go Serverless v1.0! Your function executed successfully!",
      event,
      result,
    };
  } catch (e) {
    console.error(e);
    return {
      message: "Go Serverless v1.0! Something wrong happened..",
      event,
    };
  }
};

/**
 *
 * @param {import("@/types").SnsEvent<{collection_name:string}>} event
 */
const processGroceryOffersSns = async (event) => {
  try {
    console.log("event");
    console.log(event);
    const snsMessage = getMessageFromSnsEvent(event);
    const { collection_name: siteCollection } = snsMessage;
    if (!siteCollection || typeof siteCollection !== "string") {
      throw new Error(
        `siteCollection argument has to be a string. Was ${siteCollection}`,
      );
    }
    const result = await processProducts(
      siteCollection,
      `${stage}-${siteCollection}`,
    );
    return {
      message: "Go Serverless v1.0! Your function executed successfully!",
      event,
      result,
    };
  } catch (e) {
    console.error(e);
    return {
      message: "Go Serverless v1.0! Something wrong happened..",
      event,
    };
  }
};

module.exports = {
  processGroceryOffers: Sentry.AWSLambda.wrapHandler(processGroceryOffers),
  processGroceryOffersSns: Sentry.AWSLambda.wrapHandler(
    processGroceryOffersSns,
  ),
};
