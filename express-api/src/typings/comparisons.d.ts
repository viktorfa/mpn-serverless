interface DealerConfig {
  uri: string;
  quantityValue?: number;
}
interface DealerInstance extends DealerConfig {
  product: MpnOffer;
}

interface OfferConfigBase {
  title: string;
  name: string;
  category: string;
  productCollection: string;
  quantityValue?: number;
  quantityUnit?: string;
  useUnitPrice: boolean;
}
interface OfferConfig extends OfferConfigBase {
  dealers: { [dealer: string]: DealerConfig };
}
interface PutOfferConfig extends OfferConfigBase {}

interface OfferInstance {
  dealers: { [dealer: string]: DealerInstance };
}

interface ComparisonConfig extends OfferConfigBase {
  dealers: { [dealer: string]: DealerConfig };
}
interface ComparisonInstance {
  dealers: { [dealer: string]: DealerInstance };
  category: string;
  name: string;
  productCollection: string;
  quantityUnit?: string;
  quantityValue?: number;
  title: string;
  useUnitPrice: boolean;
}
