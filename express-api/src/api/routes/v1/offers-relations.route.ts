import { router } from "typera-express";
import { Router } from "express";

import {
  addIdenticalOffers,
  removeOfferRelation,
  updateOfferRelation,
} from "@/api/controllers/offer-relations.controller";

const routes: Router = router(
  addIdenticalOffers,
  removeOfferRelation,
  updateOfferRelation,
).handler();

export default routes;
