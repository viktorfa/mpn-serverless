import AppSearchClient from "@elastic/app-search-node";

import { elasticUrl, elasticApiKey } from "@/config/vars";

import { SearchParams, SuggestParams } from "elasticsearch";

const baseUrlFn = () => elasticUrl;

let client: AppSearchClient | null = null;

interface IElasticClient {
  post(path: string, params: object);
}

interface IAppSearchClient {
  search<T>(
    engineName: string,
    query: string,
    options?: SearchParams,
  ): ElasticResponse<T>;
  querySuggestion(
    engineName: string,
    query: string,
    options?: SuggestParams,
  ): ElasticQuerySuggestionResponse;
  client: IElasticClient;
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
interface ElasticQuerySuggestionResponse {
  meta: {
    request_id: string;
  };
  results: { documents: { ["suggestion"]: string }[] };
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
