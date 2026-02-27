import json
import logging
import time
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.agent.core.graph import agent_app
from app.agent.core.state import AgentState
from app.services.rag_services.agent_logging_service import trigger_agent_logging
from app.services.auth_services.auth_service import get_current_user
from app.core.db import get_db

router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger(__name__)

class AgentRequest(BaseModel):
    """Request model for agent endpoints"""
    question: str

@router.post("/ask-agent")
async def ask_agent(
    request: AgentRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stream agent responses for a question specific to a tenant.
    
    This endpoint processes a question through an agent that can:
    1. Think about the question and decide on a strategy
    2. Execute SQL queries to retrieve structured data
    3. Retrieve relevant documents from the knowledge base
    4. Synthesize a final answer from all gathered information
    
    Automatically logs runs and costs to the database after execution.
    
    Args:
        request: AgentRequest object containing question and tenant_id
        
    Yields:
        Server-Sent Events (SSE) with the following types:
        - thought: Agent's reasoning about what to do next
        - tool_start: Notification that a tool (SQL/retrieval) is about to run
        - tool_end: Notification that a tool execution completed
        - answer: The final synthesized answer
    """
    
    async def event_generator():
        """
        Generator that yields SSE events as the agent processes the question.
        Tracks metrics and logs execution after completion.
        """
        start_time = time.time()
        final_result = None
        input_tokens = 0
        output_tokens = 0
        
        # Initialize the graph state with user inputs and defaults
        inputs: AgentState = {
            "question": request.question, 
            "tenant_id": current_user.tenant_id,
            "thoughts": [],
            "observation_history": [],
            "step_count": 0,
            "total_cost": 0.0,
            "thought": None,
            "last_action": None,
            "observation": None,
            "last_sql": None,
            "retrieval_context": None,
            "sql_result": None,
            "final_answer": None
        }

        try:
            # Stream events from the agent graph execution
            async for event in agent_app.astream_events(inputs, version="v2"):
                event_type = event.get("event", "")
                event_name = event.get("name", "")
                
                # Handle node execution start/end events
                if event_type == "on_chain_start":
                    if event_name == "thought":
                        yield f"data: {json.dumps({'type': 'tool_start', 'tool': 'Thinking', 'name': event_name})}\n\n"
                    elif event_name == "sql_tool":
                        yield f"data: {json.dumps({'type': 'tool_start', 'tool': 'SQL Query', 'name': event_name})}\n\n"
                    elif event_name == "retrieval_tool":
                        yield f"data: {json.dumps({'type': 'tool_start', 'tool': 'Document Retrieval', 'name': event_name})}\n\n"
                
                # Handle node execution completion
                elif event_type == "on_chain_end":
                    data = event.get("data", {})
                    output = data.get("output", {})
                    
                    # Stream thoughts from thought node
                    if event_name == "think" and "thought" in output:
                        thought_content = output.get("thought", "")
                        if thought_content:
                            yield f"data: {json.dumps({'type': 'thought', 'content': thought_content})}\n\n"
                    
                    # Stream final answer from finish node and capture result
                    elif event_name == "finish" and "final_answer" in output:
                        final_answer = output.get("final_answer", "")
                        if final_answer:
                            yield f"data: {json.dumps({'type': 'answer', 'content': final_answer})}\n\n"
                            yield f"data: {json.dumps({'type': 'complete', 'final_answer': final_answer})}\n\n"
                            # Store the final result for logging
                            final_result = output
                    
                    # Node completion signals
                    elif event_name in ["sql_tool", "retrieval_tool", "think"]:
                        node_display = {
                            "sql_tool": "SQL Query",
                            "retrieval_tool": "Document Retrieval", 
                            "think": "Thinking"
                        }.get(event_name, event_name)
                        yield f"data: {json.dumps({'type': 'tool_end', 'tool': node_display})}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'done', 'status': 'success'})}\n\n"
            
            # Calculate latency
            latency = time.time() - start_time
            
            # Log the agent run and cost asynchronously
            if final_result:
                try:
                    sql_queries = final_result.get("last_sql", "")
                    retrieved_docs = final_result.get("retrieval_context", "")
                    
                    trigger_agent_logging(
                        tenant_id=current_user.tenant_id,
                        question=request.question,
                        final_answer=final_result.get("final_answer", ""),
                        latency=latency,
                        step_count=final_result.get("step_count", 0),
                        total_cost=final_result.get("total_cost", 0.0),
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        sql_queries=sql_queries if sql_queries else "",
                        retrieved_docs=retrieved_docs[:200] if retrieved_docs else "",
                        model_name="Qwen2.5-1.5B"
                    )
                    logger.debug(f"Triggered logging for agent run - Latency: {latency:.2f}s")
                except Exception as log_error:
                    logger.error(f"Error triggering agent logging: {log_error}")
            
        except Exception as e:
            logger.error(f"Error during agent execution: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/ask-agent-batch")
async def ask_agent_batch(
    request: AgentRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Non-streaming endpoint that returns the full agent response.
    
    Automatically logs runs and costs to the database after execution.
    
    Args:
        request: AgentRequest object containing question
        
    Returns:
        dict: Complete agent response including thoughts, actions, and final answer
    """
    start_time = time.time()
    
    inputs: AgentState = {
        "question": request.question, 
        "tenant_id": current_user.tenant_id,
        "thoughts": [],
        "observation_history": [],
        "step_count": 0,
        "total_cost": 0.0,
        "thought": None,
        "last_action": None,
        "observation": None,
        "last_sql": None,
        "retrieval_context": None,
        "sql_result": None,
        "final_answer": None
    }
    
    try:
        result = await agent_app.ainvoke(inputs)
        
        # Calculate latency
        latency = time.time() - start_time
        
        # Log the agent run and cost asynchronously
        try:
            sql_queries = result.get("last_sql", "")
            retrieved_docs = result.get("retrieval_context", "")
            
            trigger_agent_logging(
                tenant_id=current_user.tenant_id,
                question=request.question,
                final_answer=result.get("final_answer", ""),
                latency=latency,
                step_count=result.get("step_count", 0),
                total_cost=result.get("total_cost", 0.0),
                input_tokens=0,
                output_tokens=0,
                sql_queries=sql_queries if sql_queries else "",
                retrieved_docs=retrieved_docs[:200] if retrieved_docs else "",
                model_name="Qwen2.5-1.5B"
            )
            logger.debug(f"Triggered logging for agent batch run - Latency: {latency:.2f}s")
        except Exception as log_error:
            logger.error(f"Error triggering agent logging: {log_error}")
        
        return {
            "success": True,
            "question": request.question,
            "final_answer": result.get("final_answer"),
            "thoughts": result.get("thoughts", []),
            "step_count": result.get("step_count", 0),
            "total_cost": result.get("total_cost", 0.0),
            "sql_queries": [result.get("last_sql")] if result.get("last_sql") else [],
            "retrieved_context": result.get("retrieval_context", "")
        }
    except Exception as e:
        logger.error(f"Error during agent batch execution: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
