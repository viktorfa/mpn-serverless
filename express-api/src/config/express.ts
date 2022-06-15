import express from "express";
import morgan from "morgan";
import bodyParser from "body-parser";

import firebaseAuth from "@/api/auth/firebase";
import routesV1 from "@/api/routes/v1";
import routesV2 from "@/api/routes/v2";
import * as Sentry from "@sentry/serverless";

const app = express();

app.use(morgan("tiny"));

app.use((req, _res, next) => {
  console.info(req.url);
  next();
});
app.use((req, _res, next) => {
  Sentry.AWSLambda.getCurrentHub().setTag(
    "path",
    req.url.replace(/[^\/]+:product:[^\/]+/, "_uri_"),
  );
  next();
});

app.use(firebaseAuth);

app.use(bodyParser.json());

app.use("/v1", routesV1);
app.use("/v2", routesV2);

/*app.use((_req, res, next) => {
  Sentry.AWSLambda.getCurrentHub().setTag("statusCode", res.statusCode);
  if (res.statusCode >= 400) {
    Sentry.AWSLambda.getCurrentHub().captureMessage(
      res.statusMessage,
      Sentry.Severity.Warning,
    );
  }
  next();
});*/

export default app;
