import os
from dotenv import load_dotenv
load_dotenv()

class Environment:
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = os.getenv("REDIS_PORT", 6379)
    MONGO_DB_URL = os.getenv("MONGO_DB_URL", "mongodb://localhost:27017")

environment = Environment()

    