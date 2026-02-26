"""
Routes for RAG data ingestion endpoints.

Implements admin-only access, rate limiting, and cost tracking for file ingestion.
"""
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.rate_limitizer import rate_limit
from app.services.rag_services.path_processing_service import PathProcessingService
from app.services.mlflow_service import MLflowService
from app.schema.upload_request import UploadRequest

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ingest-rag",
)


@router.post("/upload_file")
async def upload_file(
    tenant_id: str = Form(...),
    source: str = Form(...),
    author: str = Form(...),
    file: UploadFile = File(...),
    recursive: bool = Form(False),
    file_extensions: str = Form(None),
    current_user: str = Form(...),
    user_role: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Upload and ingest a file into the RAG system.
    
    This endpoint:
    1. Accepts file upload from browser
    2. Saves uploaded file to server storage
    3. Applies rate limiting (admin-specific)
    4. Verifies admin identity
    5. Logs ingestion metrics to MLflow
    6. Processes file and ingests into vector database
    
    Args:
        tenant_id: Tenant identifier
        source: Source name for tracking
        author: Author name
        file: Uploaded file from browser
        recursive: Whether to process directories recursively
        file_extensions: Comma-separated file extensions to process
        current_user: Current user ID (from form)
        user_role: Current user role (must be 'admin')
        db: Database session
        
    Returns:
        Dictionary with ingestion status and details
        
    Raises:
        HTTPException: If user is not admin or other validation fails
    """
    # Verify admin identity (case-insensitive)
    user_role_lower = (user_role or "").lower().strip()
    if user_role_lower != "admin":
        logger.warning(f"Unauthorized ingestion attempt by {current_user} (role: {user_role}, normalized: {user_role_lower})")
        raise HTTPException(
            status_code=403,
            detail=f"Only admins can ingest data. Your role: {user_role or 'not set'}"
        )
    
    # Apply rate limiting (admin-only endpoint)
    rate_limit(
        user_id=current_user or "anonymous",
        role="admin",
        endpoint="/ingest-rag/upload_file"
    )
    
    try:
        # Create upload directory
        upload_dir = Path("app/files/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        logger.info(f"File uploaded: {file.filename} -> {file_path}")
        
        # Log ingestion start to MLflow
        mlflow_run_id = MLflowService.start_run(
            experiment_name=MLflowService.DEFAULT_EXPERIMENT_INGEST,
            run_name=f"ingest_{tenant_id}_{__import__('time').time()}",
            tags={
                'tenant_id': tenant_id,
                'admin_id': current_user,
                'uploaded_file': file.filename
            }
        )
        
        import mlflow
        mlflow.log_param("tenant_id", tenant_id)
        mlflow.log_param("uploaded_file", file.filename)
        mlflow.log_param("source", source)
        mlflow.log_param("author", author)
        
        # Parse file extensions if provided
        file_ext_list = None
        if file_extensions:
            file_ext_list = [ext.strip() for ext in file_extensions.split(",")]
        
        # Process file
        result = PathProcessingService.process_path(
            self=PathProcessingService(),
            file_path=str(file_path),
            tenant_id=tenant_id,
            source=source,
            author=author,
            db=db,
            recursive=recursive,
            file_extensions=file_ext_list,
        )
        
        # Log success metrics
        mlflow.log_metric("success", 1)
        if isinstance(result, dict) and "details" in result:
            details = result.get("details", {})
            if isinstance(details, dict):
                if "documents_count" in details:
                    mlflow.log_metric("documents_count", details["documents_count"])
                if "chunks_count" in details:
                    mlflow.log_metric("chunks_count", details["chunks_count"])
        
        logger.info(
            f"File ingestion completed - Admin: {current_user}, "
            f"Tenant: {tenant_id}, File: {file.filename}"
        )
        
        return {
            "message": "File processed and ingested successfully",
            "result": result,
            "mlflow_run_id": mlflow_run_id
        }
        
    except PermissionError as e:
        logger.error(f"Permission error during ingestion: {e}")
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        logger.error(f"Validation error during ingestion: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during file ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        MLflowService.end_run(status="FINISHED")