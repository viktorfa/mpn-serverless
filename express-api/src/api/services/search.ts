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
  if (query.length > 127) {
    const message = `Query ${query} is too long (${query.length} characters). Max is 128.`;
    console.error(message);
    throw new APIError({
      status: 500,
      message,
    });
  }
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
      (await getOffersByUris(resultUris, null, { uri: 1 })).map((x) => x.uri),
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
export const searchWithFilter = async ({
  query,
  engineName,
  limit = 32,
  page = 1,
  dealers,
  categories,
  price,
  sort,
  boosts,
  precision = 4,
}: {
  query: string;
  engineName: string;
  limit?: number;
  page?: number;
  dealers?: string[];
  categories?: string[];
  price?: { from?: number; to?: number };
  sort?: { [key: string]: "desc" | "asc" };
  boosts?: AppSearchOfferBoosts;
  precision?: number;
}): Promise<{ items: MpnResultOffer[]; facets: any; meta: any }> => {
  const elasticClient = await getElasticClient();
  if (query.length > 127) {
    const message = `Query ${query} is too long (${query.length} characters). Max is 128.`;
    console.error(message);
    throw new APIError({
      status: 500,
      message,
    });
  }
  const now = getNowDate();
  const filters: { all: Record<string, any>[] } = {
    all: [{ valid_through: { from: now } }],
  };

  if (dealers) {
    filters.all.push({ dealer: dealers });
  }
  if (categories) {
    filters.all.push({ mpn_categories: categories });
  }

  if (price) {
    filters.all.push({ price });
  }

  const facets: { dealer: any; brand: any; mpn_categories?: any } = {
    dealer: [
      {
        type: "value",
      },
    ],
    brand: [
      {
        type: "value",
      },
    ],
  };
  if (engineName.startsWith("groceryoffers")) {
    facets.mpn_categories = [
      {
        type: "value",
      },
    ];
  }
  const searchOptions: AppSearchParams = {
    page: { size: limit, current: page },
    precision,
    filters,
    facets,
  };

  if (sort) {
    searchOptions.sort = sort;
  }
  if (boosts) {
    searchOptions.boosts = boosts;
  }

  const searchResponse = await elasticClient.search<ElasticMpnOfferRaw>(
    engineName,
    query,
    searchOptions,
  );

  try {
    const mpnResults = searchResponse.results.map((x) => {
      return elasticOfferToMpnOffer(x);
    });

    // Filter offers that only exist in Elastic and not in Mongo
    const resultUris = mpnResults.map((x) => x.uri);
    const urisFromMongoSet = new Set(
      (await getOffersByUris(resultUris, null, { uri: 1 })).map((x) => x.uri),
    );

    const validOffers = mpnResults.filter((x) => urisFromMongoSet.has(x.uri));

    return {
      facets: searchResponse.facets,
      meta: searchResponse.meta,
      items: validOffers,
    };
  } catch (e) {
    console.error(e);
    throw new APIError({
      status: 500,
      message: `Could not search for ${query}`,
    });
  }
};

export const querySuggestion = async (query, engineName): Promise<string[]> => {
  if (query.length > 127) {
    const message = `Query ${query} is too long (${query.length} characters). Max is 128.`;
    console.error(message);
    throw new APIError({
      status: 500,
      message,
    });
  }
  const elasticClient = await getElasticClient();
  const searchResponse = await elasticClient.querySuggestion(engineName, query);

  return searchResponse.results.documents.map(({ suggestion }) => suggestion);
};

export const registerClick = async (
  registerClickArgs,
  engineName,
): Promise<void> => {
  const elasticClient = await getElasticClient();
  const searchResponse = await elasticClient.client.post(
    `engines/${encodeURIComponent(engineName)}/click`,
    registerClickArgs,
  );
  return;
};
