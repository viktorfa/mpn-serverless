import express from "express";

import partnerRoutes from "@/api/routes/v1/partner-user.route";

import cognitoAuth from "@/api/auth/cognito";

const router = express.Router();

router.use(cognitoAuth);

router.use(partnerRoutes);

export default router;
