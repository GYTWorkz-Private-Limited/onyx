import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from sqlalchemy import create_engine, text
from qdrant_client import QdrantClient
import openai
import decimal
from json import JSONEncoder
from models import get_database_connection

# Load environment variables
load_dotenv()

# System Prompt Template
user_id_array=["default"]
memory = MemorySaver()
system_prompt = f"""
# Role
You are a concise business analyst assistant that helps users understand data *without ever exposing or referring to* SQL tables, columns, schema structures, or databases.

# Goal
- Provide high-level insights based on results from tools only.
- Do NOT expose technical terms or metadata in responses.
- Focus entirely on human-language explanations and visualization.

# Capabilities
You can:
- Use the tool `extract_revelent_info_from_vector_db` only if the user query is unclear.
- Use `run_sql_query` to fetch raw results.
- Use `create_analytical_chart` if the user explicitly asks for a chart or graph.
- Use `explain_sql_result` only if the user asks for an explanation of the data or result.

# Rules (Important)
- NEVER say: "table", "column", "schema", "field", "query", "SQL", "database"
- NEVER guess or mention missing data or structure
- NEVER explain access issues like "table not found" or "no table named X"
- If required data is not available and cannot be inferred, reply:
  <b>Final Answer:</b> Sorry, I don't have access to answer your question.

# Output Format
- For simple answers: use this HTML format:
  <b>Final Answer:</b> Your answer here.
- For charts: end with
  <b>Final Answer:</b> Chart saved as: [filename]
- NEVER give responses in markdown, only HTML.

# Chart Guidelines
Use `create_analytical_chart` if user says:
- "chart", "graph", "plot", "visualize", "analyze", or similar
Choose chart types based on context:
- bar: category comparison
- line: trends over time
- pie: parts of whole
- scatter: relationships

# Voice
- Be clear, direct, and business-friendly.
- Do NOT use uncertain language like "it seems", "maybe", "probably", etc.
- Avoid technical words and keep it end-user focused.

# Sample Bad Response (DON'T DO THIS)
❌ There is no table named `bike_riders` in the database.

# Sample Good Response
✅ <b>Final Answer:</b> Sorry, I don't have access to answer your question.
"""

# Prompt
prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_prompt),
    HumanMessagePromptTemplate.from_template("{input}")
])

# Model
model = ChatOpenAI(model_name="gpt-4.1", temperature=0)

# Load JSON files
with open("semantic_database_description.json", encoding="utf-8") as f1:
    semantic_understanding_json = json.load(f1)

with open("schema_extraction.json", encoding="utf-8") as f2:
    schema_extraction_json = json.load(f2)

# Create charts directory if it doesn't exist
CHARTS_DIR = "saved_charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

class DecimalEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super().default(o)

# Embedding function
def embed_text(text):
    response = openai.OpenAI().embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# ECharts generation function
def generate_echarts_from_data(chart_definitions: list):
    def convert(val):
        if isinstance(val, str) and val.endswith("T00:00:00"):
            return val[:10]  # Convert ISO date to 'YYYY-MM-DD'
        return val

    def get_option(chart):
        chart_type = chart["chart_type"]
        description = chart["description"]
        data = chart["data"]

        if not data:
            return {"title": {"text": description}, "series": []}

        keys = list(data[0].keys())

        if chart_type == "Line":
            return {
                "title": {"text": description},
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": [convert(row[keys[0]]) for row in data]},
                "yAxis": {"type": "value"},
                "series": [{
                    "data": [convert(row[keys[1]]) for row in data],
                    "type": "line"
                }]
            }

        elif chart_type == "Bar":
            return {
                "title": {"text": description},
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": [str(row[keys[0]]) for row in data]},
                "yAxis": {"type": "value"},
                "series": [{
                    "data": [convert(row[keys[1]]) for row in data],
                    "type": "bar"
                }]
            }

        elif chart_type == "Pie":
            return {
                "title": {"text": description, "left": "center"},
                "tooltip": {"trigger": "item"},
                "series": [{
                    "type": "pie",
                    "radius": "50%",
                    "data": [
                        {"value": convert(row[keys[1]]), "name": str(row[keys[0]])}
                        for row in data
                    ]
                }]
            }

        elif chart_type == "Scatter":
            return {
                "title": {"text": description},
                "tooltip": {"trigger": "item"},
                "xAxis": {"type": "value", "name": keys[0]},
                "yAxis": {"type": "value", "name": keys[1]},
                "series": [{
                    "symbolSize": 10,
                    "type": "scatter",
                    "data": [
                        [convert(row[keys[0]]), convert(row[keys[1]])]
                        for row in data
                    ]
                }]
            }

        elif chart_type == "Radar":
            indicators = [
                {"name": key, "max": max(convert(row[key]) for row in data)}
                for key in keys[1:]
            ]
            values = [convert(data[0][key]) for key in keys[1:]]
            return {
                "title": {"text": description},
                "tooltip": {},
                "radar": {"indicator": indicators},
                "series": [{
                    "type": "radar",
                    "data": [{
                        "value": values,
                        "name": str(data[0][keys[0]])
                    }]
                }]
            }

        return {"title": {"text": f"Unsupported chart type: {chart_type}"}}

    result = [get_option(chart) for chart in chart_definitions]
    return result

