import logging
import os
import sys

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import RESOURCE_ATTRIBUTES, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pythonjsonlogger import jsonlogger


def setup_logging(service_name: str):
    logger = logging.getLogger()
    log_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    logger.setLevel(logging.INFO)

    # Disable propagation for some noisy loggers
    logging.getLogger("uvicorn.access").propagate = False
    return logger


def setup_tracing(service_name: str, otlp_endpoint: str = "http://tempo:4317"):
    resource = Resource.create(
        attributes={RESOURCE_ATTRIBUTES.SERVICE_NAME: service_name}
    )

    provider = TracerProvider(resource=resource)

    if os.getenv("ENABLE_TRACING", "false").lower() == "true":
        processor = BatchSpanProcessor(
            OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        )
        provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)


def instrument_app(app, service_name: str):
    FastAPIInstrumentor.instrument_app(app)
