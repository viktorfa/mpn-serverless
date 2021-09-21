import { router } from "typera-express";
import { Router } from "express";

import { getGrouped } from "@/api/controllers/handleruns.controller";

const routes: Router = router(getGrouped).handler();

export default routes;
