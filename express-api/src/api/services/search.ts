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
