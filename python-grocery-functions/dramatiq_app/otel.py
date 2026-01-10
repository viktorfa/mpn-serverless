import logging
import os

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


def initialize_opentelemetry():
    """Initialize OpenTelemetry with auto-instrumentation"""
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    stage = os.environ.get("STAGE", "unknown")
    git_commit = os.environ.get("GIT_COMMIT", "unknown")

    # Create resource
    resource = Resource.create(
        {
            "service.version": git_commit,
            "service.namespace": "mpn",
            "service.name": "mpn-dramatiq",
            "deployment.environment": stage,
        }
    )

    if endpoint:
        # Setup tracing
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
        tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True)))

        # Setup metrics
        metric_reader = PeriodicExportingMetricReader(
            exporter=OTLPMetricExporter(endpoint=endpoint, insecure=True),
            export_interval_millis=60000,
        )
        metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

        # Setup logging
        logger_provider = LoggerProvider(resource=resource)
        set_logger_provider(logger_provider)
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(endpoint=endpoint, insecure=True)))
        handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
        logging.getLogger().addHandler(handler)

        logger.info(f"OpenTelemetry initialized with endpoint: {endpoint}")
    else:
        logger.warning("OTEL_EXPORTER_OTLP_ENDPOINT not set - telemetry will not be exported")

    # Auto-instrument libraries
    try:
        RedisInstrumentor().instrument()
        Psycopg2Instrumentor().instrument()
        SQLAlchemyInstrumentor().instrument()
        LoggingInstrumentor().instrument()
        logger.info("Auto-instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument some libraries: {e}")
