import logging

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

from ristops_lib_otel.settings import TelemetrySettings

_logger = logging.getLogger(__name__)

_configured = False


def configure_telemetry() -> None:
    """ Configure tracing, metrics and log export.

    A true no-op when ``RISTOPS_OTEL_ENABLED`` is unset (the default): no provider is installed
    and no connection to the collector is attempted, so a service started on the host carries
    zero telemetry overhead unless explicitly opted in. Call once per process, before
    ``instrument_app``/``instrument_clients``.

    ``service.name``/``service.version``/``deployment.environment`` come from
    ``TelemetrySettings`` (``RISTOPS_OTEL_SERVICE_NAME`` etc.) rather than a Python-code argument,
    so identifying a process is a deployment concern, not something baked into `app.py`.
    """
    global _configured
    settings = TelemetrySettings.get()
    if not settings.enabled:
        return
    if _configured:
        _logger.warning("Telemetry already configured for this process, skipping")
        return

    resource = Resource.create({
        "service.name": settings.service_name,
        "service.version": settings.service_version,
        "deployment.environment": settings.environment,
    })

    _configure_tracing(resource, settings)
    _configure_metrics(resource, settings)
    _configure_logging(resource, settings)

    # injects trace_id/span_id (as otelTraceID/otelSpanID) onto every LogRecord app-wide; we keep
    # our own LINE_FORMAT for stdout, so leave the format string itself untouched
    LoggingInstrumentor().instrument(set_logging_format=False)

    _configured = True
    _logger.info("Telemetry configured for '%s' -> %s", settings.service_name, settings.endpoint)


def _configure_tracing(resource: Resource, settings: TelemetrySettings) -> None:
    provider = TracerProvider(resource=resource, sampler=TraceIdRatioBased(settings.sample_ratio))
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.endpoint, insecure=True))
    )
    if settings.console_export:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)


def _configure_metrics(resource: Resource, settings: TelemetrySettings) -> None:
    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=settings.endpoint, insecure=True),
        export_interval_millis=settings.metric_interval_ms,
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))


def _configure_logging(resource: Resource, settings: TelemetrySettings) -> None:
    provider = LoggerProvider(resource=resource)
    provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=settings.endpoint, insecure=True))
    )
    set_logger_provider(provider)
    # additive: the stdout handler from ristops_lib_core.logging.configure_logging() is untouched
    # and keeps producing readable text; this handler ships the same records to Loki as OTLP
    logging.getLogger().addHandler(LoggingHandler(logger_provider=provider))
