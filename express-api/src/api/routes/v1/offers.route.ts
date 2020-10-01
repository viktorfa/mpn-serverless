import { router } from "typera-express";

import {
  list,
  find,
  promoted,
  similar,
} from "@/api/controllers/offers.controller";
import {
  search,
  searchPathParam,
  querySuggestion,
  registerClick,
} from "@/api/controllers/search.controller";

export default router(
  list,
  promoted,
  similar,
  search,
  querySuggestion,
  registerClick,
  searchPathParam,
  find,
).handler();
