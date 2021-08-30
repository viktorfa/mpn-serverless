import { router } from "typera-express";

import {
  getReviews,
  add,
  remove,
  listReviewsWithOffers,
  approve,
} from "@/api/controllers/reviews.controller";

export default router(
  listReviewsWithOffers,
  getReviews,
  add,
  remove,
  approve,
).handler();
