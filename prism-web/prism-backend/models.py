from passlib.context import CryptContext
from database import database_connections
from schemas import ConnectDB
from jose import JWTError, jwt
from fastapi import  HTTPException
from bson.objectid import ObjectId
from database import db_extracted_schema,db_generated_semantics,db_authorized_tables_columns_info,db_kpis
from sqlalchemy import create_engine, inspect, MetaData, Table,text

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash_password(password:str):
    return pwd_context.hash(password)

def verify_password(plain_password:str,hashed_password:str):
    return pwd_context.verify(plain_password,hashed_password)

def create_database_connection(database_connection:ConnectDB,user_id:str):
    connection_data=database_connection.model_dump()
    connection_data["user_id"]=user_id

    result=database_connections.insert_one(connection_data)
    return str(result.inserted_id)

def get_database_connection(user_id:str):
    try:
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401,detail="Invaild token")
    
    try:
        data_connection=database_connections.find_one({"user_id":user_id})
        
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    if not data_connection: 
        raise HTTPException(status_code=404,detail="Connection not found")
    return data_connection

def add_extracted_schema(response_schema,user_id):
    try:
        dic_response_schema=response_schema.copy()
        dic_response_schema["user_id"]=user_id
        response_db_extracted_schema=db_extracted_schema.insert_one(dic_response_schema)
        return {"inserted_id": str(response_db_extracted_schema.inserted_id)}
    except HTTPException as e:
        raise e

def get_extracted_schema(user_id: str):
    try:
        schemas = db_extracted_schema.find({"user_id": user_id})
        result = {}
        for schema in schemas:
            for table_name, columns in schema.items():
                if table_name not in ("_id", "user_id"):
                    result[table_name] = columns
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving extracted schemas: {str(e)}")
    
def save_authorized_tables_columns_info(authorized_tables_columns_info,user_id):
    try:
        dic_authorized_tables_columns_info=authorized_tables_columns_info.copy()
        dic_authorized_tables_columns_info["user_id"]=user_id
        response_db_authorized_tables_columns_info=db_authorized_tables_columns_info.insert_one(dic_authorized_tables_columns_info)
        # print("print save author",dic_authorized_tables_columns_info)
        return {"inserted_id": str(response_db_authorized_tables_columns_info.inserted_id)}
    except HTTPException as e:
        raise e
    
def get_authorized_tables_columns_info(user_id):
    try:
        schemas = list(db_authorized_tables_columns_info.find({"user_id": user_id}))
        # print(schemas,"schemas")
        result = {}
        for schema in schemas:
            for table_name, columns in schema.items():
                if table_name not in ("_id", "user_id"):
                    result[table_name] = columns

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving extracted schemas: {str(e)}")

    
    
def add_generated_semantics(semantic_response,user_id):
    try:
        dic_semantic_response=semantic_response.copy()
        dic_semantic_response["user_id"]=user_id
        response_db_extracted_semantic=db_generated_semantics.insert_one(dic_semantic_response)
        return {"inserted_id": str(response_db_extracted_semantic.inserted_id)}
    except HTTPException as e:
        raise e
    
def get_semantic_data(user_id:str):
    try:
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401,detail="Invaild token")
    try:
        semantic_data_extracted=db_generated_semantics.find_one({"user_id":user_id})
        
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    if not semantic_data_extracted: 
        raise HTTPException(status_code=404,detail="Connection not found")
    return semantic_data_extracted


def kpi_executor_on_db(user_id: str):
    kpis_list_db_response = db_kpis.find_one({"user_id": user_id}, {"user_id": 0, "_id": 0})
    if not kpis_list_db_response:
        return None  # Clearly return None when nothing is found
    
    
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
    list_of_answer_kpis=[]
    for kpi in kpis_list_db_response["kpis"]:
        
        query = kpi["formula"]
        name=kpi["name"]
        with engine.connect() as connection:
            result = connection.execute(text(query))
            rows = result.fetchall()
            result_list = [dict(row._mapping) for row in rows]
            list_of_answer_kpis.append({"name":name,"result":result_list})
    print(list_of_answer_kpis)
    return list_of_answer_kpis