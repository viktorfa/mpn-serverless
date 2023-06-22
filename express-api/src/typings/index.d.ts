interface Pricing {
  price: number;
  prePrice?: number;
  currency: string;
  text?: string;
}

interface QuantityAmount {
  min: number;
  max: number;
}

interface SiConfig {
  factor: number;
  symbol: string;
}

interface MpnUnit {
  symbol: string;
  type: string;
}

interface QuantityUnit extends MpnUnit {
  si: SiConfig;
}

interface Quantity {
  unit: QuantityUnit;
  amount: QuantityAmount;
  standard: QuantityAmount;
}

interface QuantityField {
  size: Quantity;
  pieces: Quantity;
}

interface ItemsField {
  amount: QuantityAmount;
}

interface MpnOffer {
  title: string;
  subtitle: string;
  shortDescription: string;
  description: string;
  brand?: string;
  brandKey?: string;

  href: string;
  ahref?: string;
  imageUrl: string;
  uri: string;

  validFrom: Date;
  validThrough: Date;

  pricing: Pricing;
  quantity: QuantityField;
  value: QuantityField;

  categories: string[];
  dealer: string;
  dealerKey: string;
  provenance: string;
  gtins?: Record<string, string>;
  mpnStock: string;
  market: string;

  mpnCategories: MpnCategory[];
}
interface CustomOffer {
  title: string;

  imageUrl: string;
  uri: string;

  validFrom: Date;
  validThrough: Date;

  pricing: Pricing;

  market: string;
}
interface MpnMongoOffer extends MpnOffer {
  readonly _id: { toString(): string };
}
interface MpnResultOffer extends MpnOffer {
  readonly _id?: { toString(): string };
  readonly score?: number;
}
interface FullMpnOffer extends MpnMongoOffer {
  similarOffers: { uri: string; score: number }[];
  siteCollection: string;
}

type MpnOfferRelation = {
  readonly _id: { toString(): string };
  offers: MpnMongoOffer[];
  title: string;
  subtitle?: string;
  shortDescription?: string;
  description?: string;
  imageUrl: string;
  dealerKey: string;
  mpnNutrition: any;
};
type MpnOfferRelationResult = MpnOfferRelation & {
  readonly score: number;
};

declare type RatingScoreType = 1 | 2 | 3 | 4 | 5;
declare type OfferRelationType =
  | "identical"
  | "interchangeable"
  | "identicaldifferentquantity"
  | "exchangeabledifferentquantity"
  | "similar"
  | "related"
  | "lowerend"
  | "higherend"
  | "usedtogether";

interface IdenticalOfferRelation {
  _id: string;
  offerSet: string[];
  relationType: OfferRelationType;
  title: string;
}

type OfferReviewStatus = "enabled" | "removed" | "pending";

interface OfferReview {
  body: string;
  author: string;
  uri: string;
  rating: RatingScoreType;
  status?: OfferReviewStatus;
}
interface MongoOfferReview extends OfferReview {
  _id: string;
}

interface OfferTag {
  uri: string;
  tag: string;
  validThrough?: Date;
  selectionType: "manual" | "ml" | "automatic";
}

interface SimilarOffersObject {
  offers: MpnOffer[];
  title: string;
  relationType?: string;
  _id?: string;
}
interface SingleSimilarOffersObject extends SimilarOffersObject {
  relationType: string;
  imageUrl: string;
  description: string;
  subtitle: string;
  shortDescription: string;
}

interface MpnCategory {
  text: string;
  key: string;
  level: number;
  parent: string;
}

interface MpnCategoryInTree {
  text: string;
  key: string;
  level: number;
  parentObject: null | MpnCategory;
  children: MpnCategory[];
}

type ListResponse<T> = {
  items: T[];
};

type UpdateOfferRelationBody = {
  title: string;
  id: string;
};

type UriOfferGroup = {
  uris: string[];
  title?: string;
  _id?: string;
  relationType?: string;
};

interface PricingHistoryObject {
  price?: number;
  pricing: Pricing;
  date: string;
  uri: string;
}

interface MpnMongoSearchResponse {
  meta: MpnMongoSearchResponseMeta;
  items: MpnResultOffer[];
  facets: MpnMongoSearchResponseFacets;
}
interface MpnMongoRelationsSearchResponse {
  meta: MpnMongoSearchResponseMeta;
  items: MpnOfferRelationResult[];
  facets: MpnMongoSearchResponseFacets;
}
interface MpnMongoSearchResponseMeta {
  count: number;
  page: number;
  pageSize: number;
  pageCount: number;
}
interface MpnMongoSearchResponseFacets {
  [key: string]: { buckets: any[] };
}

interface PromotionBanner {
  url: string;
  image: string;
  type: "horizontal" | "square" | "offer";
  text?: string;
}

interface AdTractionCampaign {
  logoURL: string;
  market: string;
  offerDescription: string;
  offerPage: string;
  programUrl: string;
  trackingURL: string;
  programId: number;
}

interface MpnDealer {
  logoUrl: string;
  market: string;
  productCollection: string;
  url: string;
  type: "horizontal" | "square";
}

interface OfferPricingHistory {
  uri: string;
  updatedAt: Date;
  siteCollection: string;
  hisotry: PricingHistoryObject[];
}

type PartnerProduct = {
  title: string;
  description: string;
  price: number;
  stockAmount: number;
};
type PartnerProductMongo = PartnerProduct & {
  _id: string;
  status: string;
};
type MpnMongoOfferPartner = MpnMongoOffer & {
  stockAmount: number;
};
type StorePartner = {
  _id: string;
  name: string;
  description: string;
  location?: Object;
  cognitoId: string;
  email: string;
  phoneNumber: string;
};
