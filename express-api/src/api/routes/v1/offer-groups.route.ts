import { router } from "typera-express";

import { getOfferGroups } from "@/api/controllers/offer-groups.controller";

export default router(getOfferGroups).handler();
