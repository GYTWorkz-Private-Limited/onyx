
# methods to save or # app/services/session_manager.py

from redis import Redis
from datetime import datetime, timedelta
from environment import environment
import json
import logging
from pydantic import BaseModel
# create redis client
redis_client = Redis(host=environment.REDIS_HOST, port=environment.REDIS_PORT, db=0)



class SessionManager:
    @staticmethod
    def create_session(session_id: str, session_model : BaseModel):
        redis_client.set(session_id, session_model.model_dump_json())
        return session_model

    @staticmethod
    async def add_or_update_last_used(session_id: str):
        res = await redis_client.zadd(
            "last_used", {session_id: int(datetime.utcnow().timestamp())})
        print(res)
    
    @staticmethod
    # persist session
    async def persist_session(session_id: str, session_model: BaseModel):
        """
        Persist the session in MongoDB.
        """

        await redis_client.set(session_id, session_model.model_dump_json())

    @staticmethod
    async def get_session(session_id: str, session_model: BaseModel) -> BaseModel:
        try:
            session_data = await redis_client.get(session_id)
            if session_data:
                session_dict = json.loads(session_data)  # returns a dict
                return session_model(**session_dict).model_dump()            # print("session_data : ",session_data)
            return None
        except Exception as e:
            print("Exception while reading redis session", e.__class__.__name__, str(e))
            return None

    @staticmethod
    async def store_session(session_id: str, session_model: BaseModel):
        await redis_client.set(session_id, session_model.model_dump_json())

    @staticmethod
    async def delete_session(session_id: str):
        await redis_client.delete(session_id)

session_manager = SessionManager()
