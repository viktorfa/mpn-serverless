import serverless from "serverless-http";

import app from "@/config/express";
import { port } from "@/config/vars";

const Sentry = require("@sentry/serverless");

Sentry.AWSLambda.init({
  // 1 of every 1000 transactions are sampled for performance monitoring
  tracesSampleRate: process.env.STAGE === "prod" ? 0.001 : 1.0,
});

if (process.env.NODE_ENV === "test") {
  app.listen(port, () => {
    console.log(`⚡️[server]: Server is running at ${port}`);
  });
} else {
  module.exports.handler = Sentry.AWSLambda.wrapHandler(serverless(app));
}
