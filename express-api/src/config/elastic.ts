import AppSearchClient from "@elastic/app-search-node";

import { elasticUrl, elasticApiKey } from "@/config/vars";

const baseUrlFn = () => elasticUrl;

let client = null;

export const getElasticClient = async () => {
  if (!client) {
    client = new AppSearchClient(undefined, elasticApiKey, baseUrlFn);
  }
  return client;
};
