export const DEFAULT_PRODUCT_COLLECTION = "groceryoffer";

export const OfferRelation: Record<OfferRelationType, OfferRelationType> = {
  identical: "identical",
  interchangeable: "interchangeable",
  similar: "similar",
  related: "related",
  lowerend: "lowerend",
  higherend: "higherend",
  usedtogether: "usedtogether",
};
