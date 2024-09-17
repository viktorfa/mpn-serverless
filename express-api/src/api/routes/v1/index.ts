import express from "express";

import offerRoutes from "@/api/routes/v1/offers.route";
import offerRelationsRoutes from "@/api/routes/v1/offers-relations.route";
import reviewsRoutes from "@/api/routes/v1/reviews.route";
import comparisonRoutes from "@/api/routes/v1/comparisons.route";
import offerGroupsRoute from "@/api/routes/v1/offer-groups.route";
import categoriesRoute from "@/api/routes/v1/categories.route";
import spiderrunsRoute from "@/api/routes/v1/spiderruns.route";
import handlerunsRoute from "@/api/routes/v1/handleruns.route";
import promotionsRoute from "@/api/routes/v1/promotions.route";
import customOffersRoute from "@/api/routes/v1/custom-offers.route";
import productGameRoute from "@/api/routes/v1/product-game.route";
import partnerRoutes from "@/api/routes/v1/partner.route";
import affiWebhooks from "@/api/routes/v1/affi-webhooks.route";
import getLogsRoute from "@/api/routes/v1/s3-logs.route";

const router = express.Router();

router.get("/status", (req, res) => res.send("OK"));
router.get("/me", (req, res) => res.send(req["user"]));

router.get("/echo/:message", (req, res) =>
  res.json({ message: req.params.message }),
);

router.use("/offers", offerRoutes);
router.use("/offers", customOffersRoute);
router.use("/categories", categoriesRoute);
router.use("/offer-relations", offerRelationsRoutes);
router.use("/reviews", reviewsRoutes);
router.use("/comparisons", comparisonRoutes);
router.use("/offer-groups", offerGroupsRoute);
router.use("/spiderruns", spiderrunsRoute);
router.use("/handleruns", handlerunsRoute);
router.use("/plakater", promotionsRoute);
router.use("/product-game", productGameRoute);
router.use("/partners", partnerRoutes);
router.use("/affi-webhooks", affiWebhooks);
router.use("/spiderruns/logs", getLogsRoute);

export default router;