# Tool: Run SQL
@tool
def run_sql_query(query: str) -> str:
    """Execute SQL query and return results as JSON."""
    try:
        data_connection = get_database_connection(user_id_array[0])
        if data_connection["db_type"] == "postgresql":
            DATABASE_URL = f"postgresql+psycopg2://{data_connection['username']}:{data_connection['password']}@{data_connection['host']}:{data_connection['port']}/{data_connection['database']}?connect_timeout=10"
        elif data_connection["db_type"] == "mysql":
            DATABASE_URL = f"mysql+pymysql://{data_connection['username']}:{data_connection['password']}@{data_connection['host']}:{data_connection['port']}/{data_connection['database']}?connect_timeout=10"
        else:
            raise ValueError("Unsupported database type. Use 'postgresql' or 'mysql'.")
        
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text(query)).fetchall()
            data = [dict(row._mapping) for row in result]
        return json.dumps(data, indent=2, cls=DecimalEncoder)
    except Exception as e:
        return f"❌ Error executing SQL: {str(e)}"

# Tool: Create and save ECharts visualization (Updated)
@tool
def create_analytical_chart(user_id: str, data_json: str, chart_type: str, title: str, x_field: str, y_field: str, description: str = "") -> str:
    """
    Create and save an ECharts visualization from SQL data using the new generate_echarts_from_data function.
    
    Args:
        user_id: User identifier
        data_json: JSON string containing the data from SQL query
        chart_type: Type of chart ('Bar', 'Line', 'Pie', 'Scatter', 'Radar')
        title: Title for the chart
        x_field: Field name for x-axis (categories)
        y_field: Field name for y-axis (values)
        description: Optional description of what the chart shows
    
    Returns:
        String with the saved chart filename and ECharts option
    """
    try:
        # Parse the data
        data = json.loads(data_json)
        
        if not data:
            return "❌ No data provided for chart creation"
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_id = str(uuid.uuid4())[:8]
        filename = f"{chart_type.lower()}_{timestamp}_{chart_id}.json"
        filepath = os.path.join(CHARTS_DIR, filename)
        
        # Prepare chart definition for the new function
        chart_definition = {
            "chart_type": chart_type.capitalize(),  # Ensure proper capitalization
            "description": title if title else description,
            "data": data
        }
        
        # Generate ECharts options using the new function
        echarts_options = generate_echarts_from_data([chart_definition])
        
        if not echarts_options:
            return "❌ Failed to generate chart options"
        
        chart_option = echarts_options[0]
        
        # Save the chart option as JSON
        chart_data = {
            "filename": filename,
            "title": title,
            "description": description,
            "chart_type": chart_type,
            "x_field": x_field,
            "y_field": y_field,
            "created_at": datetime.now().isoformat(),
            "data_points": len(data),
            "echarts_option": chart_option
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chart_data, f, indent=2, ensure_ascii=False, cls=DecimalEncoder)
        
        return f"✅ Chart saved as: {filename}"
        
    except Exception as e:
        return f"❌ Error creating chart: {str(e)}"

# Function to execute SQL queries and generate charts
def execute_sql_queries(queries, user_id):
    """
    Executes SQL queries and returns results for each query using the provided database_info.
    """
    database_info = get_database_connection(user_id)
    
    # Construct DB connection URL
    db_type = database_info.get("db_type")
    if db_type == "postgresql":
        db_url = f"postgresql+psycopg2://{database_info['username']}:{database_info['password']}@{database_info['host']}:{database_info['port']}/{database_info['database']}?connect_timeout=10"
    elif db_type == "mysql":
        db_url = f"mysql+pymysql://{database_info['username']}:{database_info['password']}@{database_info['host']}:{database_info['port']}/{database_info['database']}?connect_timeout=10"
    else:
        print("❌ Unsupported database type. Only 'postgresql' and 'mysql' are supported.")
        return
    
    # Execute queries
    results = []
    try:
        engine = create_engine(db_url)
        with engine.connect() as connection:
            for item in queries:
                chart_type = item.get("chart_type")
                description = item.get("description")
                sql = item.get("sql")
                try:
                    result = connection.execute(text(sql))
                    rows = result.mappings().all()  # Convert each row to dict
                    results.append({
                        "chart_type": chart_type,
                        "description": description,
                        "sql": sql,
                        "data": [dict(row) for row in rows]  # Ensure proper dict conversion
                    })
                except Exception as query_error:
                    print(f"❌ Error executing SQL for '{description}': {query_error}")
                    results.append({
                        "chart_type": chart_type,
                        "description": description,
                        "sql": sql,
                        "error": str(query_error)
                    })
    except Exception as conn_error:
        print(f"❌ Database connection error: {conn_error}")
        return []
    
    return results

