import { router } from "typera-express";

import {
  addIdenticalOffers,
  removeOfferRelation,
} from "@/api/controllers/offer-relations.controller";

export default router(addIdenticalOffers, removeOfferRelation).handler();
