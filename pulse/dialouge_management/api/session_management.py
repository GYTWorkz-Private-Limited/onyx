from fastapi import APIRouter
from services.redis_service import session_manager
from services.mongo_service import save_session as save_mongo_session, get_session as get_mongo_session
from models.session import Session
from schemas.request import CreateSessionRequest

router = APIRouter()


@router.post("/session")
def create_or_update_session(request: CreateSessionRequest):
    session_manager.create_session(request.session_id, request.session)
    return {"message": "Session created or updated successfully"}

@router.get("/session")
def get_session(session_id: str):
    return session_manager.get_session(session_id, Session)
    

@router.post("/session/persist")
def persist_session(request: CreateSessionRequest):
    save_mongo_session(request.session_id, request.session)
    return {"message": "Session persisted successfully"}

@router.delete("/session")
def delete_session(session_id: str):
    session_manager.delete_session(session_id)
    return {"message": "Session deleted successfully"}
