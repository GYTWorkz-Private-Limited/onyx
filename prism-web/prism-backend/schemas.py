from pydantic import BaseModel,RootModel,EmailStr
from typing import Dict, List,Optional

class UserCreate(BaseModel):
    user_name:str 
    email:str 
    password:str 


class UserLogin(BaseModel):
    email:str 
    password:str 

class Token(BaseModel):
    access_token:str 
    token_type:str 

class ConnectDB(BaseModel):
    db_type:str
    database: str
    username: str
    password: str
    host: str
    port: int

class AuthorizedTablesColumnsInfo((RootModel[Dict[str, List[str]]])):
    pass

class UserInput(BaseModel):
    user_input: str

class KPI(BaseModel):
    name:str
    description: Optional[str] = None
    formula: str
    formula_type: str = "sql"  # sql or general
    group_by: Optional[List[str]] = None 
 
class KPIs(BaseModel):
    kpis: List[KPI]


