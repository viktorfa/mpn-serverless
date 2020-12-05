import { elasticOfferToMpnOffer } from "@/api/models/mpnOffer.model";
import { getElasticClient } from "@/config/elastic";
import { getNowDate } from "../utils/helpers";
import APIError from "../utils/APIError";
import { getOffersByUris } from "./offers";

export const search = async (
  query: string,
  engineName: string,
  limit = 32,
): Promise<MpnResultOffer[]> => {
  const elasticClient = await getElasticClient();
  console.log(`Searching for ${query} on engine ${engineName}.`);
  const now = getNowDate();
  const searchResponse = await elasticClient.search<ElasticMpnOfferRaw>(
    engineName,
    query,
    { page: { size: limit }, filters: { valid_through: { from: now } } },
  );

  try {
    const mpnResults = searchResponse.results.map((x) => {
      return elasticOfferToMpnOffer(x);
    });

    // Filter offers that only exist in Elastic and not in Mongo
    const resultUris = mpnResults.map((x) => x.uri);
    const urisFromMongoSet = new Set(
      (await getOffersByUris(resultUris, { uri: 1 })).map((x) => x.uri),
    );

    const validOffers = mpnResults.filter((x) => urisFromMongoSet.has(x.uri));

    return validOffers;
  } catch (e) {
    console.error(e);
    throw new APIError({
      status: 500,
      message: `Could not search for ${query}`,
    });
  }
};

export const querySuggestion = async (query, engineName): Promise<string[]> => {
  const elasticClient = await getElasticClient();
  console.log(`Getting querySuggestion for ${query} on engine ${engineName}.`);
  const searchResponse = await elasticClient.querySuggestion(engineName, query);

  return searchResponse.results.documents.map(({ suggestion }) => suggestion);
};

export const registerClick = async (
  registerClickArgs,
  engineName,
): Promise<void> => {
  const elasticClient = await getElasticClient();
  console.log(
    `Registering click for for ${registerClickArgs.query} on engine ${engineName}.`,
  );
  const searchResponse = await elasticClient.client.post(
    `engines/${encodeURIComponent(engineName)}/click`,
    registerClickArgs,
  );
  return;
};
