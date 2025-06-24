"""Controller for indexing operations."""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import UploadFile, HTTPException

from services.indexing_service import IndexingService
from models.requests import IndexDirectoryRequest, IndexTextRequest, BatchIndexRequest
from models.responses import IndexingResponse

logger = logging.getLogger(__name__)


class IndexingController:
    """Controller for coordinating indexing operations."""
    
    def __init__(self, indexing_service: IndexingService):
        self.indexing_service = indexing_service
    
    async def index_uploaded_file(
        self, 
        file: UploadFile, 
        collection_name: str, 
        doc_id: Optional[str] = None
    ) -> IndexingResponse:
        """Process and index an uploaded file."""
        try:
            # Read and validate file content
            content = await file.read()
            text = content.decode('utf-8')
            
            # Use filename as doc_id if not provided
            if not doc_id:
                doc_id = file.filename
            
            # Process and index
            documents = self.indexing_service.process_text_content(text, doc_id)
            result = self.indexing_service.index_documents(documents, collection_name)
            
            return self._build_indexing_response(
                result=result,
                success_message=f"Successfully indexed file '{file.filename}'",
                collection_name=collection_name
            )
            
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File must be valid UTF-8 text")
        except Exception as e:
            logger.error(f"Error indexing file {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def index_multiple_files(
        self, 
        files: List[UploadFile], 
        collection_name: str
    ) -> IndexingResponse:
        """Process and index multiple uploaded files."""
        try:
            if not files:
                raise HTTPException(status_code=400, detail="No files provided")
            
            all_documents = []
            processed_files = []
            errors = []
            
            # Process each file
            for file in files:
                try:
                    content = await file.read()
                    text = content.decode('utf-8')
                    
                    documents = self.indexing_service.process_text_content(text, file.filename)
                    all_documents.extend(documents)
                    processed_files.append(file.filename)
                    
                except UnicodeDecodeError:
                    errors.append(f"{file.filename}: Invalid UTF-8 encoding")
                    continue
                except Exception as e:
                    errors.append(f"{file.filename}: {str(e)}")
                    continue
            
            if not all_documents:
                raise HTTPException(
                    status_code=400, 
                    detail=f"No files could be processed. Errors: {'; '.join(errors)}"
                )
            
            # Index all documents
            result = self.indexing_service.index_documents(all_documents, collection_name)
            
            # Build success message
            message = f"Successfully indexed {len(processed_files)} files"
            if errors:
                message += f" (with {len(errors)} errors)"
            
            return self._build_indexing_response(
                result=result,
                success_message=message,
                collection_name=collection_name
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error indexing multiple files: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def index_directory(self, request: IndexDirectoryRequest) -> IndexingResponse:
        """Process and index all files in a directory."""
        try:
            # Validate directory path
            directory_path = Path(request.directory_path)
            if not directory_path.exists():
                raise HTTPException(status_code=404, detail=f"Directory not found: {request.directory_path}")
            
            if not directory_path.is_dir():
                raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.directory_path}")
            
            # Process directory
            documents = self.indexing_service.process_directory(
                directory_path, 
                request.file_extension
            )
            
            if not documents:
                raise HTTPException(
                    status_code=400, 
                    detail=f"No {request.file_extension} files found in directory"
                )
            
            # Index documents
            result = self.indexing_service.index_documents(documents, request.collection_name)
            
            return self._build_indexing_response(
                result=result,
                success_message=f"Successfully indexed directory '{request.directory_path}'",
                collection_name=request.collection_name
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error indexing directory {request.directory_path}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def index_text(self, request: IndexTextRequest) -> IndexingResponse:
        """Process and index raw text content."""
        try:
            # Process text content
            documents = self.indexing_service.process_text_content(request.text, request.doc_id)
            
            # Index documents
            result = self.indexing_service.index_documents(documents, request.collection_name)
            
            return self._build_indexing_response(
                result=result,
                success_message="Successfully indexed text content",
                collection_name=request.collection_name
            )
            
        except Exception as e:
            logger.error(f"Error indexing text content: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def index_batch_texts(self, request: BatchIndexRequest) -> IndexingResponse:
        """Process and index multiple text contents in batch."""
        try:
            # Validate request
            request.validate_lengths()
            
            all_documents = []
            
            # Process each text
            for text, doc_id in zip(request.texts, request.doc_ids):
                documents = self.indexing_service.process_text_content(text, doc_id)
                all_documents.extend(documents)
            
            # Index all documents
            result = self.indexing_service.index_documents(all_documents, request.collection_name)
            
            return self._build_indexing_response(
                result=result,
                success_message=f"Successfully indexed {len(request.texts)} text contents",
                collection_name=request.collection_name
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error indexing batch texts: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def _build_indexing_response(
        self,
        result: Dict[str, Any],
        success_message: str,
        collection_name: str
    ) -> IndexingResponse:
        """Build a standardized IndexingResponse."""
        return IndexingResponse(
            success=result["success"],
            message=success_message if result["success"] else f"Failed to index: {result.get('error', 'Unknown error')}",
            collection_name=collection_name,
            documents_processed=result["documents_processed"],
            points_created=result.get("points_created"),
            vectors_count=result.get("vectors_count"),
            error=result.get("error")
        )
