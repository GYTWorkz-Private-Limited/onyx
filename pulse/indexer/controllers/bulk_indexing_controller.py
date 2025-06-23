
from llama_index.core.schema import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Settings
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, TextIndexParams, TokenizerType, OptimizersConfigDiff

import os

# Set your OpenAI API Key from environment variable
from dotenv import load_dotenv
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable is required")

# === Step 1: Load and chunk text files ===
folder_path = os.path.join(os.path.dirname(__file__), "..", "parsed_data_text")

if not os.path.exists(folder_path):
    raise FileNotFoundError(f"Directory does not exist: {folder_path}")

documents = []
print("Files in directory:")
for file in os.listdir(folder_path):
    print(f"  - {file}")

txt_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
if not txt_files:
    raise Exception(f"No .txt files found in {folder_path}")

text_splitter = SentenceSplitter(chunk_size=512, chunk_overlap=100)

for filename in txt_files:
    with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as f:
        text = f.read()
        chunks = text_splitter.split_text(text)
        for chunk in chunks:
            documents.append(Document(text=chunk, metadata={"doc_id": filename}))

print(f"Total documents prepared: {len(documents)}")

# === Step 2: Setup embedding model and service context ===
embed_model = OpenAIEmbedding(model="text-embedding-3-small")  # 1536-d
# Set global settings
Settings.embed_model = embed_model
Settings.llm = None

# === Step 3: Setup Qdrant ===
collection_name = "my_txt_index"
client = QdrantClient(host="localhost", port=6333)

sample_embedding = embed_model.get_text_embedding("sample test text")
embedding_size = len(sample_embedding)
print(f"Embedding dimension: {embedding_size}")

if client.collection_exists(collection_name):
    client.delete_collection(collection_name)

from qdrant_client.http.models import OptimizersConfigDiff

client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=embedding_size, distance=Distance.COSINE),
    optimizers_config=OptimizersConfigDiff(
        indexing_threshold=100  # Lower threshold to force indexing with fewer vectors
    )
)

#  Optional: Add full-text index on `text` field
client.create_payload_index(
    collection_name=collection_name,
    field_name="text",
    field_schema=TextIndexParams(
        type="text",
        tokenizer=TokenizerType.WORD,
        min_token_len=2,
        max_token_len=15,
        lowercase=True
    )
)

# === Step 4: Create vectors with proper metadata ===

from qdrant_client.http.models import PointStruct
import uuid

points = []

print(f"Creating {len(documents)} vectors with embeddings...")

for i, doc in enumerate(documents):
    print(f"Processing document {i+1}/{len(documents)}: {doc.metadata['doc_id']}")

    # Generate embedding
    embedding = embed_model.get_text_embedding(doc.text)

    # Create point with proper top-level metadata
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding,
        payload={
            "doc_id": doc.metadata["doc_id"],
            "chunk_id": i,
            "text": doc.text  # content for search and display
        }
    )
    points.append(point)

print(f"Uploading {len(points)} points to Qdrant...")

# Upload points in batches to avoid memory issues
batch_size = 50
for i in range(0, len(points), batch_size):
    batch = points[i:i + batch_size]
    client.upsert(
        collection_name=collection_name,
        points=batch
    )
    print(f"Uploaded batch {i//batch_size + 1}/{(len(points) + batch_size - 1)//batch_size}")

print(" All points uploaded successfully!")

# === Step 5: Verify ===
collection_info = client.get_collection(collection_name)
print(f"\n Collection info:\n{collection_info}")
print(f" Vector count in Qdrant: {collection_info.vectors_count}")
