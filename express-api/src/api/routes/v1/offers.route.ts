import { router } from "typera-express";

import {
  list,
  find,
  promoted,
  similar,
  addToElastic,
  relatedOffers,
  postAddTagToOffers,
  getTagsForOfferHandler,
  similarExtra,
  similarFromExtra,
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
  addToElastic,
  search,
  searchExtra,
  similarExtra,
  similarFromExtra,
  querySuggestion,
  registerClick,
  searchPathParam,
  find,
  relatedOffers,
  postAddTagToOffers,
  getTagsForOfferHandler,
).handler();
