export const defaultDealerProjection = {
  key: 1,
  text: 1,
  logoUrl: 1,
  url: 1,
  market: 1,
};

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
