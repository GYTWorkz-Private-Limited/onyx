
from pulse.dialouge_management.services.redis_service import session_manager
from pulse.dialouge_management.services.mongo_service import get_session as get_mongo_session, save_session as save_mongo_session
from pulse.dialouge_management.models.session import Session

# Create a new session and store it in Redis
def create_session(session_id: str, session_model: Session):
    return session_manager.create_session(session_id, session_model)

# Read session: check Redis first, if not found, check MongoDB
def read_session(session_id: str) -> Session | None:
    session = session_manager.get_session(session_id, Session)
    if session:
        return session
    mongo_data = get_mongo_session(session_id)
    if mongo_data:
        return Session(**mongo_data)
    return None

# Save session in Redis
def save_session(session_id: str, session_model: Session):
    session_manager.store_session(session_id, session_model)

# Persist session in MongoDB
def persist_session(session_id: str, session_model: Session):
    save_mongo_session(session_id, session_model)

