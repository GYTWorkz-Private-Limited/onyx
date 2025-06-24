import json
import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import openai
from dotenv import load_dotenv
from models import get_semantic_data

# ====== LOAD ENVIRONMENT VARIABLES ======
load_dotenv()
openai_client = openai.OpenAI()



# ====== EMBEDDING FUNCTION ======
def embed_text(text):
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding  # correct object access


def vectordb_insertion(user_id):
    # ====== LOAD SEMANTIC JSON FILE ======
    semantic_json = get_semantic_data(user_id)
    # Get the DB name (top-level key)
    # print(semantic_json)
    db_name = list(semantic_json.keys())[1]
    # print(db_name)

    # ====== SETUP QDRANT CONNECTION ======
    qdrant = QdrantClient(host="localhost", port=6333)
    collection_name = user_id

    # Create or recreate collection if not exists
    if collection_name not in [c.name for c in qdrant.get_collections().collections]:
        qdrant.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )

    # ====== PREPARE QDRANT POINTS ======
    qdrant_points = []

    # --- 1. Column-level Descriptions ---
    for table_name, table_data in semantic_json[db_name].items():
        if table_name == "database_description":
            continue
        for col_name, col_data in table_data["columns"].items():
            embedding = embed_text(col_data["description"])
            metadata = {
                "type": "column",
                "column_name": col_name,
                "table_name": table_name,
                "database_name": db_name
            }
            point_id = str(uuid.uuid4())
            qdrant_points.append(PointStruct(id=point_id, vector=embedding, payload=metadata))

    # --- 2. Table-level Descriptions ---
    for table_name, table_data in semantic_json[db_name].items():
        if table_name == "database_description":
            continue
        embedding = embed_text(table_data["table_description"])
        metadata = {
            "type": "table",
            "table_name": table_name,
            "database_name": db_name
        }
        point_id = str(uuid.uuid4())
        qdrant_points.append(PointStruct(id=point_id, vector=embedding, payload=metadata))

    # --- 3. Database-level Description ---
    embedding = embed_text(semantic_json[db_name]["database_description"])
    metadata = {
        "type": "database",
        "database_name": db_name
    }
    point_id = str(uuid.uuid4())
    qdrant_points.append(PointStruct(id=point_id, vector=embedding, payload=metadata))

    # ====== UPSERT INTO QDRANT ======
    # print(qdrant_points)
    qdrant.upsert(
        collection_name=collection_name,
        points=qdrant_points
    )
    # print("✅ All descriptions successfully embedded and stored in Qdrant!")
    return "successfull inserted data"


