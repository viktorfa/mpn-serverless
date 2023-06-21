import { router } from "typera-express";
import { Router } from "express";

import {
  offerPricingHistory,
  list,
  find,
  promoted,
  postAddTagToOffers,
  getTagsForOfferHandler,
  putRemoveTagFromOffers,
  putOfferQuantity,
  getOfferGroups,
  offersWithPriceDifference,
} from "@/api/controllers/offers.controller";

const routes: Router = router(
  offersWithPriceDifference,
  offerPricingHistory,
  getOfferGroups,
  list,
  promoted,
  putOfferQuantity,
  find,
  postAddTagToOffers,
  getTagsForOfferHandler,
  putRemoveTagFromOffers,
).handler();

export default routes;
