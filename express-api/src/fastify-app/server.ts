import dotenv from "dotenv-safe";
import path from "path";
import { fastifyApp } from "./app";

dotenv.config({
  path: path.join(__dirname, "..", ".env.local"),
  example: path.join(__dirname, "..", ".env.example"),
});

// Run the server!
fastifyApp.listen({ port: 3000 }, function (err, address) {
  if (err) {
    fastifyApp.log.error(err);
    process.exit(1);
  }
  console.log(`Server is now listening on ${address}`);
});
