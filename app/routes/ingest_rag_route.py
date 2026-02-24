"""
Routes for RAG data ingestion endpoints.

Implements admin-only access, rate limiting, and cost tracking for file ingestion.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Header
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
def upload_file(
    request: UploadRequest,
    current_user: str = Header(None),
    user_role: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Upload and ingest a file into the RAG system.
    
    This endpoint:
    1. Applies rate limiting (admin-specific)
    2. Verifies admin identity
    3. Logs ingestion metrics to MLflow
    4. Processes file and ingests into vector database
    
    Args:
        request: Upload request with file path and metadata
        current_user: Current user ID
        user_role: Current user role (must be 'admin')
        db: Database session
        
    Returns:
        Dictionary with ingestion status and details
        
    Raises:
        HTTPException: If user is not admin or other validation fails
    """
    # Verify admin identity
    if user_role != "admin":
        logger.warning(f"Unauthorized ingestion attempt by {current_user} (role: {user_role})")
        raise HTTPException(
            status_code=403,
            detail="Only admins can ingest data"
        )
    
    # Apply rate limiting (admin-only endpoint)
    rate_limit(
        user_id=current_user or "anonymous",
        role="admin",
        endpoint="/ingest-rag/upload_file"
    )
    
    try:
        # Log ingestion start to MLflow
        mlflow_run_id = MLflowService.start_run(
            experiment_name=MLflowService.DEFAULT_EXPERIMENT_INGEST,
            run_name=f"ingest_{request.tenant_id}_{__import__('time').time()}",
            tags={
                'tenant_id': request.tenant_id,
                'admin_id': current_user,
                'file_path': request.file_path
            }
        )
        
        import mlflow
        mlflow.log_param("tenant_id", request.tenant_id)
        mlflow.log_param("file_path", request.file_path)
        mlflow.log_param("source", request.source)
        mlflow.log_param("author", request.author)
        
        # Process file
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
            f"Tenant: {request.tenant_id}, File: {request.file_path}"
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