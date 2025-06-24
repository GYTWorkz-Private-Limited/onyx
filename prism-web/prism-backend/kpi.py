import argparse
import json
import logging
import re
import sqlparse
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import psycopg2
from psycopg2 import sql as psql
from pydantic import BaseModel
import openai
import os
from models import get_database_connection
from database import db_kpis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# OpenAI Client Initialization
def init_openai_client():
    """
    Initialize OpenAI client using API key from environment.
    
    Returns:
        OpenAI client instance.
    
    Raises:
        RuntimeError: If API key is not set.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set.")
        raise RuntimeError("OpenAI API key is required for natural language processing.")
    return openai.OpenAI(api_key=api_key)

# PostgreSQL Configuration
class PostgreSQLConfig(BaseModel):
    host: str 
    port: int 
    database: str 
    username: str 
    password: str

# Pydantic Models
class KPIDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    formula: str
    formula_type: str = "sql"  # sql or general
    group_by: Optional[List[str]] = None  # Columns for GROUP BY in general formulas

class KPIResponse(KPIDefinition):
    created_at: datetime

class DBStatusResponse(BaseModel):
    connected: bool
    tables: Dict[str, List[str]]
    message: str

# Custom Exceptions
class FormulaValidationError(Exception):
    """Exception raised for invalid KPI formulas."""
    pass

class KPIError(Exception):
    """Exception raised for KPI-related errors."""
    pass

# PostgreSQL Client Initialization
def init_postgres_client(config: PostgreSQLConfig):
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=config["host"],
            port=config["port"],
            dbname=config["database"],
            user=config["username"],
            password=config["password"]
        )
        conn.autocommit = True

        # Test connection
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")  # Simple test query
            logger.info(f"Successfully connected to PostgreSQL database: {config["database"]}")

        return conn

    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        raise

# Utility Functions
def load_db_schema(client):
    """
    Fetch schema (tables and columns) from PostgreSQL database.
    
    Args:
        client: PostgreSQL connection instance.
    
    Returns:
        Dictionary mapping table names to lists of column names.
    
    Raises:
        RuntimeError: If schema loading fails.
    """
    try:
        schema = {}
        with client.cursor() as cursor:
            # Get all tables in the current schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"Connected to PostgreSQL database. Available tables:")
            for table in tables:
                # Get columns for each table
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = %s
                """, (table,))
                columns = [row[0] for row in cursor.fetchall()]
                schema[table] = columns
                logger.info(f"- {table}: {columns}")
                
        if not tables:
            logger.info("No tables found in the database.")
        return schema
    except Exception as e:
        logger.error(f"Failed to load database schema: {e}")
        raise RuntimeError(f"Failed to load schema: {e}")

def find_join_keys(table1: str, table2: str, schema: Dict[str, List[str]]) -> Optional[str]:
    """
    Find a common column to use as a join key between two tables.
    
    Args:
        table1: First table name.
        table2: Second table name.
        schema: Database schema.
    
    Returns:
        Join key column name or None if no common key found.
    """
    common_columns = set(schema.get(table1, [])) & set(schema.get(table2, []))
    for key in ["product_id", "id", "user_id", "region"]:
        if key in common_columns:
            return key
    return common_columns.pop() if common_columns else None

def build_join_path(tables: List[str], schema: Dict[str, List[str]]) -> List[Tuple[str, str, str]]:
    """
    Build a list of JOIN operations to connect all required tables.
    
    Args:
        tables: List of table names to join.
        schema: Database schema.
    
    Returns:
        List of tuples (table1, table2, join_key) representing JOIN operations.
    
    Raises:
        FormulaValidationError: If no valid join path is found.
    """
    if len(tables) <= 1:
        return []
    
    joins = []
    visited = {tables[0]}
    remaining = set(tables[1:])

    while remaining:
        found = False
        for table1 in visited:
            for table2 in remaining:
                join_key = find_join_keys(table1, table2, schema)
                if join_key:
                    joins.append((table1, table2, join_key))
                    visited.add(table2)
                    remaining.remove(table2)
                    found = True
                    break
            if found:
                break
        if not found:
            raise FormulaValidationError(f"Cannot find join path for tables: {tables}")

    return joins

