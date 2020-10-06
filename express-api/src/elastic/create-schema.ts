import "./config";
import { ensureOfferSchema } from "./schema";

const run = async () => {
  const engineName = process.argv.slice(2)[0];
  if (!engineName) {
    throw new Error("Need engine name as cmd argument.");
  }
  console.log(`Creating engine, schema, and weights for ${engineName}`);
  await ensureOfferSchema(engineName);
  console.log("Fin.");
};
run();
