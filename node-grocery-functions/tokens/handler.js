const { processProducts } = require("./process-products");

const { stage } = require("../config/vars");
const { getMessageFromSnsEvent } = require("../utils");

/**
 *
 * @param {import("@/types").HandleOffersEvent} event
 */
module.exports.processGroceryOffers = async (event) => {
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
module.exports.processGroceryOffersSns = async (event) => {
  try {
    console.log("event");
    console.log(event);
    const snsMessage = getMessageFromSnsEvent(event);
    const { collection_name: mongoCollection } = snsMessage;
    if (!mongoCollection || typeof mongoCollection !== "string") {
      throw new Error(
        `mongoCollection argument has to be a string. Was ${mongoCollection}`,
      );
    }
    const result = await processProducts(
      mongoCollection,
      `${stage}-${mongoCollection}`,
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