def parse_natural_formula(formula: str, schema: Dict[str, List[str]], openai_client, max_retries: int = 1) -> tuple[str, Optional[List[str]]]:
    """
    Parse a natural language formula using OpenAI LLM to generate SQL and extract grouping.
    
    Args:
        formula: Natural language formula (e.g., "what is the average profit per quantity sold in each 3 months").
        schema: Database schema.
        openai_client: OpenAI client instance.
        max_retries: Maximum number of retries for LLM call.
    
    Returns:
        Tuple of (SQL query, group_by columns).
    
    Raises:
        FormulaValidationError: If LLM fails to generate valid SQL.
    """
    schema_str = "\n".join([f"Table {table}: {', '.join(cols)}" for table, cols in schema.items()])
    prompt = f"""
Given the following PostgreSQL database schema:
{schema_str}

Convert the natural language query "{formula}" into a valid PostgreSQL SQL query. The query should:
- Handle aggregations (e.g., average → AVG, total → SUM).
- Identify metrics and map them to schema columns (e.g., 'quantity sold' → 'quantity_sold').
- Handle time-based groupings (e.g., 'each 3 months' → GROUP BY date_trunc('quarter', date)).
- Use appropriate JOINs based on common columns (e.g., product_id, region).
- Use table aliases (e.g., s.column).
- Return *only* a valid JSON object with the SQL query and GROUP BY columns (if any):
  {{"sql": "SELECT ...", "group_by": ["column1", "column2"]}}
- Do not include code fences (```), comments, or extra text.

Ensure the SQL is valid and compatible with PostgreSQL. If the query cannot be generated, return:
  {{"sql": "", "group_by": [], "error": "Reason for failure"}}
"""
    
    for attempt in range(max_retries + 1):
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a SQL query generator for PostgreSQL, specializing in KPI formulas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            raw_content = response.choices[0].message.content
            logger.debug(f"Raw LLM response (attempt {attempt + 1}): {raw_content}")
            
            # Clean response: remove code fences and extra whitespace
            cleaned_content = raw_content.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:].rstrip("```").strip()
            
            # Parse JSON
            result = json.loads(cleaned_content)
            sql_query = result.get("sql")
            group_by = result.get("group_by", [])
            error = result.get("error")
            
            if error or not sql_query:
                raise FormulaValidationError(f"LLM failed to generate SQL: {error or 'No SQL provided'}")
            
            return sql_query, group_by if group_by else None
        except openai.OpenAIError as e:
            logger.error(f"OpenAI API error (attempt {attempt + 1}): {e}")
            if attempt == max_retries:
                raise FormulaValidationError(f"Failed to parse formula with LLM after {max_retries + 1} attempts: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from LLM (attempt {attempt + 1}): {e}")
            if attempt == max_retries:
                # Fallback for single-table case
                if "profit" in schema.get("sales_data", []) and "quantity_sold" in schema.get("sales_data", []) and "date" in schema.get("sales_data", []):
                    logger.warning("Using fallback SQL query for single-table formula.")
                    fallback_sql = "SELECT AVG(s.profit) / AVG(s.quantity_sold) FROM sales_data AS s GROUP BY date_trunc('quarter', s.date)"
                    return fallback_sql, ["date_trunc('quarter', s.date)"]
                raise FormulaValidationError(f"LLM returned invalid response format after {max_retries + 1} attempts: {e}")

