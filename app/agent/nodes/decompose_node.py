from app.services.llm_runner import call_llama
from app.agent.core.state import AgentState
from app.agent.nodes.thought_node import extract_first_json_block
import json
import logging

logger = logging.getLogger(__name__)

def decompose_node(state: AgentState):
    """
    Analyzes the user's question to determine if it is a compound question.
    If it is, decomposes it into multiple sub-questions.
    If not, keeps it as a single question.
    
    Args:
        state: The current agent state
        
    Returns:
        dict: Updated state with decomposed questions and initialized index
    """
    question = state.get("question", "")
    tenant_id = state.get("tenant_id")
    
    prompt = f"""You are an AI planner for an Enterprise RAG and Database system.
Your job is to analyze a user's question and determine if it is a compound question that needs to be decomposed into multiple sub-questions to be answered accurately.

A compound question usually asks for two or more distinct pieces of information that might require different operational tools (like querying a database for numbers, AND retrieving documents for explanations).

Example 1 (Compound): "How many users do we have and what is the RAG architecture?"
Output:
{{
    "is_compound": true,
    "sub_questions": [
        "How many users do we have?",
        "What is the RAG architecture?"
    ]
}}

Example 2 (Simple): "What was our revenue last quarter?"
Output:
{{
    "is_compound": false,
    "sub_questions": [
        "What was our revenue last quarter?"
    ]
}}

Analyze this question:
"{question}"

Return ONLY a valid JSON object matching the format above. Do not include markdown blocks or any other text.
"""
    try:
        response_dict = call_llama(prompt)
        response_text = response_dict['content']
        
        # Parse the JSON response
        json_text = extract_first_json_block(response_text)
        
        parsed = json.loads(json_text)
        sub_questions = parsed.get("sub_questions", [question])
        
        # Ensure we always have at least the original question
        if not sub_questions:
            sub_questions = [question]
            
        print(f"[DECOMPOSE] Question broken down into {len(sub_questions)} part(s).")
        logger.info(f"Decomposed question into {len(sub_questions)} parts: {sub_questions}")
        
    except Exception as e:
        logger.error(f"Error in decompose node: {e}")
        # Fallback to just the original question
        sub_questions = [question]
        print(f"[DECOMPOSE] Error during decomposition, falling back to original question.")

    return {
        "original_question": question,
        "sub_questions": sub_questions,
        "current_sub_question_index": 0,
        "sub_answers": [],
        "observation_history": state.get("observation_history", []) + [f"Decomposed into {len(sub_questions)} sub-questions: {sub_questions}"]
    }
