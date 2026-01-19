import logging
import os
import sys
from pythonjsonlogger import jsonlogger

def setup_logging(service_name: str):
    logger = logging.getLogger()
    # Check if handlers already exist to avoid duplicates
    if not logger.handlers:
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
    if os.getenv("ENABLE_TRACING", "false").lower() != "true":
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        try:
            from opentelemetry.semconv.resource import ResourceAttributes
            SERVICE_NAME = ResourceAttributes.SERVICE_NAME
        except ImportError:
            # Fallback for different versions
            SERVICE_NAME = "service.name"

        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create(
            attributes={SERVICE_NAME: service_name}
        )

        provider = TracerProvider(resource=resource)
        processor = BatchSpanProcessor(
            OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        )
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
    except Exception as e:
        logging.getLogger().warning(f"Failed to setup tracing: {e}")

def instrument_app(app, service_name: str):
    if os.getenv("ENABLE_TRACING", "false").lower() != "true":
        return

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
    except Exception as e:
        logging.getLogger().warning(f"Failed to instrument app: {e}")
