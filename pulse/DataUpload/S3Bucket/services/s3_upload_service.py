"""
S3 Upload Service - Business logic for uploading files to S3
"""
import asyncio
import boto3
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from datetime import datetime
from fastapi import UploadFile
from botocore.exceptions import ClientError, NoCredentialsError

from config.settings import settings
from models.upload_models import UploadFileResult, UploadResponse
from utils.logger import get_logger

logger = get_logger(__name__)


class S3UploadService:
    """Service class for handling S3 upload operations"""
    
    def __init__(self):
        """Initialize S3 upload service"""
        self.s3_client = self._create_s3_client()
        self.thread_pool = ThreadPoolExecutor(max_workers=settings.max_concurrent_uploads)
        logger.info("S3 Upload Service initialized")
    
    def _create_s3_client(self):
        """Create and configure S3 client"""
        try:
            client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
            
            # Test connection by listing buckets
            client.head_bucket(Bucket=settings.s3_bucket_name)
            logger.info(f"Successfully connected to S3 bucket: {settings.s3_bucket_name}")
            return client
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise ValueError("AWS credentials not configured properly")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"S3 bucket not found: {settings.s3_bucket_name}")
                raise ValueError(f"S3 bucket '{settings.s3_bucket_name}' does not exist")
            elif error_code == '403':
                logger.error(f"Access denied to S3 bucket: {settings.s3_bucket_name}")
                raise ValueError(f"Access denied to S3 bucket '{settings.s3_bucket_name}'")
            else:
                logger.error(f"Error connecting to S3: {e}")
                raise ValueError(f"Failed to connect to S3: {e}")
    
    async def upload_file_to_s3(self, file: UploadFile, s3_key: str) -> UploadFileResult:
        """
        Upload a single file to S3 asynchronously
        
        Args:
            file: UploadFile instance
            s3_key: S3 key (path) for the file
            
        Returns:
            UploadFileResult with upload status and details
        """
        start_time = datetime.now()
        
        try:
            # Read file content
            content = await file.read()
            file_size = len(content)
            
            logger.info(f"Uploading {file.filename} ({file_size} bytes) to s3://{settings.s3_bucket_name}/{s3_key}")
            
            # Run S3 upload in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.thread_pool,
                lambda: self.s3_client.put_object(
                    Bucket=settings.s3_bucket_name,
                    Key=s3_key,
                    Body=content,
                    ContentType=self._get_content_type(file.filename)
                )
            )
            
            upload_time = datetime.now()
            duration = (upload_time - start_time).total_seconds()
            
            logger.info(f"Successfully uploaded {file.filename} in {duration:.2f} seconds")
            
            return UploadFileResult(
                filename=file.filename,
                s3_path=f"s3://{settings.s3_bucket_name}/{s3_key}",
                status="success",
                file_size=file_size,
                upload_time=upload_time
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error uploading {file.filename}: {error_msg}")
            
            return UploadFileResult(
                filename=file.filename,
                s3_path=f"s3://{settings.s3_bucket_name}/{s3_key}",
                status="failed",
                error=error_msg,
                upload_time=datetime.now()
            )
        finally:
            # Ensure file is closed
            if hasattr(file, 'close'):
                await file.close()
    
    async def upload_multiple_files(
        self,
        files: List[UploadFile],
        project_name: str,
        s3_prefix: str = ""
    ) -> UploadResponse:
        """
        Upload multiple files to S3 with concurrent processing
        
        Args:
            files: List of files to upload
            project_name: Project name for organizing uploads
            s3_prefix: Optional S3 prefix path
            
        Returns:
            UploadResponse with detailed results
        """
        start_time = datetime.now()
        
        # Create full S3 prefix path
        full_prefix = f"projects/{project_name}/{s3_prefix}".rstrip("/")
        
        # Prepare upload tasks
        upload_tasks = []
        valid_files = []
        
        for file in files:
            if not file.filename:
                logger.warning("Skipping file with no filename")
                continue
            
            # Construct S3 key
            s3_key = f"{full_prefix}/{file.filename}".replace("//", "/")
            
            # Create upload task
            task = self.upload_file_to_s3(file, s3_key)
            upload_tasks.append(task)
            valid_files.append(file)
        
        if not upload_tasks:
            logger.warning("No valid files found for upload")
            return UploadResponse(
                status="failed",
                summary="No valid files found for upload",
                uploaded_files=[],
                total_files=0,
                successful_uploads=0,
                failed_uploads=0,
                project_name=project_name,
                s3_prefix=s3_prefix
            )
        
        # Process uploads with concurrency control
        results = []
        batch_size = settings.max_concurrent_uploads
        
        for i in range(0, len(upload_tasks), batch_size):
            batch = upload_tasks[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} with {len(batch)} files")
            
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            # Handle any exceptions in batch results
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    file_idx = i + j
                    filename = valid_files[file_idx].filename if file_idx < len(valid_files) else "unknown"
                    logger.error(f"Exception in upload task for {filename}: {result}")
                    
                    # Create failed result
                    s3_key = f"{full_prefix}/{filename}".replace("//", "/")
                    result = UploadFileResult(
                        filename=filename,
                        s3_path=f"s3://{settings.s3_bucket_name}/{s3_key}",
                        status="failed",
                        error=str(result),
                        upload_time=datetime.now()
                    )
                
                results.append(result)
        
        # Calculate statistics
        successful_uploads = sum(1 for result in results if result.status == "success")
        failed_uploads = len(results) - successful_uploads
        
        # Determine overall status
        if successful_uploads == len(results):
            overall_status = "success"
        elif successful_uploads > 0:
            overall_status = "partial_success"
        else:
            overall_status = "failed"
        
        duration = (datetime.now() - start_time).total_seconds()
        summary = f"{successful_uploads} of {len(results)} files uploaded successfully in {duration:.2f} seconds"
        
        logger.info(f"Upload completed: {summary}")
        
        return UploadResponse(
            status=overall_status,
            summary=summary,
            uploaded_files=results,
            total_files=len(results),
            successful_uploads=successful_uploads,
            failed_uploads=failed_uploads,
            project_name=project_name,
            s3_prefix=s3_prefix
        )
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type for file based on extension"""
        import mimetypes
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"
    
    def __del__(self):
        """Cleanup thread pool on service destruction"""
        if hasattr(self, 'thread_pool'):
            self.thread_pool.shutdown(wait=False)
