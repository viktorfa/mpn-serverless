import { router } from "typera-express";
import { Router } from "express";

import {
  getOfferGroup,
  getOfferGroups,
  postAddTagToOfferGroup,
  getTagsForOfferGroupHandler,
  putRemoveTagFromOfferGroup,
  getOfferGroupsForOffer,
  getOfferGroupsForOfferWithOffer,
} from "@/api/controllers/offer-groups.controller";

const routes: Router = router(
  getOfferGroups,
  getOfferGroup,
  postAddTagToOfferGroup,
  getTagsForOfferGroupHandler,
  putRemoveTagFromOfferGroup,
  getOfferGroupsForOffer,
  getOfferGroupsForOfferWithOffer,
).handler();

export default routes;
