import { router } from "typera-express";
import { Router } from "express";

import {
  getByGtin,
  extraRelations,
  mergeIdenticalRelations,
  unmergeIdenticalRelations,
  addIdenticalOffers,
  removeOfferRelation,
  updateOfferRelation,
  getById,
} from "@/api/controllers/offer-relations.controller";

const routes: Router = router(
  getByGtin,
  extraRelations,
  mergeIdenticalRelations,
  unmergeIdenticalRelations,
  addIdenticalOffers,
  removeOfferRelation,
  updateOfferRelation,
  getById,
).handler();

export default routes;
