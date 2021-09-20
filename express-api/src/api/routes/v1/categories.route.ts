import { router } from "typera-express";
import { Router } from "express";

import { getByKey, list } from "@/api/controllers/categories.controller";

const routes: Router = router(list, getByKey).handler();

export default routes;
