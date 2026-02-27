from app.agent.tools.sql_engine.schema_provider import get_schema_description
from app.services.llm_runner import call_llama

def generate_sql_logic(question: str):

    schema = get_schema_description()

    prompt = f"""
    You are a SQL generator for a SaaS multi-tenant system.

    RULES:
    - Only generate SELECT queries.
    - NEVER use UPDATE, DELETE, INSERT, DROP.
    - Every query MUST filter by tenant_id.
    - Do not hallucinate tables or columns.

    DATABASE SCHEMA:
    {schema}

    QUESTION:
    {question}

    Generate ONLY valid PostgreSQL SQL:
    """

    response = call_llama(prompt)
    sql = response['content'].strip()

    return sql