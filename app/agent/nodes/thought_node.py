
from app.agent.schemas import ActionDecision, format_instructions
from app.services.llm_runner import call_llama
from app.agent.core.state import AgentState
from langchain_core.output_parsers import JsonOutputParser
import json
import re

def extract_first_json_block(text: str) -> str:
    """
    Extract the first valid JSON object from text that may contain multiple JSON blocks.
    Handles markdown code blocks and multiple concatenated JSON responses.
    
    Args:
        text: Raw text that may contain JSON blocks
        
    Returns:
        str: First valid JSON string
    """
    # Remove markdown code block markers
    text = text.strip()
    
    # Try to find JSON blocks wrapped in ``` markers
    code_block_pattern = r'```(?:json)?\s*([\s\S]*?)```'
    code_blocks = re.findall(code_block_pattern, text)
    
    if code_blocks:
        # Use the first code block found
        text = code_blocks[0].strip()
    
    # If there are multiple JSON objects concatenated, extract just the first one
    # This handles cases like: {"action":"sql"}{"action":"sql"} -> get just the first
    brace_count = 0
    first_json = []
    in_string = False
    escape_next = False
    
    for i, char in enumerate(text):
        if escape_next:
            first_json.append(char)
            escape_next = False
            continue
            
        if char == '\\' and in_string:
            escape_next = True
            first_json.append(char)
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
            
        first_json.append(char)
        
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and i < len(text) - 1:
                    # Found the end of first JSON object
                    return ''.join(first_json).strip()
    
    return ''.join(first_json).strip()


def thought_node(state: AgentState):
    """
    Node responsible for generating the agent's thought process and deciding the next action.
    Decomposes complex questions into steps and decides whether to use SQL, retrieval, or finish.
    
    Args:
        state: The current agent state
        
    Returns:
        dict: Updated state with thought, last_action, and incremented step_count
    """
    # Track what actions have been taken
    has_queried_sql = bool(state.get('last_sql'))
    has_retrieved_docs = bool(state.get('retrieval_context'))
    
    # Build context of what's been done
    actions_taken = []
    if has_queried_sql:
        actions_taken.append("SQL database query executed")
    if has_retrieved_docs:
        actions_taken.append("Document retrieval completed")
    
    actions_context = "\n".join(f"- {a}" for a in actions_taken) if actions_taken else "None yet"
    
    # Use intelligent classification instead of fixed keyword lists
    question_lower = state['question'].lower()
    
    # Get question classification from helper function
    question_type = _classify_question_type(state['question'])
    
    # Build more specific guidance based on question type
    if question_type == "data":
        action_guidance = "This question asks for QUANTITATIVE DATA (numbers, counts, statistics). Use SQL query to get actual data from the database."
    elif question_type == "knowledge":
        action_guidance = "This question asks for KNOWLEDGE/INFORMATION/EXPLANATIONS. Use RETRIEVAL to search knowledge base documents and get explanations."
    else:
        action_guidance = "Analyze the question to determine if it needs DATA (SQL) or KNOWLEDGE (RETRIEVAL)."
    
    # Build prompt for better decision making
    prompt = f"""You are an AI Agent for an Enterprise RAG system. Respond with ONLY one JSON object, no markdown, no extra text.

CURRENT QUESTION: {state['question']}
Current Step: {state['step_count']} / 10

{action_guidance}

QUESTION CATEGORIES:
- QUANTITATIVE DATA: How many? Count? Total? Revenue? Stats? → Use 'sql'
- KNOWLEDGE/INFORMATION: What is? Explain? Information? Definitions? → Use 'retrieval'
- ANSWERABLE: You have enough information → Use 'finish'

PREVIOUS DATA GATHERED:
{actions_context}

CRITICAL: 
1. Output ONLY valid JSON, no markdown code blocks
2. Do NOT repeat yourself
3. Do NOT output multiple JSON blocks
4. Choose the CORRECT action type based on question category
5. If question needs data but havent got it yet, choose 'sql' or 'retrieval'

Output exactly one JSON object with no extra text:
{format_instructions}"""
    
    response_dict = call_llama(prompt)
    response_text = response_dict['content']
    
    # Determine action with improved parsing
    next_action = _parse_action_decision(response_text, state, question_lower)
    
    return {
        "thought": response_text,
        "last_action": next_action,
        "step_count": state['step_count'] + 1,
        "thoughts": state.get('thoughts', []) + [response_text],
        "observation_history": state.get('observation_history', []) + [f"Thought step {state['step_count'] + 1}: Decision = {next_action}"]
    }


