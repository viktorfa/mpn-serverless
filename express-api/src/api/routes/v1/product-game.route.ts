import { router } from "typera-express";
import { Router } from "express";

import {
  getRandomOffer,
  registerSkipOffer,
} from "@/api/controllers/product-game.controller";

const routes: Router = router(getRandomOffer, registerSkipOffer).handler();

export default routes;
