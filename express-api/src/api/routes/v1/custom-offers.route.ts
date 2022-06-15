import { router } from "typera-express";
import { Router } from "express";

import { postCustomOffer } from "@/api/controllers/custom-offers.controller";

const routes: Router = router(postCustomOffer).handler();

export default routes;
