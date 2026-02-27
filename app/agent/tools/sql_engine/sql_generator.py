from app.services.llm_runner import call_llama
from pydantic import BaseModel
from app.agent.tools.sql_engine.schema_provider import get_schema_description
import logging

logger = logging.getLogger(__name__)

class SQLQuery(BaseModel):
    sql: str

def generate_sql(question: str) -> str:
    """
    Generate a SQL query based on a natural language question.
    
    Args:
        question: The natural language question
        
    Returns:
        str: The generated SQL query
    """
    try:
        schema = get_schema_description()

        prompt = f"""You are a SQL generator for a SaaS multi-tenant system.

RULES:
- Only generate SELECT queries.
- NEVER use UPDATE, DELETE, INSERT, DROP.
- Every query MUST filter by tenant_id.
- Do not hallucinate tables or columns.
- Return ONLY the SQL query, no explanations or markdown.

DATABASE SCHEMA:
{schema}

QUESTION:
{question}

Output ONLY valid SQL (no markdown, no explanations):"""

        response_dict = call_llama(prompt)
        sql = response_dict['content'].strip()
        print(f"[SQL_GEN] Raw LLM response: {sql[:150]}...")
        
        # Strip markdown code blocks if present
        if sql.startswith('```'):
            # Remove opening ```sql or ```
            sql = sql.split('```')[1]
            if sql.startswith('sql'):
                sql = sql[3:]
            sql = sql.strip()
        if sql.endswith('```'):
            # Remove closing ```
            sql = sql.rsplit('```', 1)[0].strip()
        
        print(f"[SQL_GEN] After cleanup: {sql}")
        logger.info(f"Generated SQL: {sql[:200]}...")
        return sql
    except Exception as e:
        logger.error(f"Error generating SQL: {e}")
        print(f"[SQL_GEN] ERROR: {e}")
        raise