def sanitize_response(output: str) -> str:
    forbidden_keywords = [
        "table", "column", "schema", "sql", "query", "database", 
        "field", "structure", "filtered", "bike_rider", "bike_rides"
    ]
    lower_output = output.lower()
    if any(word in lower_output for word in forbidden_keywords):
        return "<b>Final Answer:</b> Sorry, I don't have access to answer your question."
    return output

# Tool: Explain SQL result
@tool
def explain_sql_result(context: str, question: str) -> str:
    """Explain SQL query results to a non-technical user."""

    # If context is empty or has no valid data, don't allow explanation
    if not context or context.strip() in ["[]", "{}", "null"]:
        return "<b>Final Answer:</b> Sorry, I don't have access to answer your question."

    try:
        parsed = json.loads(context)
        if isinstance(parsed, list) and len(parsed) == 0:
            return "<b>Final Answer:</b> Sorry, I don't have access to answer your question."
        if isinstance(parsed, dict) and not parsed:
            return "<b>Final Answer:</b> Sorry, I don't have access to answer your question."
    except Exception:
        return "<b>Final Answer:</b> Sorry, I don't have access to answer your question."

    exp_prompt = f"""
# Role
You are a concise and helpful data analyst assistant who explains SQL query results in plain English, without exposing any technical metadata unless explicitly required.

# Objective
You are given:
- A SQL result as context
- A user question

Your task is to:
1. Understand the user question.
2. Interpret the SQL result in clear, business-friendly language.
3. Do not mention table names, column names, values like "bike_rider", or SQL structures.
4. Do not infer missing or filtered values.
5. If the context is ambiguous or you are unsure, reply with:
   <b>Final Answer:</b> Sorry, I don't have access to answer your question.

# Output Rules
- Always respond using HTML tags.
- Wrap your explanation like this: <b>Final Answer:</b> Your explanation.
- Never use technical terms like "column", "schema", "table", "SQL", or "query".
- Never assume or fabricate a filtered value (e.g., "account_type is bike_rider").

# Input
Explain this SQL result:
{context}
Based on the user question:
{question}
"""

    formatted = prompt.format_messages(input=exp_prompt)
    raw_output = model.invoke(formatted).content
    return sanitize_response(raw_output)

# Tool: Extract relevant info from vector DB
@tool
def extract_revelent_info_from_vector_db(question: str) -> str:
    """Retrieve relevant information from vector DB based on the question."""
    score_threshold = 0.15
    search_limit = 50
    qdrant = QdrantClient(host="localhost", port=6333)
    query_vector = embed_text(question)

    results = qdrant.search(
        collection_name=user_id_array[0],
        query_vector=query_vector,
        limit=search_limit,
        score_threshold=score_threshold
    )

    llm_context = {
        "query_related_tables": [],
        "query_related_columns": [],
        "meta_data": []
    }

    for hit in results:
        llm_context["meta_data"].append({
            "semantic_score": hit.score,
            "meta_info": hit.payload
        })

        if hit.payload['type'] == "table":
            llm_context["query_related_tables"].append({
                "table_name": hit.payload['table_name'],
                "table_description": semantic_understanding_json[
                    hit.payload['database_name']
                ][hit.payload['table_name']]["table_description"]
            })

        if hit.payload['type'] == "column":
            llm_context["query_related_columns"].append({
                "column_name": hit.payload['column_name'],
                "column_description": semantic_understanding_json[
                    hit.payload['database_name']
                ][hit.payload['table_name']]["columns"][
                    hit.payload['column_name']
                ]["description"]
            })

    return str(llm_context)

def conversational_agent(user_input, user_id):
    user_id_array[0] = user_id
    
    # Agent setup
    tools = [run_sql_query, explain_sql_result, extract_revelent_info_from_vector_db, create_analytical_chart]
    agent_executor = create_react_agent(model, tools, checkpointer=memory)

    # Agent loop
    config = {"configurable": {"thread_id": f"{user_id}"}}
    
    result = agent_executor.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)

    return result["messages"][-1].content