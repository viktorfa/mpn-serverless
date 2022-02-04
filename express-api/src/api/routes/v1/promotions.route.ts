import { router } from "typera-express";
import { Router } from "express";

import { getPromotions } from "@/api/controllers/promotions.controller";

const routes: Router = router(getPromotions).handler();

export default routes;
