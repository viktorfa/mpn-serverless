import serverless from "serverless-http";
import "regenerator-runtime/runtime"; // Regenerator runtime must be imported when using babel

import app from "@/config/express";
import { port } from "@/config/vars";

if (process.env.NODE_ENV === "test") {
  app.listen(port, () => {
    console.log(`⚡️[server]: Server is running at ${port}`);
  });
} else {
  module.exports.handler = serverless(app);
}
