const AppSearchClient = require("@elastic/app-search-node");

const { elasticUrl, elasticApiKey } = require("./vars");

const baseUrlFn = () => elasticUrl;

let client = null;

/**
 * @returns {AppSearchClient}
 */
const getElasticClient = async () => {
  if (!client) {
    client = new AppSearchClient(undefined, elasticApiKey, baseUrlFn);
  }
  return client;
};

module.exports = {
  getElasticClient,
};
