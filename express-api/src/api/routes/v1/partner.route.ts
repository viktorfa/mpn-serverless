import { router } from "typera-express";
import { Router } from "express";

import { getPartnerProducts } from "@/api/controllers/partner.controller";

const routes: Router = router(getPartnerProducts).handler();

export default routes;
