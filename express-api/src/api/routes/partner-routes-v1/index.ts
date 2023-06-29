import express from "express";

import partnerRoutes from "@/api/routes/v1/partner-user.route";

import nhostAuth from "@/api/auth/nhost";

const router = express.Router();

router.use(nhostAuth);

router.use(partnerRoutes);

export default router;
