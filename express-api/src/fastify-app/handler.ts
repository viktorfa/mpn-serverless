import { ServerlessAdapter } from "@h4ad/serverless-adapter";
import { ApiGatewayV2Adapter } from "@h4ad/serverless-adapter/adapters/aws";
import { DefaultHandler } from "@h4ad/serverless-adapter/handlers/default";
import { FastifyFramework } from "@h4ad/serverless-adapter/frameworks/fastify";
import { fastifyApp } from "./app";

export const handler = ServerlessAdapter.new(fastifyApp)
  .setHandler(new DefaultHandler())
  .setFramework(new FastifyFramework())
  // .setResolver(new PromiseResolver())
  .addAdapter(new ApiGatewayV2Adapter())
  // customizing:
  // .addAdapter(new ApiGatewayV2Adapter({ stripBasePath: '/prod' }))
  .build();
