const { processProducts } = require("./process-products");

module.exports.processGroceryOffers = async (event, context) => {
  const result = await processProducts();
  return {
    message: "Go Serverless v1.0! Your function executed successfully!",
    event,
    result,
  };
};
