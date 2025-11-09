import FastifyOtelInstrumentation from "@fastify/otel";

// If serverName is not provided, it will fallback to OTEL_SERVICE_NAME
// as per https://opentelemetry.io/docs/languages/sdk-configuration/general/.
export const fastifyOtelInstrumentation = new FastifyOtelInstrumentation({
  servername: process.env.OTEL_SERVICE_NAME,
});
fastifyOtelInstrumentation.setTracerProvider(provider);
