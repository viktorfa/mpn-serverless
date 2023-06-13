import { last, get } from "lodash";
export const defaultDealerProjection = { key: 1, text: 1, logoUrl: 1, url: 1 };
const requriedElasticOfferFields = [
  "title",
  "valid_from",
  "valid_through",
  "provenance",
  "id",
  "pricing",
];
const defaultOfferFields = [
  "title",
  "description",
  "shortDescription",
  "subtitle",
  "pricing",
  "dealer",
  "dealerKey",
  "brand",
  "brandKey",
  "vendor",
  "vendorKey",
  "uri",
  "href",
  "ahref",
  "imageUrl",
  "value",
  "provenance",
  "categories",
  "quantity",
  "gtins",
  "mpnStock",
  "validFrom",
  "validThrough",
  "mpnProperties",
  "mpnNutrition",
  "mpnIngredients",
  "mpnCategories",
  "market",
];

export const defaultOfferProjection = defaultOfferFields.reduce(
  (acc, current) => ({ ...acc, [current]: true }),
  { dealerObject: defaultDealerProjection },
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
    uri: last(elasticOffer.id.raw.split("|")),

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
    market: elasticOffer.market?.raw,

    score: elasticOffer._meta.score,
  };
};

export const mpnOfferToElasticOffer = (
  offer: FullMpnOffer,
): ElasticMpnOffer => {
  const result = {
    title: offer.title,
    subtitle: offer.subtitle || "",
    short_description: offer.shortDescription || "",
    description: offer.description || "",
    brand: offer.brand || "",

    image_url: offer.imageUrl || "",
    href: offer.href || "",
    id: offer.uri,

    valid_from: offer.validFrom,
    valid_through: offer.validThrough,

    price: offer.pricing.price || null,
    price_text: offer.pricing.text || "",
    pre_price: offer.pricing.prePrice || null,
    price_currency: offer.pricing.currency || "",
    standard_value: get(offer, ["value", "size", "standard", "min"], null),
    standard_value_unit: get(
      offer,
      ["value", "size", "unit", "si", "symbol"],
      null,
    ),
    standard_size: get(offer, ["quantity", "size", "standard", "min"], null),
    standard_size_unit: get(
      offer,
      ["quantity", "size", "unit", "si", "symbol"],
      null,
    ),

    categories: get(offer, ["categories"], []),
    dealer: offer.dealer || "",
    provenance: offer.provenance,
    gtins: get(offer, ["gtins"], {}),
    mpn_stock: offer.mpnStock || "",
    market: offer.market || "",

    pricing: offer.pricing || {},
    value: offer.value || {},
    quantity: offer.quantity || {},
  };
  requriedElasticOfferFields.forEach((key) => {
    if (!result[key]) {
      throw new Error(`Cannot add elastic offer without required field ${key}`);
    }
  });
  return result;
};
