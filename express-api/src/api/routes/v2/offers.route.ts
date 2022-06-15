import { router } from "typera-express";
import { Router } from "express";

import { search, searchExtra } from "@/api/controllers/search.controller";
import {
  similar,
  similarEnd,
  extra,
  similarPromoted,
  offerPricingHistoryV2,
  getDetailedOffers,
} from "@/api/controllers/offers.controller";

const routes: Router = router(
  search,
  searchExtra,
  extra,
  similar,
  similarEnd,
  similarPromoted,
  offerPricingHistoryV2,
  getDetailedOffers,
).handler();

export default routes;
