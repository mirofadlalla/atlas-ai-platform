from app.agent.core.state import AgentState
from app.agent.tools.sql_engine.validator import SQLValidator
from app.core.db import get_db_session
from sqlalchemy import text
from app.agent.tools.sql_engine.sql_generator import generate_sql
import logging

logger = logging.getLogger(__name__)

def sql_node(state: AgentState):
    """
    Node responsible for generating and executing SQL queries.
    Retrieves structured data from the database.
    
    Args:
        state: The current agent state
        
    Returns:
        dict: Updated state with observation and sql_result
    """
    MAX_ALLOWED_COST = 1000.0 
    
    try:
        raw_sql = generate_sql(state['question'])
        print(f"[SQL_NODE] Generated SQL: {raw_sql[:200] if raw_sql else 'EMPTY'}...")
        logger.info(f"Generated SQL: {raw_sql[:200] if raw_sql else 'EMPTY'}...")
        
        safe_sql = SQLValidator.validate_and_enforce_tenant(raw_sql, state['tenant_id'])
        print(f"[SQL_NODE] Safe SQL (with tenant filter): {safe_sql[:200]}...")
        logger.info(f"Safe SQL: {safe_sql[:200]}...")
        
        cost = SQLValidator.get_query_cost(safe_sql)
        
        if cost > MAX_ALLOWED_COST:
            return {
                "observation": f"Error: Query is too expensive (Cost: {cost}). Please ask a more specific question."
            }

        db = get_db_session()
        result = db.execute(text(safe_sql)).fetchall()
        result_count = len(result) if result else 0
        print(f"[SQL_NODE] Query results: {result_count} rows")
        logger.info(f"Query returned {result_count} rows")
        db.close()
        
        # Format results nicely
        if result and result_count > 0:
            # Convert rows to readable format
            if hasattr(result[0], 'keys'):
                # SQLAlchemy Row objects
                formatted_results = []
                for row in result:
                    formatted_results.append(dict(zip(row.keys(), row)))
                result_str = "Found " + str(len(result)) + " record(s):\n" + str(formatted_results)
            else:
                # Tuple results
                result_str = f"Found {len(result)} record(s):\n{str(result)}"
            has_data = True
        else:
            result_str = "No results found"
            has_data = False
        
        observation = f"[DATABASE] SQL executed:\n{result_str}"
        print(f"[SQL_NODE] Observation: {observation[:150]}")
        
        return {
            "observation": observation,
            "observation_history": state.get('observation_history', []) + [observation],
            "last_sql": safe_sql,
            "sql_result": result_str if has_data else None,
            "sql_attempted": True,
            "sql_has_results": has_data,
            "total_cost": state.get('total_cost', 0.0) + cost
        }
    except ValueError as e:
        logger.error(f"SQL Security validation error: {e}")
        error_obs = f"Error: {str(e)}"
        return {
            "observation": error_obs,
            "observation_history": state.get('observation_history', []) + [error_obs]
        }
    except Exception as e:
        logger.error(f"SQL execution error: {e}")
        error_obs = f"Error executing query: {str(e)}"
        return {
            "observation": error_obs,
            "observation_history": state.get('observation_history', []) + [error_obs]
        }