def _parse_action_decision(response_text: str, state: AgentState, question_lower: str) -> str:
    """
    Parse LLM response to extract action decision. Handles multiple JSON blocks and malformed responses.
    Uses JsonOutputParser for robust parsing.
    
    Args:
        response_text: Raw LLM response
        state: Agent state for context
        question_lower: Lowercased question for keyword analysis
        
    Returns:
        str: The action to take ('sql', 'retrieval', or 'finish')
    """
    try:
        # Extract first JSON block from potentially multi-block response
        json_text = extract_first_json_block(response_text)
        
        # Parse using JsonOutputParser for robustness
        parser = JsonOutputParser(pydantic_object=ActionDecision)
        action_decision = ActionDecision.model_validate_json(json_text)
        next_action = action_decision.action.lower().strip()
        
        # Validate action is one of allowed values
        if next_action not in ['sql', 'retrieval', 'finish']:
            next_action = 'finish'
            
    except Exception as e:
        print(f"Error parsing action decision: {e}, Response: {response_text[:200]}")
        # Fallback: use keyword detection
        next_action = _fallback_action_detection(question_lower, state)
    
    # Apply safety overrides using intelligent classification
    has_queried_sql = bool(state.get('last_sql'))
    has_retrieved_docs = bool(state.get('retrieval_context'))
    
    question_type = _classify_question_type(question_lower)
    
    # Override: if question clearly needs data but tries to finish without data, force appropriate action
    if next_action == 'finish' and not has_queried_sql and not has_retrieved_docs:
        if question_type == 'data':
            next_action = 'sql'
            print(f"Override: Forcing SQL for data question: '{question_lower[:50]}...'")
        elif question_type == 'knowledge':
            next_action = 'retrieval'
            print(f"Override: Forcing RETRIEVAL for knowledge question: '{question_lower[:50]}...'")
    
    return next_action


def _fallback_action_detection(question_lower: str, state: AgentState) -> str:
    """
    Fallback action detection when JSON parsing fails.
    Uses intelligent question classification instead of keyword matching.
    
    Args:
        question_lower: Lowercased question
        state: Agent state
        
    Returns:
        str: The action to take
    """
    has_queried_sql = bool(state.get('last_sql'))
    has_retrieved_docs = bool(state.get('retrieval_context'))
    
    # Classify question type intelligently
    question_type = _classify_question_type(question_lower)
    
    # Route based on question type
    if question_type == 'data' and not has_queried_sql:
        return 'sql'
    elif question_type == 'knowledge' and not has_retrieved_docs:
        return 'retrieval'
    
    # Default to finish if we've tried data gathering
    return 'finish'


def _classify_question_type(question: str) -> str:
    """
    Intelligently classify a question as 'data', 'knowledge', or 'mixed'.
    Uses linguistic patterns to determine if question seeks:
    - DATA: numbers, counts, statistics, specific values from database
    - KNOWLEDGE: explanations, definitions, information, concepts, how-tos
    
    Args:
        question: The user's question
        
    Returns:
        str: 'data', 'knowledge', or 'mixed'
    """
    question_lower = question.lower().strip()
    
    # Quantitative/Data indicators - asking for specific numbers or measurements
    data_patterns = [
        'how many', 'how much', 'count', 'total', 'sum', 'average', 'what % of',
        'what is the total', 'what is the count', 'how many registered',
        'number of', 'amount of', 'statistics', 'report', 'revenue', 'sales',
        'percentage of', 'breakdown of', 'distribution of'
    ]
    
    # Knowledge/Conceptual indicators - asking for explanations or information
    knowledge_patterns = [
        'what is', 'what are', 'explain', 'describe', 'definition', 'tell me about',
        'how does', 'how to', 'why', 'information about', 'what does', 'list the',
        'get me', 'show me', 'give me', 'provide', 'import', 'architecture',
        'structure', 'benefit', 'advantage', 'feature', 'capability', 'improve'
    ]
    
    # Count matches for each pattern
    data_matches = sum(1 for pattern in data_patterns if pattern in question_lower)
    knowledge_matches = sum(1 for pattern in knowledge_patterns if pattern in question_lower)
    
    # Simple decision logic
    if data_matches > knowledge_matches and data_matches > 0:
        return 'data'
    elif knowledge_matches > data_matches and knowledge_matches > 0:
        return 'knowledge'
    
    # If unclear, use question length heuristic
    # Longer questions asking for explanation tend to be knowledge questions
    if len(question) > 50 and any(word in question_lower.split() for word in ['explain', 'what', 'how']):
        return 'knowledge'
    
    # Default: if it looks like asking for specific values/counts
    if any(pattern in question_lower for pattern in ['how many', 'count', 'total', 'number']):
        return 'data'
    
    # Otherwise default to knowledge (better to return docs than wrong query)
    return 'knowledge'
