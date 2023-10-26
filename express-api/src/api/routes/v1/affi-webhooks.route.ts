import { router } from "typera-express";
import { Router } from "express";

import { adTractionPurchase } from "@/api/controllers/affi-webhooks.controller";

const routes: Router = router(adTractionPurchase).handler();

export default routes;
