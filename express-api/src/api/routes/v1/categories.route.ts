import { router } from "typera-express";
import { Router } from "express";

import {
  getAllCategoriesForDealer,
  getCategoryMappingsForDealer,
  list,
  getByKey,
  setMapping,
} from "@/api/controllers/categories.controller";

const routes: Router = router(
  getAllCategoriesForDealer,
  getCategoryMappingsForDealer,
  list,
  getByKey,
  setMapping,
).handler();

export default routes;
