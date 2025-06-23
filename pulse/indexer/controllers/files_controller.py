"""Controller for file management operations."""

import logging
from typing import List, Dict, Any
from pathlib import Path
from fastapi import UploadFile, HTTPException

from services.config import Settings
from models.responses import FileUploadResponse

logger = logging.getLogger(__name__)


class FilesController:
    """Controller for coordinating file management operations."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    async def upload_file(self, file: UploadFile) -> FileUploadResponse:
        """Process and save an uploaded file."""
        try:
            # Validate file
            self._validate_file(file)
            
            # Prepare file path
            file_path = self._prepare_file_path(file.filename)
            
            # Save file
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            logger.info(f"File uploaded: {file_path}")
            
            return FileUploadResponse(
                filename=file_path.name,
                size=len(content),
                content_type=file.content_type or "application/octet-stream",
                saved_path=str(file_path)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def upload_multiple_files(self, files: List[UploadFile]) -> List[FileUploadResponse]:
        """Process and save multiple uploaded files."""
        try:
            if not files:
                raise HTTPException(status_code=400, detail="No files provided")
            
            results = []
            errors = []
            
            for file in files:
                try:
                    # Validate file
                    self._validate_file(file)
                    
                    # Prepare file path
                    file_path = self._prepare_file_path(file.filename)
                    
                    # Save file
                    content = await file.read()
                    with open(file_path, "wb") as f:
                        f.write(content)
                    
                    results.append(FileUploadResponse(
                        filename=file_path.name,
                        size=len(content),
                        content_type=file.content_type or "application/octet-stream",
                        saved_path=str(file_path)
                    ))
                    
                    logger.info(f"File uploaded: {file_path}")
                    
                except HTTPException as e:
                    errors.append(f"{file.filename}: {e.detail}")
                    continue
                except Exception as e:
                    errors.append(f"{file.filename}: {str(e)}")
                    continue
            
            if errors and not results:
                raise HTTPException(status_code=400, detail=f"All uploads failed: {'; '.join(errors)}")
            
            if errors:
                logger.warning(f"Some uploads failed: {'; '.join(errors)}")
            
            return results
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading multiple files: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def list_uploaded_files(self) -> List[Dict[str, Any]]:
        """List all uploaded files with metadata."""
        try:
            upload_dir = Path(self.settings.upload_directory)
            
            if not upload_dir.exists():
                return []
            
            files = []
            for file_path in upload_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        "filename": file_path.name,
                        "size": stat.st_size,
                        "created_at": stat.st_ctime,
                        "modified_at": stat.st_mtime,
                        "path": str(file_path)
                    })
            
            return sorted(files, key=lambda x: x["modified_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def delete_file(self, filename: str) -> Dict[str, str]:
        """Delete an uploaded file."""
        try:
            upload_dir = Path(self.settings.upload_directory)
            file_path = upload_dir / filename
            
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            if not file_path.is_file():
                raise HTTPException(status_code=400, detail="Path is not a file")
            
            # Security check: ensure file is within upload directory
            if not str(file_path.resolve()).startswith(str(upload_dir.resolve())):
                raise HTTPException(status_code=400, detail="Invalid file path")
            
            file_path.unlink()
            logger.info(f"File deleted: {file_path}")
            
            return {"message": f"File '{filename}' deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting file {filename}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def _validate_file(self, file: UploadFile) -> None:
        """Validate file size and extension."""
        # Validate file size
        if file.size and file.size > self.settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {self.settings.max_file_size} bytes"
            )
        
        # Validate file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self.settings.allowed_file_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed extensions: {self.settings.allowed_file_extensions}"
            )
    
    def _prepare_file_path(self, filename: str) -> Path:
        """Prepare file path, handling duplicates."""
        # Create upload directory if it doesn't exist
        upload_dir = Path(self.settings.upload_directory)
        upload_dir.mkdir(exist_ok=True)
        
        # Handle duplicate filenames
        file_path = upload_dir / filename
        counter = 1
        original_path = file_path
        
        while file_path.exists():
            stem = original_path.stem
            suffix = original_path.suffix
            file_path = upload_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        return file_path
