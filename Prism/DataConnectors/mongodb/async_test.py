"""
Async MongoDB Connector Test Suite

This module provides comprehensive tests for the async MongoDB connector,
demonstrating its capabilities for large database operations including
aggregation pipelines, GridFS, text search, and geospatial queries.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any
import os
from datetime import datetime
from bson import ObjectId

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the async connector
try:
    from . import AsyncMongoDBConnector
except ImportError:
    try:
        from async_connector import AsyncMongoDBConnector
    except ImportError as e:
        logger.error(f"Failed to import AsyncMongoDBConnector: {e}")
        logger.info("Make sure to install required dependencies: pip install motor")
        exit(1)


class AsyncMongoDBTester:
    """Test suite for async MongoDB connector with large database scenarios."""

    def __init__(self, cleanup_data=False):
        self.connector = None
        self.test_collection = "async_test_collection"
        self.text_collection = "async_text_collection"
        self.geo_collection = "async_geo_collection"
        self.start_time = None
        self.cleanup_data = cleanup_data  # Control whether to clean up data after tests

    async def setup(self):
        """Initialize the async connector."""
        try:
            self.connector = AsyncMongoDBConnector(max_connections=50)
            logger.info("✅ Async MongoDB connector initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize connector: {e}")
            raise

    async def cleanup(self):
        """Clean up test resources."""
        try:
            if self.connector:
                if self.cleanup_data:
                    # Drop test collections only if cleanup is enabled
                    logger.info("🧹 Cleaning up test data...")
                    await self.connector.drop_collection(self.test_collection)
                    await self.connector.drop_collection(self.text_collection)
                    await self.connector.drop_collection(self.geo_collection)
                    logger.info("✅ Test data cleaned up")
                else:
                    logger.info("💾 Test data preserved in database")
                    logger.info(f"   Collections: {self.test_collection}, {self.text_collection}, {self.geo_collection}")

                await self.connector.close()
                logger.info("✅ Database connection closed")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

    async def test_basic_operations(self):
        """Test basic async database operations."""
        logger.info("🧪 Testing basic async operations...")

        try:
            # Test connection
            is_connected = await self.connector.test_connection()
            assert is_connected, "Connection test failed"
            logger.info("✅ Connection test passed")

            # Test single insert
            document = {
                "name": "John Doe",
                "email": "john@example.com",
                "age": 30,
                "created_at": datetime.now()
            }
            doc_id = await self.connector.insert_one(self.test_collection, document)
            assert doc_id, "Single insert failed"
            logger.info("✅ Single insert test passed")

            # Test find_one
            found_doc = await self.connector.find_one(
                self.test_collection,
                {"name": "John Doe"}
            )
            assert found_doc is not None, "Find one failed"
            assert found_doc['name'] == "John Doe", "Fetched data mismatch"
            logger.info("✅ Find one test passed")

            # Test find_by_id
            found_by_id = await self.connector.find_by_id(self.test_collection, doc_id)
            assert found_by_id is not None, "Find by ID failed"
            logger.info("✅ Find by ID test passed")

            # Test count_documents
            count = await self.connector.count_documents(self.test_collection)
            assert count >= 1, "Count documents failed"
            logger.info("✅ Count documents test passed")

        except Exception as e:
            logger.error(f"❌ Basic operations test failed: {e}")
            raise

    async def test_bulk_operations(self):
        """Test bulk operations for large datasets."""
        logger.info("🧪 Testing bulk operations...")

        try:
            # Generate test data
            test_data = [
                {
                    "name": f"User_{i}",
                    "email": f"user_{i}@example.com",
                    "age": 20 + (i % 50),
                    "department": f"Dept_{i % 10}",
                    "salary": 30000 + (i * 100),
                    "created_at": datetime.now()
                }
                for i in range(5000)
            ]

            # Test bulk insert with batching
            start_time = time.time()
            success = await self.connector.bulk_insert_with_batching(
                self.test_collection,
                test_data,
                batch_size=500
            )
            end_time = time.time()

            assert success, "Bulk insert failed"
            logger.info(f"✅ Bulk insert completed in {end_time - start_time:.2f} seconds")

            # Verify data count
            total_count = await self.connector.count_documents(self.test_collection)
            assert total_count >= 5000, f"Expected at least 5000 documents, got {total_count}"
            logger.info(f"✅ Verified {total_count} documents in database")

        except Exception as e:
            logger.error(f"❌ Bulk operations test failed: {e}")
            raise

    async def test_streaming_operations(self):
        """Test streaming operations for large result sets."""
        logger.info("🧪 Testing streaming operations...")

        try:
            total_streamed = 0
            chunk_count = 0

            # Stream large dataset
            async for chunk in self.connector.find_large_dataset(
                self.test_collection,
                filter_dict={"age": {"$gte": 25}},
                sort=[("name", 1)],
                chunk_size=500
            ):
                total_streamed += len(chunk)
                chunk_count += 1

                # Process chunk (simulate work)
                await asyncio.sleep(0.01)

            logger.info(f"✅ Streamed {total_streamed} documents in {chunk_count} chunks")
            assert total_streamed > 0, "No data streamed"

        except Exception as e:
            logger.error(f"❌ Streaming operations test failed: {e}")
            raise

    async def test_aggregation_operations(self):
        """Test aggregation pipeline operations."""
        logger.info("🧪 Testing aggregation operations...")

        try:
            # Test basic aggregation
            pipeline = [
                {"$match": {"age": {"$gte": 25}}},
                {"$group": {
                    "_id": "$department",
                    "avg_age": {"$avg": "$age"},
                    "avg_salary": {"$avg": "$salary"},
                    "count": {"$sum": 1}
                }},
                {"$sort": {"avg_salary": -1}},
                {"$limit": 5}
            ]

            results = await self.connector.aggregate(self.test_collection, pipeline)
            assert len(results) > 0, "Aggregation returned no results"
            logger.info(f"✅ Basic aggregation completed with {len(results)} results")

            # Test streaming aggregation for large results
            large_pipeline = [
                {"$match": {"age": {"$gte": 20}}},
                {"$project": {"name": 1, "age": 1, "department": 1}}
            ]

            total_agg_streamed = 0
            async for chunk in self.connector.aggregate_large_dataset(
                self.test_collection,
                large_pipeline,
                chunk_size=1000
            ):
                total_agg_streamed += len(chunk)

            logger.info(f"✅ Streamed aggregation completed with {total_agg_streamed} documents")

        except Exception as e:
            logger.error(f"❌ Aggregation operations test failed: {e}")
            raise

    async def test_text_search(self):
        """Test text search functionality."""
        logger.info("🧪 Testing text search...")

        try:
            # Create text search collection with sample data
            text_documents = [
                {"title": "Python Programming Guide", "content": "Learn Python programming with examples"},
                {"title": "MongoDB Database Tutorial", "content": "Complete guide to MongoDB database operations"},
                {"title": "Async Programming in Python", "content": "Master asynchronous programming with asyncio"},
                {"title": "Data Science with Python", "content": "Python for data analysis and machine learning"},
                {"title": "Web Development", "content": "Building web applications with modern frameworks"}
            ]

            await self.connector.insert_many(self.text_collection, text_documents)

            # Create text index
            await self.connector.create_index(
                self.text_collection,
                [("title", "text"), ("content", "text")]
            )

            # Perform text search
            search_results = await self.connector.text_search(
                self.text_collection,
                "Python programming",
                limit=3
            )

            assert len(search_results) > 0, "Text search returned no results"
            logger.info(f"✅ Text search completed with {len(search_results)} results")

        except Exception as e:
            logger.error(f"❌ Text search test failed: {e}")
            raise

    async def test_geospatial_operations(self):
        """Test geospatial query operations."""
        logger.info("🧪 Testing geospatial operations...")

        try:
            # Create geospatial collection with sample data
            geo_documents = [
                {
                    "name": "Central Park",
                    "location": {"type": "Point", "coordinates": [-73.9857, 40.7484]}
                },
                {
                    "name": "Times Square",
                    "location": {"type": "Point", "coordinates": [-73.9857, 40.7589]}
                },
                {
                    "name": "Brooklyn Bridge",
                    "location": {"type": "Point", "coordinates": [-73.9969, 40.7061]}
                }
            ]

            await self.connector.insert_many(self.geo_collection, geo_documents)

            # Create geospatial index
            await self.connector.create_index(
                self.geo_collection,
                [("location", "2dsphere")]
            )

            # Perform geospatial search (near Central Park)
            geo_results = await self.connector.geospatial_search(
                self.geo_collection,
                "location",
                [-73.9857, 40.7484],  # Central Park coordinates
                max_distance=2000,    # 2km radius
                limit=5
            )

            assert len(geo_results) > 0, "Geospatial search returned no results"
            logger.info(f"✅ Geospatial search completed with {len(geo_results)} results")

        except Exception as e:
            logger.error(f"❌ Geospatial operations test failed: {e}")
            raise

    async def test_concurrent_operations(self):
        """Test concurrent operation execution."""
        logger.info("🧪 Testing concurrent operations...")

        try:
            # Define concurrent operations
            operations = [
                {
                    'type': 'count_documents',
                    'collection': self.test_collection,
                    'args': {'filter_dict': {'age': {'$gte': 30}}}
                },
                {
                    'type': 'find_one',
                    'collection': self.test_collection,
                    'args': {'filter_dict': {'name': 'User_1'}}
                },
                {
                    'type': 'distinct',
                    'collection': self.test_collection,
                    'args': {'field': 'department'}
                },
                {
                    'type': 'count_documents',
                    'collection': self.text_collection,
                    'args': {}
                }
            ]

            start_time = time.time()
            results = await self.connector.execute_concurrent_operations(
                operations,
                max_concurrent=4
            )
            end_time = time.time()

            assert len(results) == 4, "Not all concurrent operations completed"
            logger.info(f"✅ Concurrent operations completed in {end_time - start_time:.2f} seconds")

        except Exception as e:
            logger.error(f"❌ Concurrent operations test failed: {e}")
            raise

    async def test_gridfs_operations(self):
        """Test GridFS file storage operations."""
        logger.info("🧪 Testing GridFS operations...")

        try:
            # Test file upload
            test_file_content = b"This is a test file for GridFS storage operations."
            file_id = await self.connector.gridfs_put(
                test_file_content,
                "test_file.txt",
                content_type="text/plain",
                author="test_user"
            )

            assert file_id, "GridFS file upload failed"
            logger.info("✅ GridFS file upload test passed")

            # Test file download
            downloaded_content = await self.connector.gridfs_get(file_id)
            assert downloaded_content == test_file_content, "Downloaded content mismatch"
            logger.info("✅ GridFS file download test passed")

            # Test file deletion
            deleted = await self.connector.gridfs_delete(file_id)
            assert deleted, "GridFS file deletion failed"
            logger.info("✅ GridFS file deletion test passed")

        except Exception as e:
            logger.error(f"❌ GridFS operations test failed: {e}")
            raise

    async def test_database_stats(self):
        """Test database statistics and monitoring."""
        logger.info("🧪 Testing database statistics...")

        try:
            # Test database stats
            db_stats = await self.connector.get_database_stats()
            assert 'collections' in db_stats, "Database stats missing collections info"
            logger.info(f"✅ Database stats: {db_stats.get('collections', 0)} collections")

            # Test collection stats
            collection_stats = await self.connector.get_collection_stats(self.test_collection)
            assert 'count' in collection_stats, "Collection stats missing count info"
            logger.info(f"✅ Collection stats: {collection_stats.get('count', 0)} documents")

            # Test collection management
            collections = await self.connector.get_collection_names()
            assert self.test_collection in collections, "Test collection not found in list"
            logger.info(f"✅ Found {len(collections)} collections")

        except Exception as e:
            logger.error(f"❌ Database stats test failed: {e}")
            raise

    async def show_data_summary(self):
        """Show summary of data created during tests."""
        try:
            logger.info("")
            logger.info("📊 DATA SUMMARY")
            logger.info("=" * 40)

            # Get collection counts
            test_count = await self.connector.count_documents(self.test_collection)
            text_count = await self.connector.count_documents(self.text_collection)
            geo_count = await self.connector.count_documents(self.geo_collection)

            logger.info(f"📄 {self.test_collection}: {test_count} documents")
            logger.info(f"   - User data with departments, ages, salaries")
            logger.info(f"   - Sample queries: age >= 30, department = 'Dept_1'")

            logger.info(f"📄 {self.text_collection}: {text_count} documents")
            logger.info(f"   - Articles with text search index")
            logger.info(f"   - Try text search: 'Python programming'")

            logger.info(f"📄 {self.geo_collection}: {geo_count} documents")
            logger.info(f"   - Locations with 2dsphere index")
            logger.info(f"   - Try geospatial queries near coordinates")

            logger.info("")
            logger.info("🔍 SAMPLE MONGODB QUERIES:")
            logger.info(f"db.{self.test_collection}.find({{age: {{$gte: 30}}}}).limit(5)")
            logger.info(f"db.{self.test_collection}.aggregate([{{$group: {{_id: '$department', count: {{$sum: 1}}}}}}])")
            logger.info(f"db.{self.text_collection}.find({{$text: {{$search: 'Python'}}}})")
            logger.info(f"db.{self.geo_collection}.find({{location: {{$near: {{$geometry: {{type: 'Point', coordinates: [-73.9857, 40.7484]}}}}}}}}).limit(3)")

            if not self.cleanup_data:
                logger.info("")
                logger.info("💡 TIP: Connect to your MongoDB and explore this data!")
                logger.info("   The collections will remain in your database for exploration.")

        except Exception as e:
            logger.error(f"❌ Failed to show data summary: {e}")

    async def run_all_tests(self):
        """Run all async MongoDB connector tests."""
        logger.info("🚀 Starting Async MongoDB Connector Test Suite")
        logger.info("=" * 60)

        self.start_time = time.time()

        try:
            await self.setup()

            # Run test categories
            test_methods = [
                self.test_basic_operations,
                self.test_bulk_operations,
                self.test_streaming_operations,
                self.test_aggregation_operations,
                self.test_text_search,
                self.test_geospatial_operations,
                self.test_concurrent_operations,
                self.test_gridfs_operations,
                self.test_database_stats
            ]

            for test_method in test_methods:
                try:
                    await test_method()
                except Exception as e:
                    logger.error(f"❌ Test {test_method.__name__} failed: {e}")
                    raise

            end_time = time.time()
            logger.info("=" * 60)
            logger.info(f"🎉 All tests completed successfully in {end_time - self.start_time:.2f} seconds")

            # Show data summary
            await self.show_data_summary()

        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            raise
        finally:
            await self.cleanup()


async def main():
    """Main test runner."""
    # Check environment variables
    required_env_vars = ['MONGO_HOST', 'MONGO_DB']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars and not os.getenv('MONGO_URI'):
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.info("Please set either MONGO_URI or individual connection parameters:")
        logger.info("  MONGO_HOST=localhost")
        logger.info("  MONGO_DB=test_database")
        logger.info("  MONGO_USERNAME=username (optional)")
        logger.info("  MONGO_PASSWORD=password (optional)")
        logger.info("Or:")
        logger.info("  MONGO_URI=mongodb://localhost:27017/test_database")
        return

    # Check if user wants to clean up data (default: keep data)
    cleanup = os.getenv('CLEANUP_DATA', 'false').lower() == 'true'

    if cleanup:
        logger.info("🧹 Data cleanup is ENABLED - test data will be removed after tests")
    else:
        logger.info("💾 Data cleanup is DISABLED - test data will be preserved")
        logger.info("   Set CLEANUP_DATA=true environment variable to enable cleanup")

    tester = AsyncMongoDBTester(cleanup_data=cleanup)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
