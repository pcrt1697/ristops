from pydantic import Field, model_validator
from pydantic_settings import SettingsConfigDict

from ristops_lib_core.settings import BaseServiceSettings, ENVVARS_PREFIX


class TelemetrySettings(BaseServiceSettings):
    """ Settings for the OpenTelemetry instrumentation framework. """

    model_config = SettingsConfigDict(
        env_prefix=ENVVARS_PREFIX + "OTEL_",
    )

    enabled: bool = Field(
        default=False,
        description=(
            "Master switch for tracing, metrics and log export. Disabled is a true no-op: no "
            "provider or instrumentor is installed and no connection to the collector is "
            "attempted, so a service started on the host carries zero telemetry overhead."
        ),
    )
    service_name: str | None = Field(
        default=None,
        description=(
            "Resource `service.name` reported on every span/metric/log. No default on purpose — "
            "every process must identify itself explicitly; a silently shared fallback name would "
            "make signals from different services indistinguishable in Tempo/Grafana. Only "
            "required when `enabled` is true (see validator below) — a disabled service on the "
            "host doesn't need to declare one."
        ),
    )

    @model_validator(mode="after")
    def _require_service_name_when_enabled(self) -> "TelemetrySettings":
        if self.enabled and not self.service_name:
            raise ValueError(
                "RISTOPS_OTEL_SERVICE_NAME is required when RISTOPS_OTEL_ENABLED is true"
            )
        return self
    service_version: str = Field(
        default="0.1.0",
        description="Resource `service.version` reported on every span/metric/log.",
    )
    environment: str = Field(
        default="local",
        description="Resource `deployment.environment` reported on every span/metric/log.",
    )
    endpoint: str = Field(
        default="http://localhost:4317",
        description="OTLP gRPC endpoint of the collector.",
    )
    sample_ratio: float = Field(
        default=1.0,
        description=(
            "Fraction of traces to sample (1.0 = all). A local/training deployment has no "
            "volume problem that needs head sampling."
        ),
        ge=0.0,
        le=1.0,
    )
    metric_interval_ms: int = Field(
        default=10_000,
        description="Interval, in milliseconds, between metric exports.",
        gt=0,
    )
    console_export: bool = Field(
        default=False,
        description=(
            "Also print spans to stdout. Debug escape hatch for when the collector itself is "
            "the thing being debugged."
        ),
    )
