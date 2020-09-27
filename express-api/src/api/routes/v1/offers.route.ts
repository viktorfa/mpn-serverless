import { router } from "typera-express";

import { list } from "@/api/controllers/offers.controller";
import {
  search,
  querySuggestion,
  registerClick,
} from "@/api/controllers/search.controller";

export default router(list, search, querySuggestion, registerClick).handler();
