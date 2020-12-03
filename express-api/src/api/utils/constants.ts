export const OfferRelation: Record<OfferRelationType, OfferRelationType> = {
  identical: "identical",
  interchangeable: "interchangeable",
  similar: "similar",
  related: "related",
  lowerend: "lowerend",
  higherend: "higherend",
  usedtogether: "usedtogether",
};

export const offerCollectionName = "mpnoffers";
export const offerRelationCollectionName = "offerrelations";
export const offerReviewsCollectionName = "offerreviews";
