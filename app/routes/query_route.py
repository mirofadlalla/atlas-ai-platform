"""
Routes for RAG query/answer endpoints.

Implements query processing with streaming responses, rate limiting, and cost tracking.
"""
import logging
import time
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.rate_limitizer import rate_limit
from app.schema.query_request import QueryRequest
from app.rag.retrivel_data_pipline import RetrievalPipeline
from app.services.mlflow_service import MLflowService
from app.repositories.runs_repository import RunsRepository
from app.repositories.cost_log_repository import CostLogRepository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/query",
)


@router.post("/ask")
async def ask_question(
    request: QueryRequest,
    current_user: str = Header(None),
    tenant_id: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Answer a user question using the RAG pipeline with streaming response.
    
    This endpoint:
    1. Applies rate limiting based on user role
    2. Logs query metrics to MLflow
    3. Generates answer using RetrievalPipeline
    4. Tracks latency and costs
    5. Saves run and cost information to database
    
    Args:
        request: QueryRequest with user query
        current_user: Current user ID
        tenant_id: Tenant identifier
        db: Database session
        
    Returns:
        StreamingResponse with answer chunks
        
    Raises:
        HTTPException: If query processing fails
    """
    # Apply rate limiting (user gets standard limit)
    rate_limit(
        user_id=current_user or "anonymous",
        role="user",
        endpoint="/query/ask"
    )
    
    try:
        # Start MLflow run for this query
        mlflow_run_id = MLflowService.start_run(
            experiment_name=MLflowService.DEFAULT_EXPERIMENT_QUERY,
            run_name=f"query_{tenant_id}_{time.time()}",
            tags={
                'tenant_id': tenant_id,
                'user_id': current_user or 'anonymous',
                'endpoint': '/query/ask'
            }
        )
        
        # Log query parameters
        import mlflow
        mlflow.log_param("tenant_id", tenant_id)
        mlflow.log_param("query_length", len(request.query))
        mlflow.log_param("user_id", current_user or "anonymous")
        
        # Create pipeline for this tenant
        pipeline = RetrievalPipeline(tenant_id=tenant_id)
        
        # Start timing
        start_time = time.time()
        
        # Initialize repositories for logging
        runs_repo = RunsRepository(db)
        cost_repo = CostLogRepository(db)
        
        async def answer_generator():
            """
            Generator that yields answer chunks and logs metrics after completion.
            """
            full_answer = ""
            latency = 0
            cost_usd = 0.0
            input_tokens = 0
            output_tokens = 0
            cache_hit = False
            
            try:
                # Stream answer
                for chunk in pipeline.ask_stream(query=request.query):
                    full_answer += chunk
                    yield chunk
                
                # Calculate metrics
                latency = time.time() - start_time
                
                # Get token usage from the LLM (if available)
                try:
                    from app.services.llm_runner import CustomLocalLLM
                    usage = CustomLocalLLM.last_usage or {}
                    input_tokens = usage.get("input", 0)
                    output_tokens = usage.get("output", 0)
                    
                    # Calculate cost based on token usage
                    # Example pricing for Qwen 2.5 1.5B (adjust based on actual pricing)
                    cost_usd = (input_tokens * 0.0000001) + (output_tokens * 0.0000002)
                except:
                    pass
                
                # Save run to database
                run = runs_repo.create(
                    tenant_id=tenant_id,
                    query=request.query,
                    answer=full_answer[:1000],  # Store first 1000 chars in DB
                    latency=latency,
                    cache_hit=cache_hit,
                    retrieved_docs_ids=""
                )
                
                # Save cost log if there are tokens
                if input_tokens > 0 or output_tokens > 0:
                    cost_repo.create(
                        run_id=run.run_id,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        model_name="Local-LLM",
                        cost_usd=cost_usd
                    )
                
                # Log metrics to MLflow
                mlflow.log_metric("latency_seconds", latency)
                mlflow.log_metric("cost_usd", cost_usd)
                mlflow.log_metric("input_tokens", input_tokens)
                mlflow.log_metric("output_tokens", output_tokens)
                mlflow.log_metric("answer_length", len(full_answer))
                
                logger.info(
                    f"Query completed - Tenant: {tenant_id}, User: {current_user}, "
                    f"Latency: {latency:.2f}s, Cost: ${cost_usd:.6f}, Run ID: {run.run_id}"
                )
                
            except Exception as e:
                logger.error(f"Error during query streaming: {e}")
                yield f"\n\nError: {str(e)}"
            
            finally:
                # End MLflow run
                MLflowService.end_run(status="FINISHED")
        
        return StreamingResponse(answer_generator(), media_type="text/plain")
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieve")
async def retrieve_documents(
    request: QueryRequest,
    current_user: str = Header(None),
    tenant_id: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Retrieve relevant documents for a query without generating an answer.
    
    This endpoint:
    1. Applies rate limiting
    2. Retrieves relevant documents from the vector database
    3. Returns document metadata and content
    
    Args:
        request: QueryRequest with user query
        current_user: Current user ID
        tenant_id: Tenant identifier
        db: Database session
        
    Returns:
        List of retrieved documents with relevance scores
    """
    # Apply rate limiting
    rate_limit(
        user_id=current_user or "anonymous",
        role="user",
        endpoint="/query/retrieve"
    )
    
    try:
        # Create pipeline for this tenant
        pipeline = RetrievalPipeline(tenant_id=tenant_id)
        
        # Retrieve documents
        documents = pipeline.retrieve(query=request.query)
        
        # Format response
        doc_results = []
        for doc in documents:
            doc_results.append({
                "id": doc.metadata.get("_id", ""),
                "content": doc.page_content[:500],  # First 500 chars
                "metadata": doc.metadata,
                "source": doc.metadata.get("source", "unknown")
            })
        
        logger.info(
            f"Documents retrieved - Tenant: {tenant_id}, Query: {request.query[:50]}, "
            f"Documents found: {len(doc_results)}"
        )
        
        return {
            "query": request.query,
            "documents_count": len(doc_results),
            "documents": doc_results
        }
        
    except Exception as e:
        logger.error(f"Error retrieving documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))
