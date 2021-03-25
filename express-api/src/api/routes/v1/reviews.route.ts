import { router } from "typera-express";

import { getReviews, add, remove } from "@/api/controllers/reviews.controller";

export default router(getReviews, add, remove).handler();
