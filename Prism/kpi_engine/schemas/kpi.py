from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class KPIDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    formula: str

class KPIResponse(KPIDefinition):
    created_by: str
    created_at: datetime 