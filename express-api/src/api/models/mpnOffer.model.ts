import get from "lodash/get";

const defaultOfferFields = [
  "title",
  "description",
  "shortDescription",
  "subtitle",
  "pricing",
  "dealer",
  "brand",
  "uri",
  "href",
  "imageUrl",
  "value",
  "provenance",
  "categories",
  "quantity",
  "gtins",
  "mpnStock",
];

export const defaultOfferProjection = defaultOfferFields.reduce(
  (acc, current) => ({ ...acc, [current]: true }),
  {},
);

export const getJsonFromRaw = <T = Record<string, any> | Array<any>>(
  field:
    | undefined
    | {
        raw?: any;
      },
): T => {
  return JSON.parse(get(field, ["raw"], "{}")) || {};
};

export const elasticOfferToMpnOffer = (
  elasticOffer: ElasticMpnOfferRaw,
): MpnResultOffer => {
  return {
    title: elasticOffer.title.raw,
    subtitle: elasticOffer.subtitle?.raw,
    shortDescription: elasticOffer.short_description?.raw,
    description: elasticOffer.description?.raw,
    brand: elasticOffer.brand?.raw,

    href: elasticOffer.href.raw,
    imageUrl: elasticOffer.image_url.raw,
    uri: elasticOffer.id.raw,

    validFrom: new Date(elasticOffer.valid_from.raw),
    validThrough: new Date(elasticOffer.valid_through.raw),

    pricing: getJsonFromRaw<Pricing>(elasticOffer.pricing),
    quantity: getJsonFromRaw<QuantityField>(elasticOffer.quantity),
    value: getJsonFromRaw<QuantityField>(elasticOffer.value),

    categories: elasticOffer.categories?.raw,
    dealer: elasticOffer.dealer?.raw,
    provenance: elasticOffer.provenance.raw,
    gtins: getJsonFromRaw<Record<string, string>>(elasticOffer.gtins),
    mpnStock: elasticOffer.mpn_stock?.raw,

    score: elasticOffer._meta.score,
  };
};
