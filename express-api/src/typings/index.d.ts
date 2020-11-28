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
  brand: string;

  href: string;
  imageUrl: string;
  uri: string;

  validFrom: Date;
  validThrough: Date;

  pricing: Pricing;
  quantity: QuantityField;
  value: QuantityField;

  categories: string[];
  dealer: string;
  provenance: string;
  gtins?: Record<string, string>;
  mpnStock: string;
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
}

interface ElasticMpnOffer {
  title: string;
  subtitle: string;
  short_description: string;
  description: string;
  brand: string;

  image_url: string;
  href: string;
  id: string;

  valid_from: Date;
  valid_through: Date;

  price: number;
  pre_price?: number;
  price_currency: string;
  price_text?: string;
  standard_value?: number;
  standard_value_unit?: string;
  standard_size?: number;
  standard_size_unit?: string;

  categories: string[];
  dealer: string;
  provenance: string;
  gtins: Record<string, string>;
  mpn_stock: string;
}

interface RawField<
  T extends string[] | Record<string, string> | string = string
> {
  raw: T;
}

interface ElasticMpnOfferRaw {
  title: RawField;
  subtitle: RawField;
  short_description: RawField;
  description: RawField;
  brand: RawField;

  image_url: RawField;
  href: RawField;
  id: RawField;

  valid_from: RawField;
  valid_through: RawField;

  price: RawField;
  pre_price?: RawField;
  price_currency: RawField;
  standard_value: RawField;
  standard_value_unit: RawField;
  standard_size: RawField;
  standard_size_unit: RawField;

  categories: RawField<string[]>;
  dealer: RawField;
  provenance: RawField;
  gtins?: RawField<Record<string, string>>;
  mpn_stock: RawField;

  quantity: RawField;
  value: RawField;
  pricing: RawField;

  _meta: { score: number; id: string; engine: string };
}

declare type RatingScoreType = 1 | 2 | 3 | 4 | 5;
declare type OfferRelationType =
  | "identical"
  | "interchangeable"
  | "similar"
  | "related"
  | "lowerend"
  | "higherend"
  | "usedtogether";

interface IdenticalOfferRelation {
  offerSet: string[];
  relationType: OfferRelationType;
}

interface OfferReview {
  body: string;
  author: string;
  uri: string;
  rating: RatingScoreType;
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
}

type ListResponse<T> = {
  items: T[];
};
