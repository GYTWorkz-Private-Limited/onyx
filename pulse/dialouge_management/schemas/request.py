from pydantic import BaseModel
from models.session import Session

class CreateSessionRequest(BaseModel):
    session_id: str
    session: Session