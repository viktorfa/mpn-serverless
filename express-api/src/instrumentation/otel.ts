// otel.ts
import { diag, DiagConsoleLogger, DiagLogLevel } from "@opentelemetry/api";
import { NodeSDK } from "@opentelemetry/sdk-node";
import { getNodeAutoInstrumentations } from "@opentelemetry/auto-instrumentations-node";

// Exporters
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { OTLPMetricExporter } from "@opentelemetry/exporter-metrics-otlp-http";
import { PeriodicExportingMetricReader } from "@opentelemetry/sdk-metrics";

// Dev-only exporters (don’t use these in prod)
import { ConsoleSpanExporter } from "@opentelemetry/sdk-trace-base";
import { ConsoleMetricExporter } from "@opentelemetry/sdk-metrics";

const useHttpExporter = !!process.env.OTEL_EXPORTER_OTLP_ENDPOINT;
const isProd = process.env.STAGE === "prod";

// OTel SDK/log verbosity
diag.setLogger(
  new DiagConsoleLogger(),
  isProd ? DiagLogLevel.ERROR : DiagLogLevel.INFO,
);

// Exporters: in prod use OTLP; in dev keep console for quick feedback.
const traceExporter = useHttpExporter
  ? new OTLPTraceExporter() // uses OTEL_EXPORTER_OTLP_{TRACES_}ENDPOINT + HEADERS
  : new ConsoleSpanExporter();

const metricReader = useHttpExporter
  ? new PeriodicExportingMetricReader({
      exporter: new OTLPMetricExporter(), // uses OTEL_EXPORTER_OTLP_{METRICS_}ENDPOINT + HEADERS
      exportIntervalMillis: 60000,
    })
  : new PeriodicExportingMetricReader({
      exporter: new ConsoleMetricExporter(),
      exportIntervalMillis: 10000,
    });

const sdk = new NodeSDK({
  traceExporter,
  metricReader,
  instrumentations: [getNodeAutoInstrumentations()],
  // Resource/service.name comes from OTEL_SERVICE_NAME; other attrs from OTEL_RESOURCE_ATTRIBUTES.
  // Sampler from OTEL_TRACES_SAMPLER (e.g. always_on).
});

sdk.start();

// Graceful shutdown
const shutdown = () => sdk.shutdown().finally(() => process.exit(0));
process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);
