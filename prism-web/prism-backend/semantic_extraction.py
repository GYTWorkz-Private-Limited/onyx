import json
import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, inspect, MetaData, Table
import openai
from dotenv import load_dotenv
from models import get_database_connection,get_extracted_schema
load_dotenv()


# ====== SETUP OPENAI CLIENT ======
client = openai.OpenAI()  # make sure OPENAI_API_KEY is set in .env



# ====== PROMPT TEMPLATES ======
column_prompt_template = """
Column Name: `{col_name}`
Data Type: {col_type}
Column Stats or Sample Data: {meta}
Schema Column Metadata: {schema_meta}

Using the above info, generate a short, meaningful description of this column that captures what it likely represents in the dataset. Write it to be used in a vector search context (descriptive and keyword-rich, even if redundant).Keep it as short as possible
"""

table_prompt_template = """
Table Name: `{table_name}`
Column Descriptions:
{column_descriptions}

Schema Table Metadata:
{schema_meta}

Generate a concise summary of what this table represents and how it's likely used in the context of a relational database. Add any useful information that could support better understanding or searchability.keep it as short as possable
"""

db_prompt_template = """
Database Name: `{db_name}`
Table Descriptions:
{table_descriptions}

Schema Relationships and Metadata:
{schema_meta}

Generate an overview of this database's purpose, including any useful metadata or inferred relationships between tables that a developer or data scientist might want to know when exploring it.keep it as short as possable
"""

# ====== UTILITY FUNCTIONS ======
def ask_llm(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    return response.choices[0].message.content.strip()

def clean_numpy_floats(d):
    if isinstance(d, dict):
        return {k: clean_numpy_floats(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [clean_numpy_floats(i) for i in d]
    elif isinstance(d, np.generic):
        return d.item()
    else:
        return d

def render_column_prompt(col_name, col_type, meta, schema_meta):
    return column_prompt_template.format(
        col_name=col_name,
        col_type=col_type,
        meta=json.dumps(meta, ensure_ascii=False) if isinstance(meta, dict) else meta,
        schema_meta=json.dumps(schema_meta, ensure_ascii=False)
    )

def render_table_prompt(table_name, col_descs, schema_meta):
    desc_text = "\n".join([f"- {col}: {desc}" for col, desc in col_descs.items()])
    return table_prompt_template.format(
        table_name=table_name,
        column_descriptions=desc_text,
        schema_meta=json.dumps(schema_meta, ensure_ascii=False)
    )

def render_db_prompt(db_name, table_descs, schema_meta):
    desc_text = "\n".join([f"- {table}: {desc}" for table, desc in table_descs.items()])
    return db_prompt_template.format(
        db_name=db_name,
        table_descriptions=desc_text,
        schema_meta=json.dumps(schema_meta, ensure_ascii=False)
    )


def semantic_extactor(authorized_tables_columns_info,user_id):
    # db_type="postgresql"
    # username = "postgres"
    # password = "ntzzmeDX1tXrJz06YiHc"
    # host = "dev-lawndepot-postgresdb.cd4ecsq627o3.us-east-1.rds.amazonaws.com"
    # port = 5432
    # database = "lawnDepot"

    # ====== DATABASE CONFIG ======
    data_connection=get_database_connection(user_id)
    if data_connection["db_type"] == "postgresql":
        DATABASE_URL = f"postgresql+psycopg2://{data_connection["username"]}:{data_connection["password"]}@{data_connection["host"]}:{data_connection["port"]}/{data_connection["database"]}?connect_timeout=10"
    elif data_connection["db_type"] == "mysql":
        DATABASE_URL = f"mysql+pymysql://{data_connection["username"]}:{data_connection["password"]}@{data_connection["host"]}:{data_connection["port"]}/{data_connection["database"]}?connect_timeout=10"
    else:
        raise ValueError("Unsupported database type. Use 'postgresql' or 'mysql'.")
    
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    db_name = engine.url.database

    # ====== LOAD SCHEMA DATA ======
    # with open("schema_extraction.json", encoding='utf-8') as schema_extraction:
    #     schema_data = json.load(schema_extraction)
    schema_data=get_extracted_schema(user_id)
    # ====== MAIN PROCESSING ======
    semantic_json = {db_name: {}}
    table_descriptions = {}
    # print(authorized_tables_columns_info)
    with engine.connect() as conn:
        for table_name in authorized_tables_columns_info:
            
            semantic_json[db_name][table_name] = {}
            table = Table(table_name, metadata, autoload_with=engine)
            columns_str=", ".join(authorized_tables_columns_info[table_name])
            df = pd.read_sql(f"SELECT {columns_str} FROM {table_name}", conn)
            column_descriptions = {}

            for column in authorized_tables_columns_info[table_name]:
                col_name = column
                col_type = schema_data["tables"][table_name]["columns"][col_name]["type"]
                data = df[col_name]
                meta = ""

                if pd.api.types.is_string_dtype(data):
                    unique_vals = data.dropna().unique().tolist()[:10]
                    meta = ", ".join(map(str, unique_vals))
                elif pd.api.types.is_numeric_dtype(data):
                    desc = data.describe(percentiles=[.25, .5, 1.0])
                    meta = {
                        "min": clean_numpy_floats(desc.get("min", None)),
                        "max": clean_numpy_floats(desc.get("max", None)),
                        "mean": clean_numpy_floats(desc.get("mean", None)),
                        "25%": clean_numpy_floats(desc.get("25%", None)),
                        "50%": clean_numpy_floats(desc.get("50%", None)),
                        "100%": clean_numpy_floats(desc.get("100%", None)),
                    }

                schema_meta = schema_data["tables"][table_name]["columns"][col_name]
                prompt = render_column_prompt(col_name, col_type, meta, schema_meta)
                col_description = ask_llm(prompt)
                column_descriptions[col_name] = {
                    "column_info": meta,
                    "description": col_description
                }

            table_prompt = render_table_prompt(table_name, {k: v["description"] for k, v in column_descriptions.items()}, schema_data["tables"][table_name])
            table_description = ask_llm(table_prompt)
            table_descriptions[table_name] = table_description

            semantic_json[db_name][table_name] = {
                "columns": column_descriptions,
                "table_description": table_description
            }

    # Final Database Level Description
    db_prompt = render_db_prompt(db_name, table_descriptions, schema_data)
    database_description = ask_llm(db_prompt)
    semantic_json[db_name]["database_description"] = database_description

    # ====== SAVE TO FILE ======
    with open("semantic_database_description.json", "w", encoding='utf-8') as f:
        json.dump(semantic_json, f, indent=2, ensure_ascii=False)

    print("✅ Semantic understanding saved to semantic_database_description.json")

    return semantic_json
