import { router } from "typera-express";

import { addIdenticalOffers } from "@/api/controllers/offer-relations.controller";

export default router(addIdenticalOffers).handler();
