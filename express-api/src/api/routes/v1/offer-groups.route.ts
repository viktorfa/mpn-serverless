import { router } from "typera-express";

import {
  getOfferGroup,
  getOfferGroups,
} from "@/api/controllers/offer-groups.controller";

export default router(getOfferGroups, getOfferGroup).handler();
