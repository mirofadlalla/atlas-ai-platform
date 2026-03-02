"""
Background task service for RAG query logging.

Handles asynchronous logging of runs and costs to avoid blocking query responses.
Records both database logs and Prometheus metrics for monitoring and analytics.
"""
import logging
from celery import shared_task
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.repositories.runs_repository import RunsRepository
from app.repositories.cost_log_repository import CostLogRepository
from app.core.monitors import (
    track_llm_cost,
    query_pipeline_duration_seconds,
    llm_tokens_consumed,
    llm_tokens_generated,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def log_query_run_and_cost(
    self,
    tenant_id: int,
    query: str,
    answer: str,
    latency: float,
    cache_hit: bool,
    retrieved_docs_ids: str,
    input_tokens: int,
    output_tokens: float,
    model_name: str = "Qwen2.5-1.5B",
):
    """
    Background task to log query runs and costs to the database.
    
    Also records Prometheus metrics for monitoring and analytics.
    Runs asynchronously to avoid blocking the response stream.
    Retries up to 3 times on failure.
    
    Args:
        tenant_id: Tenant identifier
        query: Original user query
        answer: Generated answer
        latency: Query processing latency in seconds
        cache_hit: Whether response was cached
        retrieved_docs_ids: Comma-separated document IDs used
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens used
        model_name: LLM model name used
    """
    try:
        # Get a fresh database session for this task
        db = next(get_db())
        
        runs_repo = RunsRepository(db)
        cost_repo = CostLogRepository(db)
        
        # Calculate cost
        cost_usd = (input_tokens * 0.0000001) + (output_tokens * 0.0000002)
        
        # Save run record
        run = runs_repo.create(
            tenant_id=tenant_id,
            query=query,
            answer=answer,
            latency=latency,
            cache_hit=cache_hit,
            retrieved_docs_ids=retrieved_docs_ids
        )
        
        # Save cost log if tokens were used
        if input_tokens > 0 or output_tokens > 0:
            cost_repo.create(
                run_id=run.run_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model_name=model_name,
                cost_usd=cost_usd
            )
            logger.info(
                f"Logged run {run.run_id} - Tenant: {tenant_id}, "
                f"Tokens: {input_tokens + output_tokens}, Cost: ${cost_usd:.6f}"
            )
        else:
            logger.info(f"Logged run {run.run_id} - Tenant: {tenant_id} (no token usage)")
        
        # Record Prometheus metrics for monitoring and analytics
        try:
            # Track LLM cost and token usage
            track_llm_cost(
                tenant_id=str(tenant_id),
                model_name=model_name,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
                cost=float(cost_usd)
            )
            
            # Record query pipeline latency
            query_pipeline_duration_seconds.labels(pipeline_stage="total").observe(float(latency))
            
            # Track token consumption
            llm_tokens_consumed.labels(
                tenant_id=str(tenant_id),
                model_name=model_name
            ).inc(int(input_tokens) + int(output_tokens))
            
            llm_tokens_generated.labels(
                tenant_id=str(tenant_id),
                model_name=model_name
            ).inc(int(output_tokens))
            
            logger.debug(f"Recorded Prometheus metrics for run {run.run_id}")
        except Exception as metric_error:
            logger.error(f"Error recording Prometheus metrics: {metric_error}")
            # Don't fail the entire task if metrics recording fails
        
        # Clean up database session
        db.close()
        
    except Exception as exc:
        logger.error(f"Error logging query run and cost: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=min(60 * (2 ** self.request.retries), 600))


def trigger_query_logging(
    tenant_id: int,
    query: str,
    answer: str,
    latency: float,
    cache_hit: bool,
    retrieved_docs_ids: str,
    input_tokens: int,
    output_tokens: float,
    model_name: str = "Qwen2.5-1.5B",
) -> None:
    """
    Trigger background logging task without blocking.
    
    This function returns immediately, allowing the response to stream
    while logging happens in the background.
    
    Args:
        tenant_id: Tenant identifier
        query: Original user query
        answer: Generated answer
        latency: Query processing latency in seconds
        cache_hit: Whether response was cached
        retrieved_docs_ids: Comma-separated document IDs used
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens used
        model_name: LLM model name used
    """
    try:
        # Queue the logging task to run in background
        log_query_run_and_cost.apply_async(
            args=(
                tenant_id,
                query,
                answer,
                latency,
                cache_hit,
                retrieved_docs_ids,
                input_tokens,
                output_tokens,
                model_name,
            ),
            queue="default",
            routing_key="default",
        )
        logger.debug(f"Queued logging task for query: {query[:50]}...")
    except Exception as e:
        logger.error(f"Failed to queue logging task: {e}")
        # Log error but don't fail the response
