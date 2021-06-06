import { router } from "typera-express";

import {
  addIdenticalOffers,
  removeOfferRelation,
  updateOfferRelation,
} from "@/api/controllers/offer-relations.controller";

export default router(
  addIdenticalOffers,
  removeOfferRelation,
  updateOfferRelation,
).handler();
