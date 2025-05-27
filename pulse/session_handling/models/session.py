from pydantic import BaseModel
from typing import Any, List, Dict
from enum import Enum




class Session(BaseModel):
    session_id: str
    user_id: str
    user_name:str = ""
    user_profile: Any = None # store app specific key-value pairs
    messages: List[Dict[str, str]] = []
    created_at: str = ""
    updated_at: str = ""
    # Add any addtional fields will go here...

