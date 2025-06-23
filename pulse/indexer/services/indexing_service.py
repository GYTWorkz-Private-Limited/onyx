"""Core indexing service for processing documents."""

import os
import uuid
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from llama_index.core.schema import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Settings
from qdrant_client.http.models import PointStruct

from .config import get_settings, validate_openai_key
from .qdrant_service import QdrantService

logger = logging.getLogger(__name__)


class IndexingService:
    """Service for indexing documents into Qdrant vector database."""
    
    def __init__(self):
        self.settings = get_settings()
        self.qdrant_service = QdrantService()
        self.embed_model = None
        self.text_splitter = None
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize embedding model and text splitter."""
        if not validate_openai_key():
            raise ValueError("OpenAI API key is not configured or invalid")
        
        # Set OpenAI API key
        os.environ["OPENAI_API_KEY"] = self.settings.openai_api_key
        
        # Initialize embedding model
        self.embed_model = OpenAIEmbedding(model=self.settings.openai_embedding_model)
        
        # Set global settings
        Settings.embed_model = self.embed_model
        Settings.llm = None
        
        # Initialize text splitter
        self.text_splitter = SentenceSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap
        )
        
        logger.info("Indexing service initialized successfully")
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from the model."""
        try:
            sample_embedding = self.embed_model.get_text_embedding("sample test text")
            return len(sample_embedding)
        except Exception as e:
            logger.error(f"Error getting embedding dimension: {e}")
            raise
    
    def process_text_content(self, text: str, doc_id: str) -> List[Document]:
        """Process text content into chunks."""
        try:
            chunks = self.text_splitter.split_text(text)
            documents = []
            
            for chunk in chunks:
                documents.append(Document(
                    text=chunk,
                    metadata={"doc_id": doc_id}
                ))
            
            logger.info(f"Processed {len(documents)} chunks from {doc_id}")
            return documents
            
        except Exception as e:
            logger.error(f"Error processing text content for {doc_id}: {e}")
            raise
    
    def process_file(self, file_path: Union[str, Path], doc_id: Optional[str] = None) -> List[Document]:
        """Process a single file into documents."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if doc_id is None:
            doc_id = file_path.name
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            return self.process_text_content(text, doc_id)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise
    
    def process_directory(self, directory_path: Union[str, Path], file_extension: str = ".txt") -> List[Document]:
        """Process all files in a directory."""
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        files = list(directory_path.glob(f"*{file_extension}"))
        if not files:
            raise ValueError(f"No {file_extension} files found in {directory_path}")
        
        all_documents = []
        
        for file_path in files:
            try:
                documents = self.process_file(file_path)
                all_documents.extend(documents)
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                continue
        
        logger.info(f"Processed {len(all_documents)} total documents from {len(files)} files")
        return all_documents
    
    def create_points_from_documents(self, documents: List[Document]) -> List[PointStruct]:
        """Create Qdrant points from documents with embeddings."""
        points = []
        
        logger.info(f"Creating embeddings for {len(documents)} documents...")
        
        for i, doc in enumerate(documents):
            try:
                # Generate embedding
                embedding = self.embed_model.get_text_embedding(doc.text)
                
                # Create point
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "doc_id": doc.metadata["doc_id"],
                        "chunk_id": i,
                        "text": doc.text
                    }
                )
                points.append(point)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Created embeddings for {i + 1}/{len(documents)} documents")
                    
            except Exception as e:
                logger.error(f"Error creating embedding for document {i}: {e}")
                continue
        
        logger.info(f"Created {len(points)} points with embeddings")
        return points
    
    def index_documents(self, documents: List[Document], collection_name: str) -> Dict[str, Any]:
        """Index documents into Qdrant collection."""
        try:
            # Get embedding dimension
            embedding_dim = self.get_embedding_dimension()
            
            # Create or recreate collection
            if not self.qdrant_service.create_collection(collection_name, embedding_dim):
                raise Exception("Failed to create collection")
            
            # Create points with embeddings
            points = self.create_points_from_documents(documents)
            
            if not points:
                raise Exception("No valid points created")
            
            # Upload points to Qdrant
            if not self.qdrant_service.upsert_points(collection_name, points):
                raise Exception("Failed to upload points")
            
            # Get collection info for verification
            collection_info = self.qdrant_service.get_collection_info(collection_name)
            
            result = {
                "success": True,
                "collection_name": collection_name,
                "documents_processed": len(documents),
                "points_created": len(points),
                "vectors_count": collection_info.vectors_count if collection_info else 0
            }
            
            logger.info(f"Successfully indexed {len(documents)} documents into {collection_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            return {
                "success": False,
                "error": str(e),
                "collection_name": collection_name,
                "documents_processed": len(documents)
            }
