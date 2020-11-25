import { router } from "typera-express";

import { getReviews, add } from "@/api/controllers/reviews.controller";

export default router(getReviews, add).handler();
