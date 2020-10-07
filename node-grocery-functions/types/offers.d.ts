export interface Pricing {
  price: number;
  prePrice?: number;
  currency: string;
}

export interface QuantityAmount {
  min: number;
  max: number;
}

export interface SiConfig {
  factor: number;
  symbol: string;
}

export interface MpnUnit {
  symbol: string;
  type: string;
}

export interface QuantityUnit extends MpnUnit {
  si: SiConfig;
}

export interface Quantity {
  unit: QuantityUnit;
  amount: QuantityAmount;
  standard: QuantityAmount;
}

export interface QuantityField {
  size: Quantity;
  pieces: Quantity;
}

export interface ItemsField {
  amount: QuantityAmount;
}

export interface MpnOffer {
  title: string;
  subtitle: string;
  shortDescription: string;
  description: string;
  brand: string;

  href: string;
  imageUrl: string;
  uri: string;

  validFrom: string;
  validThrough: string;

  pricing: Pricing;
  quantity: QuantityField;
  value: QuantityField;

  categories: string[];
  dealer: string;
  provenance: string;
  gtins?: Record<string, string>;
  mpnStock: string;
}

export interface ElasticMpnOffer {
  title: string;
  subtitle: string;
  short_description: string;
  description: string;
  brand: string;

  image_url: string;
  href: string;
  id: string;

  valid_from: string;
  valid_through: string;

  price: number;
  pre_price?: number;
  price_currency: string;
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
