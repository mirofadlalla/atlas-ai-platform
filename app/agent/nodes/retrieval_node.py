from app.rag.steps.retriever import get_retriever
from app.agent.core.state import AgentState
import logging

logger = logging.getLogger(__name__)

def retrieval_node(state: AgentState):
    """
    Node responsible for retrieving context from the vector database.
    
    Args:
        state: The current agent state
        
    Returns:
        dict: Updated state with retrieval_context and observation
    """
    try:
        retriever = get_retriever(state["tenant_id"])
        docs = retriever.invoke(state["question"])
        
        if docs:
            # Format results with document metadata
            formatted_docs = []
            for i, doc in enumerate(docs, 1):
                content = doc.page_content[:300]
                metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                formatted_docs.append(f"{i}. {content}...")
            
            context = "\n".join(formatted_docs)
            observation = f"Retrieved {len(docs)} relevant document(s) from knowledge base:\n{context}"
        else:
            context = ""
            observation = "No relevant documents found in knowledge base."
        
        return {
            "retrieval_context": context,
            "observation": observation,
            "observation_history": state.get("observation_history", []) + [observation],
            "thoughtz": state.get("thoughtz", []) + [f"Retrieved {len(docs)} document(s)"]
        }
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        error_obs = f"Error during retrieval: {str(e)}"
        return {
            "retrieval_context": "",
            "observation": error_obs,
            "observation_history": state.get("observation_history", []) + [error_obs]
        }