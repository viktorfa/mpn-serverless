import type { AWS } from "@serverless/typescript";

// Only use API Gateway locally as only that is supported by serverless-offline
// Lambda URLS cost less, are faster, and have longer timeout
const functions: AWS["functions"] = {};
if (process.argv.includes("offline")) {
  functions.api = {
    timeout: 30,
    handler: "src/server.handler",
    events: [
      {
        http: {
          method: "ANY",
          path: "/",
        },
      },
      {
        http: {
          method: "ANY",
          path: "{proxy+}",
        },
      },
    ],
  };
} else {
  functions.api = {
    timeout: 30,
    handler: "src/server.handler",
  };
  functions["api-url"] = {
    timeout: 30,
    handler: "src/server.handler",
    disableLogs: true,
    url: { cors: true },
  };
}

const serverlessConfiguration: AWS = {
  service: "node-express-read-api",
  frameworkVersion: "3",
  useDotenv: true,
  provider: {
    name: "aws",
    runtime: "nodejs20.x",
    region: "eu-central-1",
    logRetentionInDays: 1,
    profile: "serverless-grocery-admin",
    memorySize: 512,
    versionFunctions: false,
    environment: {
      MONGO_URI: "${env:MONGO_URI}",
      MONGO_DATABASE: "${env:MONGO_DATABASE}",
      NHOST_JWT_SECRET: "${env:NHOST_JWT_SECRET}",
      SENTRY_DSN: "${env:SENTRY_DSN}",
      SENTRY_ENVIRONMENT: "${sls:stage}", // ${sls:stage} == ${opt:stage, self:provider.stage, "dev"}
      STAGE: "${sls:stage}",
    },
    apiGateway: {
      minimumCompressionSize: 1024,
    },
  },
  functions,
  custom: {
    esbuild: {
      bundle: true,
      minify: true,
      sourcemap: true,
      exclude: ["aws-sdk"],
      target: "node20",
      define: { "require.resolve": undefined },
      platform: "node",
      concurrency: 10,
      watch: {
        pattern: ["src/**/*.ts", "serverless.ts"],
      },
    },
  },
  plugins: ["serverless-offline", "serverless-esbuild"],
};

module.exports = serverlessConfiguration;
