import { router } from "typera-express";
import { Router } from "express";

import { getPromotionsV2 } from "@/api/controllers/promotions.controller";

const routes: Router = router(getPromotionsV2).handler();

export default routes;
