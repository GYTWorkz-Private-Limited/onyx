"""
Ultra-optimized AWS Lambda handler for S3 event notifications
Minimal code for maximum efficiency
"""
import json
import os
import urllib.request
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

API_ENDPOINT = os.environ.get("API_ENDPOINT", "http://localhost:8888")


def lambda_handler(event, _):
    """Forward S3 events to DataSync service"""
    try:
        records_count = len(event.get('Records', []))
        logger.info(f"Forwarding {records_count} S3 records to DataSync")

        # Forward to DataSync service
        urllib.request.urlopen(
            urllib.request.Request(
                url=f"{API_ENDPOINT}/sync/s3-notification",
                data=json.dumps(event).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            ),
            timeout=30
        )

        logger.info("Successfully forwarded S3 event")
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'success', 'records': records_count})
        }

    except Exception as e:
        logger.error(f"Failed to forward S3 event: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }
