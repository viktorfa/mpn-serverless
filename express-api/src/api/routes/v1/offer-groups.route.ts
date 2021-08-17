import { router } from "typera-express";

import {
  getOfferGroup,
  getOfferGroups,
  postAddTagToOfferGroup,
  getTagsForOfferGroupHandler,
  putRemoveTagFromOfferGroup,
  getOfferGroupsForOffer,
} from "@/api/controllers/offer-groups.controller";

export default router(
  getOfferGroups,
  getOfferGroup,
  postAddTagToOfferGroup,
  getTagsForOfferGroupHandler,
  putRemoveTagFromOfferGroup,
  getOfferGroupsForOffer,
).handler();
