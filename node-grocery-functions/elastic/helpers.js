const get = require("lodash/get");

/**
 *
 * @param {import("@/types/offers").MpnOffer} offer
 * @returns {import("@/types/offers").ElasticMpnOffer}
 */
const mpnOfferToElasticOffer = (offer) => {
  const result = {
    title: offer.title,
    subtitle: offer.subtitle,
    short_description: offer.shortDescription,
    description: offer.description,
    brand: offer.brand,

    image_url: offer.imageUrl,
    href: offer.href,
    id: offer.uri,

    valid_from: offer.validFrom,
    valid_through: offer.validThrough,

    price: offer.pricing.price,
    pre_price: offer.pricing.prePrice,
    price_currency: offer.pricing.currency,
    standard_value: get(offer, ["value", "size", "standard", "min"]),
    standard_value_unit: get(offer, ["value", "size", "unit", "si", "symbol"]),
    standard_size: get(offer, ["quantity", "size", "standard", "min"]),
    standard_size_unit: get(offer, [
      "quantity",
      "size",
      "unit",
      "si",
      "symbol",
    ]),

    categories: get(offer, ["categories"], []),
    dealer: offer.dealer,
    provenance: offer.provenance,
    gtins: get(offer, ["gtins"], {}),
    mpn_stock: offer.mpnStock,
    mpn_properties: Object.values(offer.mpnProperties || []).map(
      (x) => x.value,
    ),
    mpn_ingredients: Object.values(offer.mpnIngredients || []).map(
      (x) => x.key,
    ),
    mpn_categories: (offer.mpnCategories || []).map((x) => x.key),

    nutrition_carbohydrates: get(offer, [
      "mpnNutrition",
      "carbohydrates",
      "value",
    ]),
    nutrition_proteins: get(offer, ["mpnNutrition", "proteins", "value"]),
    nutrition_fats: get(offer, ["mpnNutrition", "fats", "value"]),
    nutrition_energy: get(offer, ["mpnNutrition", "energy", "value"]),
    nutrition_fibers: get(offer, ["mpnNutrition", "fibers", "value"]),

    pricing: offer.pricing,
    value: offer.value,
    quantity: offer.quantity,

    market: offer.market,
    is_partner: offer.isPartner,
    site_collection: offer.siteCollection,
  };
  return result;
};

module.exports = { mpnOfferToElasticOffer };
