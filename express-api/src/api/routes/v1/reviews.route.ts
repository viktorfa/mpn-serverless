import { router } from "typera-express";
import { Router } from "express";

import {
  getReviews,
  add,
  remove,
  listReviewsWithOffers,
  approve,
} from "@/api/controllers/reviews.controller";

const routes: Router = router(
  listReviewsWithOffers,
  getReviews,
  add,
  remove,
  approve,
).handler();

export default routes;