def convert_general_to_sql(formula: str, schema: Dict[str, List[str]], group_by: Optional[List[str]] = None, openai_client=None) -> str:
    """
    Convert general formula to SQL query, supporting aggregations and GROUP BY.
    
    Args:
        formula: General formula (e.g., "SUM(profit) / SUM(quantity_sold)" or natural language).
        schema: Database schema.
        group_by: Optional list of columns to group by.
        openai_client: OpenAI client for natural language parsing.
    
    Returns:
        SQL query string.
    
    Raises:
        FormulaValidationError: If conversion fails.
    """
    # Check if formula is natural language
    if not re.match(r'^\s*(SUM|AVG|COUNT|MAX|MIN|\w+)\s*\(', formula, re.IGNORECASE) and not re.match(r'^\s*\w+\s*/\s*\w+', formula):
        if not openai_client:
            raise FormulaValidationError("Natural language formulas require OpenAI client.")
        sql_query, inferred_group_by = parse_natural_formula(formula, schema, openai_client)
        group_by = group_by or inferred_group_by
        return sql_query

    # Detect aggregation functions
    agg_pattern = re.compile(r'\b(SUM|AVG|COUNT|MAX|MIN)\s*\(\s*(\w+)\s*\)', re.IGNORECASE)
    agg_matches = agg_pattern.findall(formula)
    agg_columns = [match[1] for match in agg_matches]
    non_agg_columns = [col for col in re.findall(r'\b\w+\b', formula) if col not in agg_columns and col not in ["SUM", "AVG", "COUNT", "MAX", "MIN"]]

    # Map columns to their tables
    column_to_table = {}
    for table, cols in schema.items():
        for col in cols:
            if col in agg_columns or col in non_agg_columns:
                column_to_table[col] = table

    # Check if all columns are found
    all_columns = agg_columns + non_agg_columns
    missing_columns = [col for col in all_columns if col not in column_to_table]
    if missing_columns:
        raise FormulaValidationError(f"Columns not found in schema: {', '.join(missing_columns)}")

    # Include group_by columns in mapping
    if group_by:
        for col in group_by:
            col_name = col.split(".")[-1] if "." in col else col
            if col_name.startswith("date_trunc"):
                col_name = re.search(r'\w+\.\w+', col).group().split(".")[1]
            found = False
            for table, cols in schema.items():
                if col_name in cols:
                    column_to_table[col_name] = table
                    found = True
                    break
            if not found:
                raise FormulaValidationError(f"Group by column '{col_name}' not found in schema.")

    # Get unique tables
    used_tables = list(set(column_to_table.values()))
    if not used_tables:
        raise FormulaValidationError("No tables contain the referenced columns.")

    # Qualify columns with table aliases
    table_aliases = {table: table[0].lower() for table in used_tables}
    qualified_formula = formula
    for col in all_columns:
        if col in column_to_table:
            table = column_to_table[col]
            alias = table_aliases[table]
            qualified_formula = re.sub(r'\b' + col + r'\b', f"{alias}.{col}", qualified_formula)

    # Generate SQL query
    if len(used_tables) == 1:
        query = f"SELECT {qualified_formula} FROM {used_tables[0]} AS {table_aliases[used_tables[0]]}"
    else:
        joins = build_join_path(used_tables, schema)
        if not joins:
            raise FormulaValidationError(f"No valid join path found for tables: {used_tables}")
        first_table = used_tables[0]
        query = f"SELECT {qualified_formula} FROM {first_table} AS {table_aliases[first_table]}"
        for table1, table2, join_key in joins:
            alias1, alias2 = table_aliases[table1], table_aliases[table2]
            query += f" JOIN {table2} AS {alias2} ON {alias1}.{join_key} = {alias2}.{join_key}"

    # Add GROUP BY if needed
    if agg_matches or group_by:
        group_by_cols = group_by or non_agg_columns
        if not group_by_cols:
            raise FormulaValidationError("Aggregation functions or time-based grouping require a GROUP BY clause.")
        group_by_clause = ", ".join(col if col.startswith("date_trunc") else f"{table_aliases[column_to_table[col.split('.')[-1]]]}.{col.split('.')[-1]}" for col in group_by_cols)
        query += f" GROUP BY {group_by_clause}"

    return query

