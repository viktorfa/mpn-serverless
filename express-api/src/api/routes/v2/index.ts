import express from "express";

import offerRoutes from "@/api/routes/v1/offers.route";
import offerRoutesV2 from "@/api/routes/v2/offers.route";
import offerRelationsRoutes from "@/api/routes/v1/offers-relations.route";
import reviewsRoutes from "@/api/routes/v1/reviews.route";
import comparisonRoutes from "@/api/routes/v1/comparisons.route";
import offerGroupsRoute from "@/api/routes/v1/offer-groups.route";
import categoriesRoute from "@/api/routes/v1/categories.route";
import spiderrunsRoute from "@/api/routes/v1/spiderruns.route";
import handlerunsRoute from "@/api/routes/v1/handleruns.route";
import promotionsRoute from "@/api/routes/v2/promotions.route";

const router = express.Router();

router.get("/status", (req, res) => res.send("OK"));
router.get("/me", (req, res) => res.send(req["user"]));

router.get("/echo/:message", (req, res) =>
  res.json({ message: req.params.message }),
);

router.use("/offers", offerRoutesV2);
router.use("/offers", offerRoutes);
router.use("/categories", categoriesRoute);
router.use("/offer-relations", offerRelationsRoutes);
router.use("/reviews", reviewsRoutes);
router.use("/comparisons", comparisonRoutes);
router.use("/offer-groups", offerGroupsRoute);
router.use("/spiderruns", spiderrunsRoute);
router.use("/handleruns", handlerunsRoute);
router.use("/plakater", promotionsRoute);

export default router;
