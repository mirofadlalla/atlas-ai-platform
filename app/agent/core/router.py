def route_action(state):
    """
    Routes to the next node based on the agent's decision and conversation state.
    Enforces data gathering before allowing to finish, but prevents infinite retries.
    
    Args:
        state: The current agent state
        
    Returns:
        str: The next node to execute ('sql', 'retrieval', or 'finish')
    """
    # Get the agent's decision
    last_action = state.get("last_action", "finish")
    
    # Check what data has been gathered
    has_sql_data = bool(state.get("sql_result") or state.get("last_sql"))
    has_retrieval_data = bool(state.get("retrieval_context"))
    
    # Track which actions have been attempted (even if they failed)
    observation_history = state.get("observation_history", [])
    sql_attempted_flag = state.get("sql_attempted", False)
    has_attempted_sql = sql_attempted_flag or any("SQL" in obs or "[DATABASE]" in obs for obs in observation_history)
    has_attempted_retrieval = any("Retrieved" in obs or "retrieval" in obs.lower() or "Retrieval error" in obs for obs in observation_history)
    
    has_no_data = not (has_sql_data or has_retrieval_data)
    
    # Check if question seems to need data
    question = state.get("question", "").lower()
    needs_data_keywords = [
        'how many', 'count', 'total', 'average', 'sum', 'number', 
        'revenue', 'sales', 'users', 'products', 'reports', 'stats',
        'statistics', 'data', 'results', 'list', 'show', 'find'
    ]
    question_needs_data = any(kw in question for kw in needs_data_keywords)
    
    # Step limit (prevent infinite loops)
    max_steps = 10
    step_count = state.get("step_count", 0)
    if step_count >= max_steps:
        print(f"Router: Reached max steps ({max_steps}), finishing")
        return "finish"
    
    # Validate action value
    if last_action not in ["sql", "retrieval", "finish"]:
        last_action = "finish"
    
    # PREVENT INFINITE RETRY: If last action failed (attempted but no data), try alternative or finish
    if last_action == "retrieval" and has_attempted_retrieval and not has_retrieval_data:
        print(f"Router: Retrieval attempted but failed/no data, moving to finish")
        return "finish"
    
    if last_action == "sql" and has_attempted_sql and not has_sql_data:
        print(f"Router: SQL attempted but failed/no data, trying retrieval if not attempted")
        if not has_attempted_retrieval:
            return "retrieval"
        return "finish"
    
    # If agent wants to finish but hasn't gathered data and question needs it, force data gathering
    if last_action == "finish" and has_no_data and question_needs_data:
        print(f"Router: Question needs data but none gathered, forcing data gathering")
        # Prefer SQL for data questions
        if any(kw in question for kw in ['how many', 'count', 'total', 'revenue', 'stats']):
            if not has_attempted_sql:
                print(f"Router: Routing to SQL (not yet attempted)")
                return "sql"
            elif not has_attempted_retrieval:
                print(f"Router: SQL attempted, trying retrieval")
                return "retrieval"
        else:
            if not has_attempted_retrieval:
                print(f"Router: Routing to retrieval (not yet attempted)")
                return "retrieval"
            elif not has_attempted_sql:
                print(f"Router: Retrieval attempted, trying SQL")
                return "sql"
    
    print(f"Router: Returning agent decision: {last_action}")
    return last_action