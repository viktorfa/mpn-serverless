import "source-map-support/register";

import dotenv from "dotenv-safe";
import path from "node:path";
import { fastifyApp } from "./app";

dotenv.config({
  path: path.join(__dirname, "..", ".env.local"),
  example: path.join(__dirname, "..", ".env.example"),
});

// Run the server!
fastifyApp.listen({ port: 3000, host: "0.0.0.0" }, function (err, address) {
  if (err) {
    fastifyApp.log.error(err);
    process.exit(1);
  }
  console.log(`Server is now listening on ${address}`);
});
