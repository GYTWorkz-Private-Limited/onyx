"""
File utility functions for S3 Sync Service
"""
import os
import mimetypes
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class FileUtils:
    """Utility class for file operations"""
    
    @staticmethod
    def get_file_type(file_path: str) -> str:
        """
        Determine file type based on extension
        
        Args:
            file_path: Path to the file
            
        Returns:
            MIME type of the file
        """
        content_type, _ = mimetypes.guess_type(file_path)
        return content_type or "application/octet-stream"
    
    @staticmethod
    def s3_key_to_local_path(s3_key: str) -> str:
        """
        Convert an S3 key to a local file path
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Local file path
        """
        return settings.get_absolute_download_path(s3_key)
    
    @staticmethod
    def local_path_to_s3_key(local_path: str) -> str:
        """
        Convert a local file path to S3 key
        
        Args:
            local_path: Local file path
            
        Returns:
            S3 object key
        """
        # Remove the download directory prefix
        relative_path = os.path.relpath(local_path, settings.local_download_dir)
        return relative_path.replace(os.sep, '/')  # Use forward slashes for S3
    
    @staticmethod
    def ensure_directory_exists(file_path: str) -> bool:
        """
        Ensure the directory for a file path exists
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if directory exists or was created successfully
        """
        try:
            directory = os.path.dirname(file_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory for {file_path}: {e}")
            return False
    
    @staticmethod
    def get_file_size(file_path: str) -> Optional[int]:
        """
        Get the size of a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in bytes, or None if file doesn't exist
        """
        try:
            if os.path.exists(file_path):
                return os.path.getsize(file_path)
            return None
        except Exception as e:
            logger.error(f"Failed to get file size for {file_path}: {e}")
            return None
    
    @staticmethod
    def calculate_file_hash(file_path: str, algorithm: str = "md5") -> Optional[str]:
        """
        Calculate hash of a file
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm (md5, sha1, sha256)
            
        Returns:
            File hash as hex string, or None if failed
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            hash_obj = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate {algorithm} hash for {file_path}: {e}")
            return None
    
    @staticmethod
    def files_are_identical(file1_path: str, file2_path: str) -> bool:
        """
        Check if two files are identical by comparing size and hash
        
        Args:
            file1_path: Path to first file
            file2_path: Path to second file
            
        Returns:
            True if files are identical
        """
        try:
            # Check if both files exist
            if not (os.path.exists(file1_path) and os.path.exists(file2_path)):
                return False
            
            # Compare file sizes first (quick check)
            size1 = FileUtils.get_file_size(file1_path)
            size2 = FileUtils.get_file_size(file2_path)
            
            if size1 != size2:
                return False
            
            # Compare file hashes
            hash1 = FileUtils.calculate_file_hash(file1_path)
            hash2 = FileUtils.calculate_file_hash(file2_path)
            
            return hash1 == hash2 and hash1 is not None
            
        except Exception as e:
            logger.error(f"Failed to compare files {file1_path} and {file2_path}: {e}")
            return False
    
    @staticmethod
    def delete_file_safely(file_path: str) -> bool:
        """
        Safely delete a file with error handling
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if file was deleted successfully
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        info = {
            "path": file_path,
            "exists": False,
            "size": None,
            "modified_time": None,
            "content_type": None,
            "hash": None
        }
        
        try:
            if os.path.exists(file_path):
                info["exists"] = True
                stat = os.stat(file_path)
                info["size"] = stat.st_size
                info["modified_time"] = stat.st_mtime
                info["content_type"] = FileUtils.get_file_type(file_path)
                info["hash"] = FileUtils.calculate_file_hash(file_path)
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
        
        return info
    
    @staticmethod
    def cleanup_empty_directories(base_path: str) -> int:
        """
        Remove empty directories recursively
        
        Args:
            base_path: Base directory to start cleanup from
            
        Returns:
            Number of directories removed
        """
        removed_count = 0
        
        try:
            for root, dirs, files in os.walk(base_path, topdown=False):
                for directory in dirs:
                    dir_path = os.path.join(root, directory)
                    try:
                        if not os.listdir(dir_path):  # Directory is empty
                            os.rmdir(dir_path)
                            logger.debug(f"Removed empty directory: {dir_path}")
                            removed_count += 1
                    except Exception as e:
                        logger.debug(f"Could not remove directory {dir_path}: {e}")
        except Exception as e:
            logger.error(f"Error during directory cleanup: {e}")
        
        return removed_count
