import { router } from "typera-express";

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
} from "@/api/controllers/offers.controller";
import {
  search,
  searchPathParam,
  querySuggestion,
  registerClick,
  searchExtra,
} from "@/api/controllers/search.controller";

export default router(
  list,
  promoted,
  similar,
  similarEnd,
  addToElastic,
  search,
  searchExtra,
  extra,
  querySuggestion,
  registerClick,
  searchPathParam,
  find,
  relatedOffers,
  postAddTagToOffers,
  getTagsForOfferHandler,
  putRemoveTagFromOffers,
).handler();
