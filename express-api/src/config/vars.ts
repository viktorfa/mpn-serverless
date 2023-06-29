const dotenv = require("dotenv-safe");

if (!process.env.LAMBDA_TASK_ROOT) {
  let dotenvFileName = ".env.dev";
  switch (process.env.NODE_ENV) {
    case "production":
      dotenvFileName = ".env.prod";
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

export const port = process.env.PORT || 3010;

export const mongoUri = process.env.MONGO_URI;
export const mongoDatabase = process.env.MONGO_DATABASE;

export const stage = process.env.STAGE;
