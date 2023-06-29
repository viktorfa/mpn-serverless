import { router } from "typera-express";
import { Router } from "express";

import {
  getProducts,
  getPartner,
  createPartnerProduct,
  deletePartnerProduct,
  updatePartnerProduct,
  updatePartnerStore,
} from "@/api/controllers/partner-user.controller";

const routes: Router = router(
  getProducts,
  getPartner,
  createPartnerProduct,
  deletePartnerProduct,
  updatePartnerProduct,
  updatePartnerStore,
).handler();

export default routes;
