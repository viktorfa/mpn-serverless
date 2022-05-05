import { router } from "typera-express";
import { Router } from "express";

import {
  offerPricingHistory,
  list,
  find,
  promoted,
  similarV1,
  similarEndV1,
  addToElastic,
  relatedOffers,
  postAddTagToOffers,
  getTagsForOfferHandler,
  putRemoveTagFromOffers,
  extraV1,
  putOfferQuantity,
  getOfferGroups,
  findByGtin,
  offersWithPriceDifference,
} from "@/api/controllers/offers.controller";
import {
  searchV1,
  querySuggestion,
  registerClick,
  searchExtraV1,
} from "@/api/controllers/search.controller";

const routes: Router = router(
  offersWithPriceDifference,
  offerPricingHistory,
  getOfferGroups,
  list,
  promoted,
  similarV1,
  similarEndV1,
  addToElastic,
  searchV1,
  searchExtraV1,
  extraV1,
  putOfferQuantity,
  querySuggestion,
  registerClick,
  find,
  relatedOffers,
  postAddTagToOffers,
  getTagsForOfferHandler,
  putRemoveTagFromOffers,
  findByGtin,
).handler();

export default routes;
