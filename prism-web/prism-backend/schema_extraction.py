from sqlalchemy import create_engine, inspect, MetaData, text
import json
import re
from typing import Dict,List
from models import get_database_connection


# Function to get check constraints for Postgres
def get_check_constraints_postgres(connection, table_name):
    sql = f"""
    SELECT conname, pg_get_constraintdef(oid) as definition
    FROM pg_constraint
    WHERE conrelid = '{table_name}'::regclass AND contype = 'c';
    """
    result = connection.execute(text(sql))
    return [row._mapping["definition"] for row in result]

# Function to get check constraints for SQLite
def get_check_constraints_sqlite(connection, table_name):
    sql = f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    result = connection.execute(text(sql)).fetchone()
    if result:
        sql_text = result[0]
        return re.findall(r'CHECK\s*\((.*?)\)', sql_text, re.IGNORECASE)
    return []

# Start extraction


def schema_extractor(authorized_data,user_id:str):
    authorized_tables_columns_info: Dict[str, List[str]] = authorized_data
    # print(authorized_tables_columns_info)
    # print(user_id)
    data_connection=get_database_connection(user_id)
    
    # Build connection string
    if data_connection["db_type"] == "postgresql":
        DATABASE_URL = f"postgresql+psycopg2://{data_connection["username"]}:{data_connection["password"]}@{data_connection["host"]}:{data_connection["port"]}/{data_connection["database"]}?connect_timeout=10"
    elif data_connection.db_type == "mysql":
        DATABASE_URL = f"mysql+pymysql://{data_connection["username"]}:{data_connection["password"]}@{data_connection["host"]}:{data_connection["port"]}/{data_connection["database"]}?connect_timeout=10"
    else:
        raise ValueError("Unsupported database type. Use 'postgresql' or 'mysql'.")

    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    schema_json = {"tables": {}, "relationships": []}

    with engine.connect() as conn:
        for table_name in inspector.get_table_names():
            if table_name in authorized_tables_columns_info.keys():
                table_info = {
                    "columns": {},
                    "primary_key": [],
                    "foreign_keys": {},
                    "unique_constraints": [],
                    "indexes": [],
                    "check_constraints": [],
                }

                # Primary Key
                pk = inspector.get_pk_constraint(table_name)
                table_info["primary_key"] = pk.get("constrained_columns", [])

                # Foreign Keys
                foreign_keys = inspector.get_foreign_keys(table_name)
                for fk in foreign_keys:
                    for col, ref_col in zip(fk["constrained_columns"], fk["referred_columns"]):
                        table_info["foreign_keys"][col] = {
                            "references": f"{fk['referred_table']}.{ref_col}"
                        }

                # Unique Constraints
                for uc in inspector.get_unique_constraints(table_name):
                    table_info["unique_constraints"].append(uc.get("column_names", []))

                # Indexes
                for idx in inspector.get_indexes(table_name):
                    table_info["indexes"].append({
                        "name": idx["name"],
                        "columns": idx["column_names"],
                        "unique": idx.get("unique", False)
                    })

                # Check Constraints
                if data_connection["db_type"] == "postgresql":
                    table_info["check_constraints"] = get_check_constraints_postgres(conn, table_name)

                # Columns
                for column in inspector.get_columns(table_name):
                    col_name = column["name"]
                    if col_name in authorized_tables_columns_info[table_name]:
                        col_type = str(column["type"])
                        nullable = column["nullable"]
                        default = column.get("default", None)
                        autoincrement = column.get("autoincrement", False)
                        is_unique = any(col_name in uc for uc in table_info["unique_constraints"])
                        is_primary = col_name in table_info["primary_key"]

                        table_info["columns"][col_name] = {
                            "type": col_type,
                            "nullable": nullable,
                            "default": default,
                            "auto_increment": autoincrement,
                            "unique": is_unique,
                            "primary_key": is_primary
                        }

                schema_json["tables"][table_name] = table_info

        # Relationships
        for table_name in inspector.get_table_names():
            if table_name in authorized_tables_columns_info:
                foreign_keys = inspector.get_foreign_keys(table_name)
                for fk in foreign_keys:
                    source_table = table_name
                    target_table = fk["referred_table"]
                    source_columns = fk["constrained_columns"]
                    target_columns = fk["referred_columns"]

                    is_unique = any(set(source_columns) == set(uc) for uc in inspector.get_unique_constraints(source_table))

                    all_fks = inspector.get_foreign_keys(source_table)
                    all_cols = inspector.get_columns(source_table)
                    is_m2m = (
                        len(all_fks) == 2
                        and len(all_cols) == 2
                        and all(col["name"] in fk["constrained_columns"] for fk in all_fks for col in all_cols)
                    )

                    if is_m2m:
                        rel_type = "many-to-many"
                    elif is_unique:
                        rel_type = "one-to-one"
                    else:
                        rel_type = "many-to-one"

                    schema_json["relationships"].append({
                        "from_table": source_table,
                        "from_columns": source_columns,
                        "to_table": target_table,
                        "to_columns": target_columns,
                        "type": rel_type
                    })
    with open("schema_extraction.json","w", encoding="utf-8") as file_extraction:
        json.dump(schema_json,file_extraction,indent=2,ensure_ascii=False)

    return schema_json
# if __name__=="__main__":
#     # Save to JSON
#     # with open("universal_sql_schema.json", "w") as f:
#     #     json.dump(schema_json, f, indent=2)

#     # print(f"✅ Schema extracted from `{db_type}` and saved to universal_sql_schema.json")
#     # print("ani")