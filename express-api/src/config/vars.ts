const dotenv = require("dotenv-safe");

if (!process.env.LAMBDA_TASK_ROOT) {
  let dotenvFileName = ".env.development";
  switch (process.env.NODE_ENV) {
    case "production":
      dotenvFileName = ".env.production";
      break;
    case "test":
      dotenvFileName = ".env.test";
      break;
  }

  const dotenvPath = `${dotenvFileName}`;

  dotenv.config({
    path: dotenvPath,
  });
}

export const port = process.env.PORT || 3000;

export const mongoUri = process.env.MONGO_URI;
export const mongoDatabase = process.env.MONGO_DATABASE;
export const elasticUrl = process.env.ELASTIC_URL;
export const elasticApiKey = process.env.ELASTIC_API_KEY;

export const stage = process.env.STAGE;
