from fastapi import FastAPI
from app.routes import auth,query


app = FastAPI(title="Atlas AI Platform")

app.include_router(auth.router, tags=["Authentication"])
# app.include_router(query.router, prefix="/query", tags=["Query"])