import { router } from "typera-express";
import { Router } from "express";

import {
  offerPricingHistory,
  list,
  find,
  promoted,
  similar,
  similarEnd,
  addToElastic,
  relatedOffers,
  postAddTagToOffers,
  getTagsForOfferHandler,
  putRemoveTagFromOffers,
  extra,
  putOfferQuantity,
  getOfferGroups,
  findByGtin,
} from "@/api/controllers/offers.controller";
import {
  search,
  searchPathParam,
  querySuggestion,
  registerClick,
  searchExtra,
} from "@/api/controllers/search.controller";

const routes: Router = router(
  offerPricingHistory,
  getOfferGroups,
  list,
  promoted,
  similar,
  similarEnd,
  addToElastic,
  search,
  searchExtra,
  extra,
  putOfferQuantity,
  querySuggestion,
  registerClick,
  searchPathParam,
  find,
  relatedOffers,
  postAddTagToOffers,
  getTagsForOfferHandler,
  putRemoveTagFromOffers,
  findByGtin,
).handler();

export default routes;
