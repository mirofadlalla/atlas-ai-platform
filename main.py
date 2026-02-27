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

from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

# Create a Prometheus counter for tracking the number of requests
request_count = Counter("fastapi_requests_total", "Total number of requests")

# Create a Prometheus histogram for tracking request duration
request_duration = Histogram("fastapi_request_duration_seconds", "Request duration in seconds")

# Initialize the Prometheus instrumentator

# Register the instrumentator with the FastAPI app
Instrumentator().instrument(app)