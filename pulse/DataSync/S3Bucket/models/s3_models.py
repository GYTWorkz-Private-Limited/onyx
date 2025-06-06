"""
Optimized Pydantic models for S3 Sync Service
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class S3Object(BaseModel):
    """S3 object information"""
    key: str
    size: int
    eTag: str
    sequencer: Optional[str] = None


class S3Bucket(BaseModel):
    """S3 bucket information"""
    name: str
    ownerIdentity: Dict[str, str]
    arn: str


class S3Info(BaseModel):
    """S3 event information"""
    s3SchemaVersion: str
    configurationId: str
    bucket: S3Bucket
    object: S3Object


class S3EventRecord(BaseModel):
    """Individual S3 event record"""
    eventVersion: str
    eventSource: str
    awsRegion: str
    eventTime: str
    eventName: str
    userIdentity: Dict[str, Any]
    requestParameters: Dict[str, str]
    responseElements: Dict[str, str]
    s3: S3Info


class S3NotificationEvent(BaseModel):
    """S3 notification event with multiple records"""
    Records: List[S3EventRecord]


class SyncStatus(BaseModel):
    """Sync operation status"""
    operation: str  # download/delete/skip/error
    file_key: str
    status: str  # success/failed/pending/skipped
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class SyncResponse(BaseModel):
    """Sync operation response"""
    status: str
    message: str
    processed_files: int
    successful_operations: int
    failed_operations: int
    sync_details: List[SyncStatus]
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
