from pydantic import BaseModel
from pymongo import MongoClient
from environment import environment
import os

COLLECTION_NAME = "sessions"
DB_NAME = "pulse"

# create a client
client = MongoClient(environment.MONGO_DB_URL)

def get_collection():
    return client[DB_NAME][COLLECTION_NAME]

def save_session(session_id: str, session_model: BaseModel):
    """
    Insert or update the session by filtering session_id using upsert.
    """
    collection = get_collection()
    print("got the collection", collection)
    collection.update_one(
        {"session_id": session_id},
        {"$set": session_model.model_dump()},
        upsert=True
    )

def get_session(session_id: str) -> BaseModel | None:
    """
    Get the session by filtering session_id.
    """
    collection = get_collection()
    session = collection.find_one({"session_id": session_id})
    return session