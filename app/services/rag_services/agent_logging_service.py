"""
Background task service for Agent logging.

Handles asynchronous logging of agent runs and costs to avoid blocking agent responses.
Records both database logs and Prometheus metrics for monitoring and analytics.
Similar to query_logging_service but for agent-based interactions.
"""
import logging
from celery import shared_task
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.repositories.runs_repository import RunsRepository
from app.repositories.cost_log_repository import CostLogRepository
from app.core.monitors import (
    agent_queries_total,
    agent_reasoning_steps_count,
    agent_reasoning_duration_seconds,
    track_llm_cost,
    llm_tokens_consumed,
    llm_tokens_generated,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def log_agent_run_and_cost(
    self,
    tenant_id: int,
    question: str,
    final_answer: str,
    latency: float,
    step_count: int,
    total_cost: float,
    input_tokens: int,
    output_tokens: int,
    sql_queries: str = "",
    retrieved_docs: str = "",
    model_name: str = "Qwen2.5-1.5B",
):
    """
    Background task to log agent runs and costs to the database.
    
    Also records Prometheus metrics for monitoring and analytics.
    Runs asynchronously to avoid blocking the response stream.
    Retries up to 3 times on failure.
    
    Args:
        tenant_id: Tenant identifier
        question: Original user question
        final_answer: Generated final answer
        latency: Total agent execution time in seconds
        step_count: Number of reasoning steps taken
        total_cost: Total cost accumulated
        input_tokens: Total input tokens used
        output_tokens: Total output tokens used
        sql_queries: Executed SQL queries (comma-separated or JSON)
        retrieved_docs: Retrieved document IDs (comma-separated)
        model_name: LLM model name used
    """
    try:
        # Get a fresh database session for this task
        db = next(get_db())
        
        runs_repo = RunsRepository(db)
        cost_repo = CostLogRepository(db)
        
        # Save run record - include agent-specific metadata in the answer field
        run_metadata = {
            "agent_run": True,
            "step_count": step_count,
            "sql_queries": sql_queries,
            "retrieved_docs": retrieved_docs,
            "answer": final_answer
        }
        
        run = runs_repo.create(
            tenant_id=tenant_id,
            query=question,
            answer=final_answer,
            latency=latency,
            cache_hit=False,  # Agent runs are not cached
            retrieved_docs_ids=retrieved_docs
        )
        
        # Calculate total cost from tokens
        cost_usd = (input_tokens * 0.0000001) + (output_tokens * 0.0000002)
        
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
                f"Logged agent run {run.run_id} - Tenant: {tenant_id}, "
                f"Steps: {step_count}, Tokens: {input_tokens + output_tokens}, Cost: ${cost_usd:.6f}"
            )
        else:
            logger.info(f"Logged agent run {run.run_id} - Tenant: {tenant_id} (no token usage)")
        
        # Record Prometheus metrics for monitoring and analytics
        try:
            # Track agent execution metrics
            agent_queries_total.labels(
                tenant_id=str(tenant_id),
                agent_type="reasoning"
            ).inc()
            
            # Track reasoning steps
            agent_reasoning_steps_count.observe(step_count)
            
            # Track agent latency
            agent_reasoning_duration_seconds.labels(
                agent_type="reasoning"
            ).observe(float(latency))
            
            # Track LLM cost and token usage
            track_llm_cost(
                tenant_id=str(tenant_id),
                model_name=model_name,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
                cost=float(cost_usd)
            )
            
            # Track token consumption
            llm_tokens_consumed.labels(
                tenant_id=str(tenant_id),
                model_name=model_name
            ).inc(int(input_tokens) + int(output_tokens))
            
            llm_tokens_generated.labels(
                tenant_id=str(tenant_id),
                model_name=model_name
            ).inc(int(output_tokens))
            
            logger.debug(f"Recorded Prometheus metrics for agent run {run.run_id}")
        except Exception as metric_error:
            logger.error(f"Error recording Prometheus metrics: {metric_error}")
            # Don't fail the entire task if metrics recording fails
        
        # Clean up database session
        db.close()
        
    except Exception as exc:
        logger.error(f"Error logging agent run and cost: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=min(60 * (2 ** self.request.retries), 600))


def trigger_agent_logging(
    tenant_id: int,
    question: str,
    final_answer: str,
    latency: float,
    step_count: int,
    total_cost: float,
    input_tokens: int,
    output_tokens: int,
    sql_queries: str = "",
    retrieved_docs: str = "",
    model_name: str = "Qwen2.5-1.5B",
) -> None:
    """
    Trigger background logging task for agent without blocking.
    
    This function returns immediately, allowing the response to stream
    while logging happens in the background.
    
    Args:
        tenant_id: Tenant identifier
        question: Original user question
        final_answer: Generated final answer
        latency: Total agent execution time in seconds
        step_count: Number of reasoning steps taken
        total_cost: Total cost accumulated
        input_tokens: Total input tokens used
        output_tokens: Total output tokens used
        sql_queries: Executed SQL queries (comma-separated or JSON)
        retrieved_docs: Retrieved document IDs (comma-separated)
        model_name: LLM model name used
    """
    try:
        # Queue the logging task to run in background
        log_agent_run_and_cost.apply_async(
            args=(
                tenant_id,
                question,
                final_answer,
                latency,
                step_count,
                total_cost,
                input_tokens,
                output_tokens,
                sql_queries,
                retrieved_docs,
                model_name,
            ),
            queue="default",
            routing_key="default",
        )
        logger.debug(f"Queued agent logging task for question: {question[:50]}...")
    except Exception as e:
        logger.error(f"Failed to queue agent logging task: {e}")
        # Log error but don't fail the response
