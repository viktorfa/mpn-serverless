import { router } from "typera-express";
import { Router } from "express";

import {
  putOffer,
  getBors,
  getData,
  putConfig,
} from "@/api/controllers/comparisons.controller";

const routes: Router = router(putOffer, getBors, getData, putConfig).handler();

export default routes;
