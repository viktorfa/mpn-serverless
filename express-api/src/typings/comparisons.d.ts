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

type ComparisonConfig = OfferConfig[];
type ComparisonInstance = OfferInstance[];
