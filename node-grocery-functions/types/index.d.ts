import { Collection } from "mongodb";

export interface MigrateElasticEvent {
  mongoCollection: string;
  engineName: string;
  limit?: number;
  mongoFilter?: Record<string, string | number | object>;
}
export interface HandleOffersEvent {
  mongoCollection: string;
  storeInS3?: boolean;
  limit?: number;
}
export interface DeleteElasticEvent {
  engineName: string;
  limit?: number;
}

export interface SnsRecord<Message> {
  Sns: { Message: Message };
}

export interface SnsEvent<Message> {
  Records: { 0: SnsRecord<Message> };
}

export interface CollectionWithClose extends Collection {
  close(): Promise<void>;
}

export type OfferFeedHandledMessage = {
  provenance: string;
  namespace: string;
  collection_name: string;
  market: string;
  is_partner: string;
  feed_key: string;
  scrape_time: string;
  scrapeBatchId: string;
};
