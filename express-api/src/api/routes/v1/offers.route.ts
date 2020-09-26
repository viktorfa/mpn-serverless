import { router } from "typera-express";

import { list, search } from "@/api/controllers/offers.controller";

export default router(list, search).handler();