def validate_formula(formula: str, schema: Dict[str, List[str]], formula_type: str, group_by: Optional[List[str]] = None) -> str:
    """
    Validate KPI formula against database schema.
    
    Args:
        formula: Formula to validate (SQL or general).
        schema: Database schema (tables and columns).
        formula_type: Type of formula ('sql' or 'general').
        group_by: Optional list of columns to group by (for general formulas).
    
    Returns:
        Validated (and possibly converted) SQL formula.
    
    Raises:
        FormulaValidationError: If formula is invalid.
    """
    if formula_type == "general":
        try:
            openai_client = init_openai_client()
            formula = convert_general_to_sql(formula, schema, group_by, openai_client)
        except FormulaValidationError as e:
            raise FormulaValidationError(f"Invalid general formula: {e}")
    
    try:
        parsed = sqlparse.parse(formula)
        if not parsed or not parsed[0].tokens:
            raise FormulaValidationError("Formula is not valid SQL syntax.")
    except Exception as e:
        raise FormulaValidationError(f"SQL syntax error: {e}")

    table_pattern = re.compile(r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE)
    tables = set(table_pattern.findall(formula))
    if not tables:
        raise FormulaValidationError("No table found in formula.")

    for table in tables:
        if table not in schema:
            raise FormulaValidationError(f"Table '{table}' not found in database schema. Available tables: {list(schema.keys())}")
        if not any(col in formula for col in schema[table]):
            raise FormulaValidationError(f"No valid columns from table '{table}' used in formula. Available columns: {schema[table]}")

    if "JOIN" in formula.upper():
        join_pattern = re.compile(r'join\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE)
        join_tables = set(join_pattern.findall(formula))
        for table in join_tables:
            if table not in schema:
                raise FormulaValidationError(f"Join table '{table}' not found in schema. Available tables: {list(schema.keys())}")

    # Validate GROUP BY for SQL formulas with aggregations
    if formula_type == "sql" and any(agg in formula.upper() for agg in ["SUM", "AVG", "COUNT", "MAX", "MIN"]):
        non_agg_columns = re.findall(r'\b(?!(SUM|AVG|COUNT|MAX|MIN)\()[a-zA-Z_][a-zA-Z0-9_]*(?!\))\b', formula, re.IGNORECASE)
        group_by_pattern = re.compile(r'group\s+by\s+(.+?)(?:\s*(?:having|order\s+by|$))', re.IGNORECASE)
        group_by_match = group_by_pattern.search(formula)
        if non_agg_columns and not group_by_match:
            raise FormulaValidationError("SQL formula with aggregations must include GROUP BY for non-aggregated columns.")
        if group_by_match:
            group_by_cols = [col.strip() for col in group_by_match.group(1).split(",")]
            for col in group_by_cols:
                col_name = col.split(".")[-1] if "." in col else col
                if col_name not in sum(col for table in schema.values() for col in table) and not col_name.startswith("date_trunc"):
                    raise FormulaValidationError(f"Group by column '{col_name}' not found in schema.")

    return formula

# KPI Repository
class KPIJsonRepository:
    """Manages KPI storage in a JSON file."""
    
    def __init__(self, file_path: Path,user_id:str):
        self.file_path = file_path
        self.user_id=user_id

    # def _load_kpis(self) -> List[Dict]:
    #     """Load KPIs from JSON file."""
    #     if not self.file_path.exists():
    #         return []
    #     try:
    #         with open(self.file_path, "r") as f:
    #             return json.load(f)
    #     except json.JSONDecodeError as e:
    #         logger.error(f"Failed to load KPIs from {self.file_path}: {e}")
    #         return []

    def _save_kpis(self, kpi:Dict) -> None:
        """Save KPIs to JSON file."""
        try:
            with open(self.file_path, "w") as f:
                json.dump(kpi, f, default=str, indent=2)
            existing_doc = db_kpis.find_one({"user_id": self.user_id})
            if not existing_doc:
                db_kpis.insert_one({"user_id": self.user_id, "kpis": []})
                
            db_kpis.update_one(
                {"user_id": self.user_id},
                {"$push": {"kpis": kpi}}
                )
            
        except IOError as e:
            logger.error(f"Failed to save KPIs to {self.file_path}: {e}")
            raise KPIError(f"Failed to save KPIs: {e}")

    def add_kpi(self, kpi: KPIDefinition) -> KPIResponse:
        """Add a new KPI."""
        # kpis = self._load_kpis()
        # if any(existing["name"] == kpi.name for existing in kpis):
        #     raise KPIError(f"KPI with name '{kpi.name}' already exists.")
        
        kpi_data = kpi.dict()
        kpi_data["created_at"] = datetime.utcnow().isoformat()
        # kpis.append(kpi_data)
        self._save_kpis(kpi_data)
        return KPIResponse(**kpi_data)

    # def list_kpis(self) -> List[KPIResponse]:
    #     """List all KPIs."""
    #     return [KPIResponse(**k) for k in self._load_kpis()]

    # def get_kpi_by_name(self, name: str) -> Optional[KPIResponse]:
    #     """Get a KPI by name."""
    #     for kpi in self._load_kpis():
    #         if kpi["name"] == name:
    #             return KPIResponse(**kpi)
    #     return None

# Command Handlers
def create_kpi(name: str, formula: str, description: Optional[str], formula_type: str, group_by: Optional[List[str]], client, repo: KPIJsonRepository) -> None:
    """
    Create a new KPI.
    
    Args:
        name: KPI name.
        formula: SQL or general formula.
        description: Optional KPI description.
        formula_type: Type of formula ('sql' or 'general').
        group_by: Optional list of columns to group by (for general formulas).
        client: PostgreSQL connection.
        repo: KPI repository.
    """
    try:
        kpi = KPIDefinition(name=name, formula=formula, description=description, formula_type=formula_type, group_by=group_by)
        schema = load_db_schema(client)
        kpi.formula = validate_formula(kpi.formula, schema, formula_type, group_by)
        result = repo.add_kpi(kpi)
        logger.info(f"Created KPI: {result.name}")
        # print(json.dumps(result.dict(), indent=2, default=str))
    except (FormulaValidationError, KPIError) as e:
        logger.error(f"Failed to create KPI: {e}")
        raise

def list_kpis(repo: KPIJsonRepository) -> None:
    """List all KPIs."""
    kpis = repo.list_kpis()
    if not kpis:
        logger.info("No KPIs found.")
        print("No KPIs found.")
        return
    logger.info(f"Found {len(kpis)} KPIs.")
    print(json.dumps([kpi.dict() for kpi in kpis], indent=2, default=str))

def get_kpi(name: str, repo: KPIJsonRepository) -> None:
    """Get a KPI by name."""
    kpi = repo.get_kpi_by_name(name)
    if not kpi:
        logger.error(f"KPI '{name}' not found.")
        print(f"KPI '{name}' not found.")
        return
    logger.info(f"Retrieved KPI: {name}")
    print(json.dumps(kpi.dict(), indent=2, default=str))

def check_db_status(client) -> None:
    """Check PostgreSQL database connection and list tables."""
    try:
        schema = load_db_schema(client)
        response = DBStatusResponse(
            connected=True,
            tables=schema,
            message=f"Successfully connected to PostgreSQL database"
        )
        logger.info(response.message)
        print(json.dumps(response.dict(), indent=2))
    except RuntimeError as e:
        response = DBStatusResponse(
            connected=False,
            tables={},
            message=f"Failed to connect to PostgreSQL database: {str(e)}"
        )
        logger.error(response.message)
        print(json.dumps(response.dict(), indent=2))

# CLI Setup
def kpi_main(kpi,user_id):
    # Initialize dependencies
    config = get_database_connection(user_id)
    # print(config)
    try:
        client = init_postgres_client(config)
    except RuntimeError as e:
        logger.error(f"Failed to start: {e}")
        exit(1)

    repo = KPIJsonRepository(Path("kpi_registry.json"),user_id)
    create_kpi(kpi.name, kpi.formula, kpi.description, kpi.formula_type, kpi.group_by, client, repo)

if __name__ == "__main__":
    kpi_main()