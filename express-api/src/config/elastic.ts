import AppSearchClient from "@elastic/app-search-node";

import { elasticUrl, elasticApiKey } from "@/config/vars";

const baseUrlFn = () => elasticUrl;

let client: AppSearchClient | null = null;

export const getElasticClient = async (): Promise<IAppSearchClient> => {
  if (!client) {
    console.log(`Connecting Elastic search at ${baseUrlFn()}`);
    client = new AppSearchClient(undefined, elasticApiKey, baseUrlFn);
  } else {
    console.log(`Using cached Elastic connection`);
  }
  return client;
};
