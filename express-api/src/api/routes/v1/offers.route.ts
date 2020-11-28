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
} from "@/api/controllers/offers.controller";
import {
  search,
  searchPathParam,
  querySuggestion,
  registerClick,
} from "@/api/controllers/search.controller";

export default router(
  list,
  promoted,
  similar,
  addToElastic,
  search,
  querySuggestion,
  registerClick,
  searchPathParam,
  find,
  relatedOffers,
  postAddTagToOffers,
  getTagsForOfferHandler,
).handler();
