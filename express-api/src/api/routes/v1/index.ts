import express from "express";
import { validate } from "express-validation";

import offerRoutes from "@/api/routes/v1/offers.route";
import { echoValidation } from "@/api/validations/echo.validation";

const router = express.Router();

router.get("/status", (req, res) => res.send("OK"));

router.get("/echo/:message", validate(echoValidation), (req, res) =>
  res.json({ message: req.params.message }),
);

router.use("/offers", offerRoutes);

export default router;
s;
