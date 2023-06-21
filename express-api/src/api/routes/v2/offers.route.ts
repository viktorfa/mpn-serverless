import { router } from "typera-express";
import { Router } from "express";

import {
  search,
  searchExtra,
  searchRelations,
} from "@/api/controllers/search.controller";
import {
  similar,
  similarEnd,
  extra,
  extraRelations,
  similarPromoted,
  offerPricingHistoryV2,
  getDetailedOffers,
  findV2,
} from "@/api/controllers/offers.controller";

const routes: Router = router(
  search,
  searchExtra,
  searchRelations,
  extra,
  extraRelations,
  similar,
  similarEnd,
  similarPromoted,
  offerPricingHistoryV2,
  getDetailedOffers,
  findV2,
).handler();

export default routes;
