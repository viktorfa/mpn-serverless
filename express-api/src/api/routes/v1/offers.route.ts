import { router } from "typera-express";
import { Router } from "express";

import {
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
} from "@/api/controllers/offers.controller";
import {
  search,
  searchPathParam,
  querySuggestion,
  registerClick,
  searchExtra,
} from "@/api/controllers/search.controller";

const routes: Router = router(
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
).handler();

export default routes;
