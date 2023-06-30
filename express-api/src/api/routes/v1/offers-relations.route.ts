import { router } from "typera-express";
import { Router } from "express";

import {
  mergeIdenticalRelations,
  unmergeIdenticalRelations,
  addIdenticalOffers,
  removeOfferRelation,
  updateOfferRelation,
} from "@/api/controllers/offer-relations.controller";

const routes: Router = router(
  mergeIdenticalRelations,
  unmergeIdenticalRelations,
  addIdenticalOffers,
  removeOfferRelation,
  updateOfferRelation,
).handler();

export default routes;
