from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.routes import auth_route, ingest_rag_route, eval_pipline
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

app.include_router(auth_route.router, tags=["Authentication"])
app.include_router(ingest_rag_route.router, tags=["ingest-rag"])
app.include_router(eval_pipline.router, tags=["eval-rag"])