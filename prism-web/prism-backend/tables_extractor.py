from sqlalchemy import create_engine, inspect
from typing import Dict

def get_tables_and_columns(
    db_type: str,
    database: str,
    username: str,
    password: str,
    host: str,
    port: int
) -> Dict[str, list]:
    """
    Returns a dictionary with table names as keys and list of column names as values.
    
    db_type: 'postgresql' or 'mysql'
    """
    if db_type == "postgresql":
        uri = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}?connect_timeout=10"
        # print(uri)
    elif db_type == "mysql":
        uri = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}?connect_timeout=10"
    else:
        raise ValueError("Unsupported database type. Use 'postgresql' or 'mysql'.")

    try:
        engine = create_engine(uri)
        inspector = inspect(engine)

        schema = {}
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            schema[table_name] = [col["name"] for col in columns]

        return schema
    except Exception as e:
        # print("❌ Connection failed:", str(e))
        return {}
# if __name__=="__main__":
    # db_info = {
    #     "db_type": "postgresql",
    #     "username": "postgres",
    #     "password": "ntzzmeDX1tXrJz06YiHc",
    #     "host": "dev-lawndepot-postgresdb.cd4ecsq627o3.us-east-1.rds.amazonaws.com",
    #     "port": 5432,
    #     "database": "postgres"
    # }

    # schema_dict = get_tables_and_columns(**db_info)
    # print(schema_dict)