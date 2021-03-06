import express from "express";
import { validate } from "express-validation";

import offerRoutes from "@/api/routes/v1/offers.route";
import offerRelationsRoutes from "@/api/routes/v1/offers-relations.route";
import reviewsRoutes from "@/api/routes/v1/reviews.route";
import comparisonRoutes from "@/api/routes/v1/comparisons.route";
import offerGroupsRoute from "@/api/routes/v1/offer-groups.route";
import { echoValidation } from "@/api/validations/echo.validation";

const router = express.Router();

router.get("/status", (req, res) => res.send("OK"));

router.get("/echo/:message", validate(echoValidation), (req, res) =>
  res.json({ message: req.params.message }),
);

router.use("/offers", offerRoutes);
router.use("/offer-relations", offerRelationsRoutes);
router.use("/reviews", reviewsRoutes);
router.use("/comparisons", comparisonRoutes);
router.use("/offer-groups", offerGroupsRoute);

export default router;
