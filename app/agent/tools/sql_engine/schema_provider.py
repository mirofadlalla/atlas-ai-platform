from sqlalchemy import inspect
from app.core.db import data_base

def get_schema_description():
    inspector = inspect(data_base)
    schema_text = ""

    for table in inspector.get_table_names():
        columns = inspector.get_columns(table)
        schema_text += f"\nTable: {table}\n"
        for col in columns:
            schema_text += f" - {col['name']} ({col['type']})\n"

    return schema_text