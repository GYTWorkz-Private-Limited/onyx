"""File validation utilities."""

import os
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException

from environment import Environment
from utils.constants import SUPPORTED_EXTENSIONS, MAX_FILE_SIZE


class FileValidator:
    """File validation utilities."""
    
    @staticmethod
    def is_supported_file(filename: str) -> bool:
        """Check if file extension is supported."""
        return filename.lower().endswith(SUPPORTED_EXTENSIONS)
    
    @staticmethod
    def validate_file_size(file: UploadFile) -> bool:
        """Validate file size."""
        if hasattr(file, 'size') and file.size:
            return file.size <= MAX_FILE_SIZE
        return True  # If size is not available, assume it's valid
    
    @staticmethod
    def validate_upload_file(file: UploadFile) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not file.filename:
            return False, "No filename provided"
        
        if not FileValidator.is_supported_file(file.filename):
            return False, f"Unsupported file format. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
        
        if not FileValidator.validate_file_size(file):
            return False, f"File size exceeds maximum limit of {MAX_FILE_SIZE // (1024*1024)}MB"
        
        return True, None
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension."""
        return Path(filename).suffix.lower()
    
    @staticmethod
    def get_file_name_without_extension(filename: str) -> str:
        """Get filename without extension."""
        return Path(filename).stem
    
    @staticmethod
    def generate_temp_path(filename: str) -> str:
        """Generate temporary file path."""
        temp_dir = Environment.get_temp_dir()
        return os.path.join(temp_dir, f"temp_{filename}")
    
    @staticmethod
    def cleanup_temp_file(temp_path: str) -> None:
        """Clean up temporary file with robust error handling."""
        import time
        import gc

        if not os.path.exists(temp_path):
            return

        # Force garbage collection to close any lingering file handles
        gc.collect()

        # Try multiple times with increasing delays for Windows file locking issues
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                os.remove(temp_path)
                return  # Success!
            except OSError as e:
                if attempt < max_attempts - 1:
                    # Wait a bit and try again (Windows file locking can be delayed)
                    time.sleep(0.1 * (attempt + 1))  # 0.1s, 0.2s, 0.3s, 0.4s
                    continue
                else:
                    # Final attempt failed, log the error but don't raise it
                    print(f"Warning: Could not remove temporary file {temp_path}: {e}")
                    print(f"         File will be cleaned up on next server restart or manual cleanup")
    
    @staticmethod
    def validate_and_raise(file: UploadFile) -> None:
        """Validate file and raise HTTPException if invalid."""
        is_valid, error_message = FileValidator.validate_upload_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
