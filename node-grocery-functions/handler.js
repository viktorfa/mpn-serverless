const { processProducts } = require("./process-products");

const { stage } = require("./config/vars");

module.exports.processGroceryOffers = async (event) => {
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
      true,
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

module.exports.processGroceryOffersSns = async (event) => {
  try {
    console.log("event");
    console.log(event);
    console.log("event.Records[0].Sns");
    console.log(event.Records[0].Sns);
    const snsMessage = JSON.parse(event.Records[0].Sns.Message);
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
