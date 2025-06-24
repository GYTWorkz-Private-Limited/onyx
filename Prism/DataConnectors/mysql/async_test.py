"""
Async MySQL Connector Test Suite

This module provides comprehensive tests for the async MySQL connector,
demonstrating its capabilities for large database operations.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the async connector
try:
    from . import AsyncMySQLConnector
except ImportError:
    try:
        from async_connector import AsyncMySQLConnector
    except ImportError as e:
        logger.error(f"Failed to import AsyncMySQLConnector: {e}")
        logger.info("Make sure to install required dependencies: pip install aiomysql")
        exit(1)


class AsyncMySQLTester:
    """Test suite for async MySQL connector with large database scenarios."""

    def __init__(self):
        self.connector = None
        self.test_table = "async_test_table"
        self.start_time = None

    async def setup(self):
        """Initialize the async connector."""
        try:
            self.connector = AsyncMySQLConnector(max_connections=20)
            logger.info("✅ Async MySQL connector initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize connector: {e}")
            raise

    async def cleanup(self):
        """Clean up test resources."""
        try:
            if self.connector:
                # Drop test table
                await self.connector.execute(f"DROP TABLE IF EXISTS {self.test_table}")
                await self.connector.close()
            logger.info("✅ Cleanup completed")
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

            # Create test table
            create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {self.test_table} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_name (name),
                    INDEX idx_email (email)
                )
            """
            await self.connector.execute(create_table_query)
            logger.info("✅ Test table created")

            # Test single insert
            insert_query = f"INSERT INTO {self.test_table} (name, email) VALUES (%s, %s)"
            result = await self.connector.execute(insert_query, ("John Doe", "john@example.com"))
            assert result == 1, "Single insert failed"
            logger.info("✅ Single insert test passed")

            # Test fetch_one
            user = await self.connector.fetch_one(
                f"SELECT * FROM {self.test_table} WHERE name = %s",
                ("John Doe",)
            )
            assert user is not None, "Fetch one failed"
            assert user['name'] == "John Doe", "Fetched data mismatch"
            logger.info("✅ Fetch one test passed")

            # Test fetch_all
            users = await self.connector.fetch_all(f"SELECT * FROM {self.test_table}")
            assert len(users) >= 1, "Fetch all failed"
            logger.info("✅ Fetch all test passed")

        except Exception as e:
            logger.error(f"❌ Basic operations test failed: {e}")
            raise

    async def test_bulk_operations(self):
        """Test bulk operations for large datasets."""
        logger.info("🧪 Testing bulk operations...")

        try:
            # Generate test data
            test_data = [
                {"name": f"User_{i}", "email": f"user_{i}@example.com"}
                for i in range(1000)
            ]

            # Test bulk insert
            start_time = time.time()
            success = await self.connector.bulk_insert(
                self.test_table,
                test_data,
                batch_size=100
            )
            end_time = time.time()

            assert success, "Bulk insert failed"
            logger.info(f"✅ Bulk insert completed in {end_time - start_time:.2f} seconds")

            # Verify data count
            count_result = await self.connector.fetch_one(
                f"SELECT COUNT(*) as total FROM {self.test_table}"
            )
            total_count = count_result['total']
            assert total_count >= 1000, f"Expected at least 1000 records, got {total_count}"
            logger.info(f"✅ Verified {total_count} records in database")

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
            async for chunk in self.connector.fetch_large_dataset(
                f"SELECT * FROM {self.test_table} ORDER BY id",
                chunk_size=100
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

    async def test_concurrent_operations(self):
        """Test concurrent query execution."""
        logger.info("🧪 Testing concurrent operations...")

        try:
            # Define concurrent queries
            queries = [
                {
                    'query': f'SELECT COUNT(*) as count FROM {self.test_table}',
                    'params': (),
                    'type': 'fetch_one'
                },
                {
                    'query': f'SELECT * FROM {self.test_table} WHERE id = %s',
                    'params': (1,),
                    'type': 'fetch_one'
                },
                {
                    'query': f'SELECT name FROM {self.test_table} LIMIT 5',
                    'params': (),
                    'type': 'fetch_all'
                }
            ]

            start_time = time.time()
            results = await self.connector.execute_concurrent_queries(
                queries,
                max_concurrent=3
            )
            end_time = time.time()

            assert len(results) == 3, "Not all concurrent queries completed"
            logger.info(f"✅ Concurrent queries completed in {end_time - start_time:.2f} seconds")

        except Exception as e:
            logger.error(f"❌ Concurrent operations test failed: {e}")
            raise

    async def test_transaction_operations(self):
        """Test transaction handling."""
        logger.info("🧪 Testing transaction operations...")

        try:
            # Test successful transaction
            operations = [
                {
                    'query': f'INSERT INTO {self.test_table} (name, email) VALUES (%s, %s)',
                    'params': ('Transaction User 1', 'trans1@example.com')
                },
                {
                    'query': f'INSERT INTO {self.test_table} (name, email) VALUES (%s, %s)',
                    'params': ('Transaction User 2', 'trans2@example.com')
                }
            ]

            success = await self.connector.execute_transaction(operations)
            assert success, "Transaction failed"
            logger.info("✅ Transaction test passed")

            # Test transaction context manager
            async with self.connector.transaction() as cursor:
                await cursor.execute(
                    f'INSERT INTO {self.test_table} (name, email) VALUES (%s, %s)',
                    ('Context User', 'context@example.com')
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

            assert 'database_size_mb' in stats, "Database size not in stats"
            assert 'table_count' in stats, "Table count not in stats"
            assert 'active_connections' in stats, "Active connections not in stats"

            logger.info(f"✅ Database stats: {stats}")

            # Test table info
            table_info = await self.connector.get_table_info(self.test_table)
            assert 'columns' in table_info, "Columns not in table info"
            assert 'indexes' in table_info, "Indexes not in table info"

            logger.info("✅ Table info test passed")

        except Exception as e:
            logger.error(f"❌ Database stats test failed: {e}")
            raise

    async def run_all_tests(self):
        """Run all async MySQL connector tests."""
        logger.info("🚀 Starting Async MySQL Connector Test Suite")
        logger.info("=" * 60)

        self.start_time = time.time()

        try:
            await self.setup()

            # Run test categories
            test_methods = [
                self.test_basic_operations,
                self.test_bulk_operations,
                self.test_streaming_operations,
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
        finally:
            await self.cleanup()


async def main():
    """Main test runner."""
    # Check environment variables
    required_env_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DB']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.info("Please set the following environment variables:")
        for var in missing_vars:
            logger.info(f"  export {var}=your_value")
        return

    tester = AsyncMySQLTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
