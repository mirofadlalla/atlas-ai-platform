from app.services.llm_runner import call_llama
from app.agent.core.state import AgentState
import logging

logger = logging.getLogger(__name__)

def finish_node(state: AgentState):
    """
    Node responsible for generating the final answer based on gathered information.
    Uses SQL results, retrieved documents, and observations to provide a comprehensive answer.
    
    PRIORITY RULE: If question asked for database data, ONLY use SQL results (not document fallback)
    
    Args:
        state: The current agent state with question, observations, and retrieval context
        
    Returns:
        dict: Updated state with final_answer
    """
    try:
        # Check question type - does it ask for database data?
        question_lower = state.get('question', '').lower()
        sql_keywords = ['how many', 'count', 'total', 'average', 'sum', 'number of', 'revenue', 'database']
        asks_for_db_data = any(kw in question_lower for kw in sql_keywords)
        
        # Check what data sources are available
        has_sql_results = state.get('sql_has_results', False)
        has_sql_attempt = state.get('sql_attempted', False)
        has_retrieval = bool(state.get('retrieval_context'))
        
        print(f"[FINISH] Question asks for DB data: {asks_for_db_data}, SQL attempted: {has_sql_attempt}, SQL has results: {has_sql_results}")
        
        # Prepare data summary for the final answer
        data_summary = []
        data_sources_used = []
        
        # RULE: If question asks for database data and we attempted SQL, ONLY use SQL (no document fallback)
        if asks_for_db_data and has_sql_attempt:
            if has_sql_results and state.get('sql_result'):
                data_summary.append(f"=== DATABASE QUERY RESULTS ===\n{state.get('sql_result', 'No results')}")
                data_sources_used.append("DATABASE")
            else:
                # SQL was attempted but found no data - report this instead of using documents
                data_summary.append("=== DATABASE QUERY RESULTS ===\nNo matching records found in database")
                data_sources_used.append("DATABASE (no results)")
                print(f"[FINISH] ALERT: Question asks for database data but SQL returned no results. NOT using documents as fallback.")
        else:
            # For general questions, use both SQL and retrieval data
            if state.get('sql_result'):
                data_summary.append(f"=== DATABASE QUERY RESULTS ===\n{state.get('sql_result', 'No results')}")
                data_sources_used.append("DATABASE")
            
            if has_retrieval:
                data_summary.append(f"=== RETRIEVED KNOWLEDGE BASE DOCUMENTS ===\n{state.get('retrieval_context', 'No context')}")
                data_sources_used.append("DOCUMENTS")
        
        # Build observation history
        observation_history = state.get('observation_history', [])
        if observation_history:
            obs_text = "\n".join([f"- {obs}" for obs in observation_history[-5:]])  # Last 5 observations
            data_summary.append(f"=== ANALYSIS STEPS ===\n{obs_text}")
        
        data_summary_text = "\n\n".join(data_summary) if data_summary else "No data was retrieved"
        data_source_note = f"[Data sources used: {', '.join(data_sources_used)}]" if data_sources_used else "[No data sources]"
        
        print(f"[FINISH] Data sources: {data_source_note}")
        
        prompt = f"""
You are a helpful AI assistant providing answers based on retrieved data and business intelligence.

USER QUESTION:
{state['question']}

GATHERED INFORMATION:
{data_summary_text}

DATA SOURCES USED:
{data_source_note}

TASK:
Generate a clear, direct answer to the user's question using ONLY the information provided above.

IMPORTANT RULES:
1. Always use EXACT numbers and data from the gathered information
2. For "how many", "count", or database questions: Use the specific number(s) from database results ONLY
3. For analytical questions: Synthesize all available data to provide insights
4. If database results contain the answer, USE THOSE NUMBERS DIRECTLY
5. Do NOT make up numbers or estimates - only use provided data
6. Be specific: Instead of "users exist", say "42 users were found in the database"
7. If data contradicts general knowledge, use the database data as truth
8. If no data was retrieved for a database question, explicitly state "No matching records found"
9. CRITICAL: If a question asks specifically for database data but database has no results, report this clearly

Answer format:
- Start with a direct answer to the question
- Include specific numbers/data points from results (with data source)
- Provide brief explanation if needed
- Mention data source (Database, External Knowledge, etc)
- Mention any data limitations

Your Answer:"""
        
        response_dict = call_llama(prompt)
        answer_text = response_dict['content']
        
        print(f"[FINISH] Answer generated (length: {len(answer_text)} chars)")
        
        return {
            "final_answer": answer_text,
            "data_sources": data_sources_used
        }
    except Exception as e:
        logger.error(f"Error generating final answer: {e}")
        return {
            "final_answer": f"I encountered an error while generating the answer: {str(e)}"
        }