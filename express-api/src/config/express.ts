import express from "express";

import routes from "@/api/routes/v1";
import {
  converter as errorConverter,
  notFound,
  handler as errorHandler,
} from "@/api/middlewares/error";

const app = express();
app.use("/v1", routes);

// if error is not an instanceOf APIError, convert it.
app.use(errorConverter);

// catch 404 and forward to error handler
app.use(notFound);

// error handler, send stacktrace only during development
app.use(errorHandler);

export default app;
