import AppSearchClient from "@elastic/app-search-node";

import { elasticUrl, elasticApiKey } from "@/config/vars";

const baseUrlFn = () => elasticUrl;

let client: AppSearchClient | null = null;

interface IAppSearchClient {
  search<T>(
    engineName: string,
    query: string,
    options?: object,
  ): ElasticResponse<T>;
}

interface ElasticResponse<T> {
  meta: {
    alerts: [];
    warnings: [];
    page: {
      current: number;
      total_pages: number;
      total_results: number;
      size: number;
    };
    engine: { name: string; type: string };
    request_id: string;
  };
  results: T[];
}

export const getElasticClient = async (): Promise<IAppSearchClient> => {
  if (!client) {
    console.log(`Connecting Elastic search at ${baseUrlFn()}`);
    client = new AppSearchClient(undefined, elasticApiKey, baseUrlFn);
  } else {
    console.log(`Using cached Elastic connection`);
  }
  return client;
};
