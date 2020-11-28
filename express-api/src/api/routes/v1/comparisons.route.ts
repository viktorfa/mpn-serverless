import { router } from "typera-express";

import {
  putOffer,
  getBors,
  getData,
  putConfig,
} from "@/api/controllers/comparisons.controller";

export default router(putOffer, getBors, getData, putConfig).handler();
