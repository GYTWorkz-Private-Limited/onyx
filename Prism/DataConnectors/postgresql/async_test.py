"""
Async PostgreSQL Connector Test Suite

This module provides comprehensive tests for the async PostgreSQL connector,
demonstrating its capabilities for large database operations including
COPY operations, JSON/JSONB support, and advanced PostgreSQL features.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any
import os
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the async connector
try:
    from . import AsyncPostgreSQLConnector
except ImportError:
    try:
        from async_connector import AsyncPostgreSQLConnector
    except ImportError as e:
        logger.error(f"Failed to import AsyncPostgreSQLConnector: {e}")
        logger.info("Make sure to install required dependencies: pip install asyncpg")
        exit(1)


class AsyncPostgreSQLTester:
    """Test suite for async PostgreSQL connector with large database scenarios."""

    def __init__(self):
        self.connector = None
        self.test_table = "async_test_table"
        self.json_test_table = "async_json_test_table"
        self.start_time = None

    async def setup(self):
        """Initialize the async connector."""
        try:
            self.connector = AsyncPostgreSQLConnector(max_connections=20)
            logger.info("✅ Async PostgreSQL connector initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize connector: {e}")
            raise

    # async def cleanup(self):
    #     """Clean up test resources."""
    #     try:
    #         if self.connector:
    #             # Drop test tables
    #             await self.connector.execute(f"DROP TABLE IF EXISTS {self.test_table}")
    #             await self.connector.execute(f"DROP TABLE IF EXISTS {self.json_test_table}")
    #             await self.connector.close()
    #         logger.info("✅ Cleanup completed")
    #     except Exception as e:
    #         logger.error(f"❌ Cleanup failed: {e}")

    async def test_basic_operations(self):
        """Test basic async database operations."""
        logger.info("🧪 Testing basic async operations...")

        try:
            # Test connection
            is_connected = await self.connector.test_connection()
            assert is_connected, "Connection test failed"
            logger.info("✅ Connection test passed")

            # Create test table
            create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {self.test_table} (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100),
                    age INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            await self.connector.execute(create_table_query)
            logger.info("✅ Test table created")

            # Test single insert
            insert_query = f"INSERT INTO {self.test_table} (name, email, age) VALUES ($1, $2, $3)"
            result = await self.connector.execute(insert_query, "John Doe", "john@example.com", 30)
            assert "INSERT" in result, "Single insert failed"
            logger.info("✅ Single insert test passed")

            # Test fetch_one
            user = await self.connector.fetch_one(
                f"SELECT * FROM {self.test_table} WHERE name = $1",
                "John Doe"
            )
            assert user is not None, "Fetch one failed"
            assert user['name'] == "John Doe", "Fetched data mismatch"
            logger.info("✅ Fetch one test passed")

            # Test fetch_val
            count = await self.connector.fetch_val(f"SELECT COUNT(*) FROM {self.test_table}")
            assert count >= 1, "Fetch val failed"
            logger.info("✅ Fetch val test passed")

            # Test fetch_all
            users = await self.connector.fetch_all(f"SELECT * FROM {self.test_table}")
            assert len(users) >= 1, "Fetch all failed"
            logger.info("✅ Fetch all test passed")

        except Exception as e:
            logger.error(f"❌ Basic operations test failed: {e}")
            raise

    async def test_copy_operations(self):
        """Test PostgreSQL COPY operations for ultra-fast bulk inserts."""
        logger.info("🧪 Testing COPY operations...")

        try:
            # Generate test data
            test_data = [
                {"name": f"User_{i}", "email": f"user_{i}@example.com", "age": 20 + (i % 50)}
                for i in range(5000)
            ]

            # Test COPY bulk insert
            start_time = time.time()
            copied_count = await self.connector.copy_records_to_table(
                self.test_table,
                test_data
            )
            end_time = time.time()

            assert copied_count == 5000, f"Expected 5000 records, got {copied_count}"
            logger.info(f"✅ COPY operation completed in {end_time - start_time:.2f} seconds")
            logger.info(f"   Inserted {copied_count} records using COPY")

            # Verify data count
            total_count = await self.connector.fetch_val(
                f"SELECT COUNT(*) FROM {self.test_table}"
            )
            assert total_count >= 5000, f"Expected at least 5000 records, got {total_count}"
            logger.info(f"✅ Verified {total_count} records in database")

        except Exception as e:
            logger.error(f"❌ COPY operations test failed: {e}")
            raise

    async def test_streaming_operations(self):
        """Test streaming operations for large result sets."""
        logger.info("🧪 Testing streaming operations...")

        try:
            total_streamed = 0
            chunk_count = 0

            # Stream large dataset
            async for chunk in self.connector.fetch_large_dataset(
                f"SELECT * FROM {self.test_table} ORDER BY id",
                chunk_size=500
            ):
                total_streamed += len(chunk)
                chunk_count += 1

                # Process chunk (simulate work)
                await asyncio.sleep(0.01)

            logger.info(f"✅ Streamed {total_streamed} records in {chunk_count} chunks")
            assert total_streamed > 0, "No data streamed"

        except Exception as e:
            logger.error(f"❌ Streaming operations test failed: {e}")
            raise

    async def test_json_operations(self):
        """Test JSON/JSONB operations."""
        logger.info("🧪 Testing JSON/JSONB operations...")

        try:
            # Create JSON test table
            create_json_table = f"""
                CREATE TABLE IF NOT EXISTS {self.json_test_table} (
                    id SERIAL PRIMARY KEY,
                    user_data JSONB,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            await self.connector.execute(create_json_table)

            # Test JSON insert
            user_data = {
                "name": "Alice Johnson",
                "profile": {
                    "age": 28,
                    "skills": ["Python", "PostgreSQL", "Docker"],
                    "location": {"city": "San Francisco", "country": "USA"}
                },
                "preferences": {"theme": "dark", "notifications": True}
            }

            metadata = {"source": "api", "version": "1.0", "tags": ["user", "profile"]}

            result = await self.connector.insert_json(
                self.json_test_table,
                "user_data",
                user_data,
                metadata=json.dumps(metadata)
            )
            assert "INSERT" in result, "JSON insert failed"
            logger.info("✅ JSON insert test passed")

            # Test JSON query
            results = await self.connector.query_json(
                self.json_test_table,
                "user_data",
                "$.profile.location.city",
                "San Francisco"
            )
            assert len(results) > 0, "JSON query failed"
            logger.info("✅ JSON query test passed")

            # Test complex JSON query
            complex_query = f"""
                SELECT id, user_data->'name' as name,
                       user_data->'profile'->'skills' as skills
                FROM {self.json_test_table}
                WHERE user_data->'profile'->>'age' = '28'
            """
            complex_results = await self.connector.fetch_all(complex_query)
            assert len(complex_results) > 0, "Complex JSON query failed"
            logger.info("✅ Complex JSON query test passed")

        except Exception as e:
            logger.error(f"❌ JSON operations test failed: {e}")
            raise

    async def test_concurrent_operations(self):
        """Test concurrent query execution."""
        logger.info("🧪 Testing concurrent operations...")

        try:
            # Define concurrent queries
            queries = [
                {
                    'query': f'SELECT COUNT(*) FROM {self.test_table}',
                    'args': (),
                    'type': 'fetch_val'
                },
                {
                    'query': f'SELECT * FROM {self.test_table} WHERE id = $1',
                    'args': (1,),
                    'type': 'fetch_one'
                },
                {
                    'query': f'SELECT name FROM {self.test_table} LIMIT 5',
                    'args': (),
                    'type': 'fetch_all'
                },
                {
                    'query': f'SELECT AVG(age) FROM {self.test_table}',
                    'args': (),
                    'type': 'fetch_val'
                }
            ]

            start_time = time.time()
            results = await self.connector.execute_concurrent_queries(
                queries,
                max_concurrent=4
            )
            end_time = time.time()

            assert len(results) == 4, "Not all concurrent queries completed"
            logger.info(f"✅ Concurrent queries completed in {end_time - start_time:.2f} seconds")

        except Exception as e:
            logger.error(f"❌ Concurrent operations test failed: {e}")
            raise

    async def test_transaction_operations(self):
        """Test transaction handling with savepoints."""
        logger.info("🧪 Testing transaction operations...")

        try:
            # Test successful transaction
            operations = [
                {
                    'query': f'INSERT INTO {self.test_table} (name, email, age) VALUES ($1, $2, $3)',
                    'args': ('Transaction User 1', 'trans1@example.com', 25)
                },
                {
                    'query': f'INSERT INTO {self.test_table} (name, email, age) VALUES ($1, $2, $3)',
                    'args': ('Transaction User 2', 'trans2@example.com', 30)
                }
            ]

            success = await self.connector.execute_transaction(operations)
            assert success, "Transaction failed"
            logger.info("✅ Transaction test passed")

            # Test transaction context manager
            async with self.connector.transaction() as conn:
                await conn.execute(
                    f'INSERT INTO {self.test_table} (name, email, age) VALUES ($1, $2, $3)',
                    'Context User', 'context@example.com', 35
                )
            logger.info("✅ Transaction context manager test passed")

        except Exception as e:
            logger.error(f"❌ Transaction operations test failed: {e}")
            raise

    async def test_database_stats(self):
        """Test database statistics and monitoring."""
        logger.info("🧪 Testing database statistics...")

        try:
            stats = await self.connector.get_database_stats()

            required_keys = ['database_size', 'table_count', 'active_connections', 'cache_hit_ratio']
            for key in required_keys:
                assert key in stats, f"{key} not in stats"

            logger.info(f"✅ Database stats: {stats}")

            # Test table info
            table_info = await self.connector.get_table_info(self.test_table)
            assert 'columns' in table_info, "Columns not in table info"
            assert 'indexes' in table_info, "Indexes not in table info"
            assert 'size_info' in table_info, "Size info not in table info"

            logger.info("✅ Table info test passed")

        except Exception as e:
            logger.error(f"❌ Database stats test failed: {e}")
            raise

    async def run_all_tests(self):
        """Run all async PostgreSQL connector tests."""
        logger.info("🚀 Starting Async PostgreSQL Connector Test Suite")
        logger.info("=" * 60)

        self.start_time = time.time()

        try:
            await self.setup()

            # Run test categories
            test_methods = [
                self.test_basic_operations,
                self.test_copy_operations,
                self.test_streaming_operations,
                self.test_json_operations,
                self.test_concurrent_operations,
                self.test_transaction_operations,
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

        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            raise
        # finally:
        #     await self.cleanup()


async def main():
    """Main test runner."""
    # Check environment variables
    required_env_vars = ['POSTGRES_HOST', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.info("Please set the following environment variables:")
        for var in missing_vars:
            logger.info(f"  export {var}=your_value")
        return

    tester = AsyncPostgreSQLTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
