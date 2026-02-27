from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routes import auth_route, ingest_rag_route, eval_pipline, query_route, agent_route

from logging_setup import setup_logging

setup_logging() # Initialize logging For docker logs and Sentry

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

import os

# Initialize Sentry for error tracking
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0
)

# from app.design_pattern.embedded_model import EmbeddedModel

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # load model once
#     app.state.embedding_model = EmbeddedModel()
#     print("Models Loaded Successfully ...")
#     yield
#     print("Models Closed Successfully ...")

# import mlflow

app = FastAPI(
    title="Atlas AI Platform",
    description="A platform for RAG and LLM applications",
    version="1.0.0",
    # lifespan=lifespan
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_route.router, prefix="/api", tags=["Authentication"])
app.include_router(ingest_rag_route.router, prefix="/api", tags=["ingest-rag"])
app.include_router(eval_pipline.router, prefix="/api", tags=["eval-rag"])
app.include_router(query_route.router, prefix="/api", tags=["query"])
app.include_router(agent_route.router, prefix="/api", tags=["agent"])


app.add_middleware(SentryAsgiMiddleware)

# ==================== HEALTH CHECK ENDPOINT ====================

@app.get("/health", tags=["monitoring"])
async def health_check():
    """Health check endpoint for container orchestration and monitoring."""
    return {
        "status": "healthy",
        "service": "Atlas AI Platform",
        "version": "1.0.0"
    }

# ==================== PROMETHEUS & MONITORING ====================

from prometheus_client import Counter, Histogram, REGISTRY
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.monitors import record_resource_metrics
from starlette.middleware.base import BaseHTTPMiddleware
from time import time
import logging

logger = logging.getLogger(__name__)

# Custom HTTP metrics middleware
class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking HTTP request/response metrics."""

    async def dispatch(self, request, call_next):
        start_time = time()
        endpoint = request.url.path

        try:
            response = await call_next(request)
            duration = time() - start_time

            # Record metrics
            from app.core.monitors import (
                http_requests_total,
                http_request_duration_seconds,
                http_response_size_bytes,
            )

            method = request.method
            status = response.status_code

            http_requests_total.labels(
                method=method, endpoint=endpoint, status_code=status
            ).inc()
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
                duration
            )

            if hasattr(response, "body"):
                http_response_size_bytes.labels(method=method, endpoint=endpoint).observe(
                    len(response.body)
                )

            return response

        except Exception as e:
            logger.error(f"Error in metrics middleware: {e}")
            raise


# Add metrics middleware
app.add_middleware(MetricsMiddleware)

# Register the Instrumentator for advanced FastAPI metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics", tags=["monitoring"])

# Background task for recording resource metrics
@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    import asyncio

    async def record_metrics_periodically():
        """Record system metrics every 10 seconds."""
        while True:
            try:
                record_resource_metrics()
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Error recording metrics: {e}")
                await asyncio.sleep(10)

    # Run metrics collection in background
    asyncio.create_task(record_metrics_periodically())
    logger.info("Prometheus monitoring initialized successfully")