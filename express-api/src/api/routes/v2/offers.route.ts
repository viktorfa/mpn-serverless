import { router } from "typera-express";
import { Router } from "express";

import { search, searchExtra } from "@/api/controllers/search.controller";
import {
  similar,
  similarEnd,
  extra,
} from "@/api/controllers/offers.controller";

const routes: Router = router(
  search,
  searchExtra,
  extra,
  similar,
  similarEnd,
).handler();

export default routes;
