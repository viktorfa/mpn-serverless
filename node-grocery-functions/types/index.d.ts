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

export interface SnsRecord<Message> {
  Sns: { Message: Message };
}

export interface SnsEvent<Message> {
  Records: { 0: SnsRecord<Message> };
}

export interface CollectionWithClose extends Collection {
  close(): Promise<void>;
}
