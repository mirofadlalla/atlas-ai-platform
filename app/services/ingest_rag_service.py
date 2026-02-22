# app/services/ingest_rag_service.py
from app.celery.celery_config import celery_app
from app.core.db import get_db_session


# Celery task for ingesting RAG data
@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
    time_limit=600,
    soft_time_limit=550
)
def ingest_file_task(self, file_path: str, tenant_id: int, source: str, author: str):
    """
    Async task to ingest files into RAG pipeline.
    Imports RAGPipeline here to avoid loading heavy dependencies during worker startup.
    """
    try:
        db = get_db_session()  # Get a new database session for this task
        from app.rag.ingest_data_pipline import RAGPipeline
        
        # Prepare custom metadata for the RAG pipeline
        custom_metadata = {
            "tenant_id": tenant_id,
            "source": source,
            "author": author
        }
        return RAGPipeline.process_file(file_path=file_path, custom_metadata=custom_metadata,db=db)
    except MemoryError:
        self.retry(countdown=60, exc=MemoryError("Not enough memory to process file"), max_retries=3)
    except Exception as exc:
        self.retry(countdown=10, exc=exc)
