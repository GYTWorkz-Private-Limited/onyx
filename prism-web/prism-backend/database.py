from pymongo import MongoClient 
import os 
from dotenv import load_dotenv

load_dotenv()

client=MongoClient(os.getenv("MONGO_URI"))

db=client["prism-test"]
users_collection=db["users"]

database_connections=db["database_connections"]

db_authorized_tables_columns_info=db["authorized_tables_columns_info"]

db_extracted_schema=db["db_extracted_schema"]

db_generated_semantics=db["db_generated_semantics"]

db_kpis=db["db_kpis"]

db_visualizations=db["visualizations"]