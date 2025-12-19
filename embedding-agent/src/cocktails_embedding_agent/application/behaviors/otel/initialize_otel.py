import atexit
import logging
import os
import socket
from importlib.metadata import version

from cezzis_otel import OTelSettings, initialize_otel, shutdown_otel
from opentelemetry.instrumentation.confluent_kafka import (  # type: ignore
    ConfluentKafkaInstrumentor,
)
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from cocktails_embedding_agent.domain import get_otel_options


def initialize_opentelemetry() -> None:
    """Initialize OpenTelemetry tracing and logging for the application."""

    # Make sure toshutdown and gracefully flush the telemetry data on exit
    atexit.register(shutdown_otel)

    otel_options = get_otel_options()

    initialize_otel(
        settings=OTelSettings(
            service_name=otel_options.otel_service_name,
            service_namespace=otel_options.otel_service_namespace,
            otlp_exporter_endpoint=otel_options.otel_exporter_otlp_endpoint,
            otlp_exporter_auth_header=otel_options.otel_otlp_exporter_auth_header,
            service_version=version("cocktails_embedding_agent"),
            environment=os.environ.get("ENV", "unknown"),
            instance_id=socket.gethostname(),
            enable_logging=otel_options.enable_logging,
            enable_tracing=otel_options.enable_tracing,
            enable_console_logging=otel_options.enable_console_logging,
        ),
        configure_tracing=lambda _: (
            ConfluentKafkaInstrumentor().instrument(),
            RequestsInstrumentor().instrument(),
            HTTPXClientInstrumentor().instrument(),
            None,
        )[-1],
    )

    logger = logging.getLogger("initialize_otel")
    logger.info("OpenTelemetry initialized successfully")
