import logging
from app.services.llm_runner import call_llama
from app.agent.core.state import AgentState

logger = logging.getLogger(__name__)

def finish_node(state: AgentState):
    """
    Node responsible for generating the final answer based on gathered information.
    Synthesizes multiple sub-questions if the original question was compound.
    """
    try:
        sub_questions = state.get('sub_questions', [state.get('question', '')])
        current_idx = state.get('current_sub_question_index', 0)
        current_question = sub_questions[current_idx] if current_idx < len(sub_questions) else state.get('question', '')
        
        # Determine if we're answering a sub-question or ready to synthesize the final answer
        is_final_synthesis = (current_idx >= len(sub_questions) - 1)
        sub_answers = state.get('sub_answers', [])
        
        # 1) Answer the current sub-question based on gathered data
        question_lower = current_question.lower()
        sql_keywords = ['how many', 'count', 'total', 'average', 'sum', 'number of', 'revenue', 'database']
        asks_for_db_data = any(kw in question_lower for kw in sql_keywords)
        
        has_sql_results = state.get('sql_has_results', False)
        has_sql_attempt = state.get('sql_attempted', False)
        has_retrieval = bool(state.get('retrieval_context'))
        
        data_summary = []
        data_sources_used = []
        
        if asks_for_db_data and has_sql_attempt:
            if has_sql_results and state.get('sql_result'):
                data_summary.append(f"=== DATABASE QUERY RESULTS ===\n{state.get('sql_result', 'No results')}")
                data_sources_used.append("DATABASE")
            else:
                data_summary.append("=== DATABASE QUERY RESULTS ===\nNo matching records found in database")
                data_sources_used.append("DATABASE (no results)")
        else:
            if state.get('sql_result'):
                data_summary.append(f"=== DATABASE QUERY RESULTS ===\n{state.get('sql_result', 'No results')}")
                data_sources_used.append("DATABASE")
            
            if has_retrieval:
                data_summary.append(f"=== RETRIEVED KNOWLEDGE BASE DOCUMENTS ===\n{state.get('retrieval_context', 'No context')}")
                data_sources_used.append("DOCUMENTS")
                
        data_summary_text = "\n\n".join(data_summary) if data_summary else "No data was retrieved"
        
        prompt = f"""You are a helpful AI assistant providing answers based on retrieved data.

CURRENT QUESTION TO ANSWER: {current_question}

GATHERED INFORMATION:
{data_summary_text}

TASK: Generate a clear, direct answer to the question using ONLY the information provided above. Use exact numbers from the database if present.

Your Answer:"""

        response_dict = call_llama(prompt)
        sub_answer_text = response_dict['content'].strip()
        
        sub_answers.append({
            "question": current_question,
            "answer": sub_answer_text
        })
        
        # Reset the data context for the next sub-question
        next_state = {
            "sub_answers": sub_answers,
            "current_sub_question_index": current_idx + 1,
            "sql_result": None,
            "last_sql": None,
            "retrieval_context": None,
            "sql_attempted": False,
            "sql_has_results": False,
            "step_count": 0,  # reset steps for next sub-question routing
            "observation_history": state.get("observation_history", []) + [f"Answered part {current_idx+1}: {sub_answer_text[:100]}..."],
            "data_sources": data_sources_used
        }
        
        # 2) If it was the last sub-question, synthesize the final answer
        if is_final_synthesis:
            # If there was only 1 sub-question, the sub_answer IS the final answer
            if len(sub_questions) == 1:
                next_state["final_answer"] = sub_answer_text
            else:
                # Synthesize all answers
                original_question = state.get("original_question", state.get("question", ""))
                combined_text = "\n\n".join([f"Q: {sa['question']}\nA: {sa['answer']}" for sa in sub_answers])
                
                synthesis_prompt = f"""You are an AI assistant tasked with answering a complex user question.
We have broken down the question into parts and answered each part separately.

ORIGINAL USER QUESTION:
{original_question}

COLLECTED PARTIAL ANSWERS:
{combined_text}

TASK: Combine all the partial answers into one cohesive, beautifully formatted final answer that directly addresses the original user question.

Your Final Answer:"""
                
                final_response = call_llama(synthesis_prompt)
                next_state["final_answer"] = final_response['content'].strip()
                
        return next_state
        
    except Exception as e:
        logger.error(f"Error generating final answer: {e}")
        return {
            "final_answer": f"I encountered an error while generating the answer: {str(e)}"
        }