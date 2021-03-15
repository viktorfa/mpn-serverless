import express from "express";
import morgan from "morgan";
import bodyParser from "body-parser";
import cors from "cors";

import * as Sentry from "@sentry/node";
import * as Tracing from "@sentry/tracing";

import routes from "@/api/routes/v1";
import { sentryDsn } from "./vars";

const app = express();

Sentry.init({
  dsn: sentryDsn,
  integrations: [
    // enable HTTP calls tracing
    new Sentry.Integrations.Http({ tracing: true }),
    // enable Express.js middleware tracing
    new Tracing.Integrations.Express({ app }),
  ],

  // We recommend adjusting this value in production, or using tracesSampler
  // for finer control
  tracesSampleRate: 1.0,
});

app.use(Sentry.Handlers.requestHandler());

app.use(cors());
app.use(morgan("tiny"));
app.use(bodyParser.json());

app.use("/v1", routes);

app.use(Sentry.Handlers.errorHandler());

export default app;
