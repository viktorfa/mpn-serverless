import { getElasticClient } from "@/config/elastic";
import { mpnOfferToElasticOffer } from "../models/mpnOffer.model";

export const indexDocuments = async (
  documents: FullMpnOffer[],
  engineName: string,
): Promise<any> => {
  const elasticClient = await getElasticClient();
  const elasticDocuments = documents.map(mpnOfferToElasticOffer);
  console.log(`Indexing documents to ${engineName}`);
  console.log(elasticDocuments);
  return elasticClient.indexDocuments(engineName, elasticDocuments);
};
