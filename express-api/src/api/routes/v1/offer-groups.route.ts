import { router } from "typera-express";
import { Router } from "express";

import {
  getOfferGroup,
  getOfferGroups,
  postAddTagToOfferGroup,
  getTagsForOfferGroupHandler,
  putRemoveTagFromOfferGroup,
  getOfferGroupsForOffer,
} from "@/api/controllers/offer-groups.controller";

const routes: Router = router(
  getOfferGroups,
  getOfferGroup,
  postAddTagToOfferGroup,
  getTagsForOfferGroupHandler,
  putRemoveTagFromOfferGroup,
  getOfferGroupsForOffer,
).handler();

export default routes;
