import { router } from "typera-express";
import { Router } from "express";

import {
  search,
  searchRelationsCondensed,
  searchExtra,
  searchRelations,
} from "@/api/controllers/search.controller";
import {
  extra,
  extraRelations,
  offerPricingHistoryV2,
  getDetailedOffers,
  findV2,
} from "@/api/controllers/offers.controller";

const routes: Router = router(
  search,
  searchRelationsCondensed,
  searchExtra,
  searchRelations,
  extra,
  extraRelations,
  offerPricingHistoryV2,
  getDetailedOffers,
  findV2,
).handler();

export default routes;
