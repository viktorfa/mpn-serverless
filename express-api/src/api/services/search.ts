import { getElasticClient } from "@/config/elastic";

const DEFAULT_ENGINE_NAME = "groceryoffers";

export const search = async (
  query: string,
  engineName: string = DEFAULT_ENGINE_NAME,
): Promise<MpnOffer[]> => {
  const elasticClient = await getElasticClient();
  console.log(`Searching for ${query} on engine ${engineName}.`);
  const searchResponse = await elasticClient.search<MpnOffer>(
    engineName,
    query,
  );
  console.log("searchResponse");
  console.log(searchResponse.meta);

  return searchResponse.results;
};

export const querySuggestion = async (
  query,
  engineName = DEFAULT_ENGINE_NAME,
): Promise<string[]> => {
  const elasticClient = await getElasticClient();
  console.log(`Getting querySuggestion for ${query} on engine ${engineName}.`);
  const searchResponse = await elasticClient.querySuggestion(engineName, query);
  console.log("querySuggestionResponse");
  console.log(searchResponse.meta);
  console.log(searchResponse.results.documents);

  return searchResponse.results.documents.map(({ suggestion }) => suggestion);
};

export const registerClick = async (
  registerClickArgs,
  engineName = DEFAULT_ENGINE_NAME,
): Promise<void> => {
  const elasticClient = await getElasticClient();
  console.log(
    `Registering click for for ${registerClickArgs.query} on engine ${engineName}.`,
  );
  const searchResponse = await elasticClient.client.post(
    `engines/${encodeURIComponent(engineName)}/click`,
    registerClickArgs,
  );
  console.log("searchResponse for register click");
  console.log(searchResponse);
  return;
};
