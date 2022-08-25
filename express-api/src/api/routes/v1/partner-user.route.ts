import { router } from "typera-express";
import { Router } from "express";

import {
  getProducts,
  getPartner,
  createPartnerProduct,
  deletePartnerProduct,
  updatePartnerProduct,
} from "@/api/controllers/partner-user.controller";

const routes: Router = router(
  getProducts,
  getPartner,
  createPartnerProduct,
  deletePartnerProduct,
  updatePartnerProduct,
).handler();

export default routes;
