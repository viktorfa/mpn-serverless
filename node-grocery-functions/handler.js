const { processProducts } = require("./process-products");

const { stage } = require("./config/vars");

module.exports.processGroceryOffers = async (event, context) => {
  try {
    const { mongoCollection } = event;
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
