import { router } from "typera-express";
import { Router } from "express";

import {
  getPartner,
  getPartnerProducts,
  getPartnerShopWithProducts,
  getPartners,
  getProducts,
} from "@/api/controllers/partner.controller";

const routes: Router = router(
  getPartners,
  getProducts,
  getPartner,
  getPartnerProducts,
  getPartnerShopWithProducts,
).handler();

export default routes;
