import sqlparse
import re
from prism.kpi_engine.utils.schema_mock import load_mock_schema

class FormulaValidationError(Exception):
    pass

def validate_formula(formula: str, schema: dict):
    # 1. Check SQL syntax using sqlparse
    try:
        parsed = sqlparse.parse(formula)
        if not parsed or not parsed[0].tokens:
            raise FormulaValidationError("Formula is not valid SQL syntax.")
    except Exception as e:
        raise FormulaValidationError(f"SQL syntax error: {e}")

    # 2. Extract table and column references (simple regex for demo)
    # This is a naive approach and works for simple SQL only
    table_pattern = re.compile(r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE)
    column_pattern = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b')

    tables = set(table_pattern.findall(formula))
    if not tables:
        raise FormulaValidationError("No table found in formula.")

    for table in tables:
        if table not in schema:
            raise FormulaValidationError(f"Table '{table}' not found in schema.")
        # Find all columns used after the table name
        # For demo, just check all words in formula against columns
        for col in schema[table]:
            if col in formula:
                continue
        # Optionally, you could extract columns more precisely
        # For now, just check that at least one column from the table is used
        if not any(col in formula for col in schema[table]):
            raise FormulaValidationError(f"No valid columns from table '{table}' used in formula.")
    # Optionally, check all column references
    # For now, pass if tables and at least one column per table are valid
    return True 