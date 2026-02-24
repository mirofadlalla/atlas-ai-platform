from fastapi import APIRouter, Depends

from app.core.db import get_db
from sqlalchemy.orm import Session
# from app.rag.ingest_data_pipline import RAGPipeline

from app.services.rag_services.path_processing_service import PathProcessingService

from app.design_pattern.upload_factory import process_upload

from app.schema.upload_request import UploadRequest

router = APIRouter(
    prefix="/ingest-rag",
)

# endpoint to trigger file ingestion
# @router.get("/upload_file")
# def upload_file(file_path: str, tenant_id: str, source: str, author: str, db: Session = Depends(get_db) ):
#     result = process_upload(file_path=file_path, tenant_id=tenant_id, source=source, author=author, db=db)
#     return {"message": "File processed and ingested successfully", "result": result}

# new endpoint to trigger file ingestion with factory pattern
@router.post("/upload_file")
def upload_file(
    request: UploadRequest,
    db: Session = Depends(get_db)
):
    result = PathProcessingService.process_path(
        self=PathProcessingService(),
        file_path=request.file_path,
        tenant_id=request.tenant_id,
        source=request.source,
        author=request.author,
        db=db,
        recursive=request.recursive,
        file_extensions=request.file_extensions,
    )

    return {
        "message": "File processed and ingested successfully",
        "result": result
    }