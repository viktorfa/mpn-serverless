import path from "path";
import dotenv from "dotenv-safe";

let dotenvFileName = ".env.development";
switch (process.env.NODE_ENV) {
  case "production":
    dotenvFileName = ".env.production";
    break;
  case "test":
    dotenvFileName = ".env.test";
    break;
}
console.log(`Env file: ${path.resolve(`${dotenvFileName}`)}`);
dotenv.config({
  path: path.resolve(`${dotenvFileName}`),
});
console.log(process.env.ELASTIC_URL);
