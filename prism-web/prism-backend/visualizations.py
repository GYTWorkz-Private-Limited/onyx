from openai import OpenAI
from models import get_semantic_data,get_database_connection
import json
from sqlalchemy import create_engine, text
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.engine import RowMapping
import json
from database import db_visualizations
def get_sql_queries(user_id):
    semantics=get_semantic_data(user_id)
    # with open("semantic_database_description.json","r") as sddj:
    #     semantics=json.load(sddj)
    print(semantics)
    prompt=f"""

You are a data analyst assistant. I will provide you with a database semantics.

semantics:
{semantics}

Based on this, generate a list of SQL queries that return data suitable for visualizing common business metrics using Apache ECharts.

Each item should be a valid JSON object with:

- "chart_type": chart type (e.g., Line, Bar, Pie, Scatter, Radar)
- "description": what the chart will show
- "sql": a self-contained, ready-to-run SQL query optimized for aggregated visualization

Only include a chart if it's meaningful based on the schema. Skip time-based or radar charts if no suitable columns exist.

Return **only** a JSON array, no notes, no markdown, no explanation. Ensure the JSON is valid and directly usable with `json.loads()`.
don't add ```json or ``` in the response

Output format:
[
  {{
    "chart_type": "Line",
    "description": "Revenue trends over time by month",
    "sql": "SELECT DATE_TRUNC('month', order_date) AS month, SUM(revenue) AS total_revenue FROM orders GROUP BY month ORDER BY month"
  }},
  {{
    "chart_type": "Bar",
    "description": "Number of products in each category",
    "sql": "SELECT category, COUNT(*) AS product_count FROM products GROUP BY category"
  }}
]
"""


    client=OpenAI()
    response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=0.4
)
    sql_queries_response=response.choices[0].message.content
    print("==========================================================")
    print("Hi")
    print(type(sql_queries_response))
    print(sql_queries_response)
    print("==========================================================")

    return json.loads(sql_queries_response)

# get_sql_queries("abc")


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, RowMapping):
            return dict(obj)  # convert RowMapping to dict
        return super().default(obj)


def execute_sql_queries(queries,user_id):
    """
    Executes SQL queries from sql_queries.json and returns results
    for each query using the provided database_info.
    Results are stored in executed_sql_results.json.
    """
    database_info=get_database_connection(user_id)
    # Step 1: Load the generated SQL queries
    # try:
    #     with open("sql_queries.json", "r") as f:
    #         queries = json.load(f)
    #          # Convert from string to list of dicts
    # except Exception as e:
    #     print(f"❌ Failed to load or parse sql_queries.json: {e}")
    #     return

    # Step 2: Construct DB connection URL
    db_type = database_info.get("db_type")
    if db_type == "postgresql":
        db_url = f"postgresql+psycopg2://{database_info['username']}:{database_info['password']}@{database_info['host']}:{database_info['port']}/{database_info['database']}"
    elif db_type == "mysql":
        db_url = f"mysql+pymysql://{database_info['username']}:{database_info['password']}@{database_info['host']}:{database_info['port']}/{database_info['database']}"
    else:
        print("❌ Unsupported database type. Only 'postgresql' and 'mysql' are supported.")
        return

    # Step 3: Execute queries
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
                    rows = result.mappings().all()  # ✅ Convert each row to dict
                    results.append({
                        "chart_type": chart_type,
                        "description": description,
                        "sql": sql,
                        "data": rows
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
        

    # Step 4: Save results to JSON file
    # print(results)

    try:
        with open("executed_sql_results.json", "w") as fout:
            json.dump(results, fout, indent=2, cls=CustomJSONEncoder)

        with open("executed_sql_results.json","r") as rfout:
            json_result=json.load(rfout)
            return json_result

        print("✅ Executed queries and saved results to 'executed_sql_results.json'")
    except Exception as write_error:
        print(f"❌ Error saving results: {write_error}")


# database_info = {
#     "db_type": "postgresql",
#     "host": "dev-lawndepot-postgresdb.cd4ecsq627o3.us-east-1.rds.amazonaws.com",
#     "port": 5432,
#     "username": "postgres",
#     "password": "ntzzmeDX1tXrJz06YiHc",
#     "database": "postgres"
# }

# execute_sql_queries(database_info)


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

    # result= [
    #     {
    #         "chart_type": chart["chart_type"],
    #         "description": chart["description"],
    #         "sql": chart["sql"],
    #         "option": get_option(chart)
    #     }
    #     for chart in chart_definitions
    # ]
    # return result

    result= [get_option(chart) for chart in chart_definitions]
    return result




# # `chart_definitions` = the big list you pasted above (already fetched data)
# with open("executed_sql_results.json","r") as esqj:
#     chart_definitions =json.load(esqj) 

# # To view:
# echarts_configs = generate_echarts_from_data(chart_definitions)
# with open("echart_response.json","w") as erjw:
#     json.dump(echarts_configs,erjw,indent=2)
# # print(json.dumps(echarts_configs, indent=2))



def visualization_generator(user_id):
    try:
        sql_query_response=get_sql_queries(user_id)
        sql_query_executer_response=execute_sql_queries(sql_query_response,user_id)
        gen_chat_response=generate_echarts_from_data(sql_query_executer_response)
        db_visualizations.insert_one({"charts":gen_chat_response,"user_id":user_id})
        return "successfull generated echarts"
    except Exception as e:
        raise e