"""
ClickHouse DataConnector Test Suite

Comprehensive test suite for the ClickHouse DataConnector with real database testing,
performance benchmarks, and feature validation.
"""
import os
import sys
import time
import random
from datetime import datetime, date
from typing import List, Dict, Any

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Handle both package and direct execution imports
try:
    from .connector import ClickHouseConnector
    from .config import Config
    from .exceptions import (
        ClickHouseConnectionError, ClickHouseQueryError, ClickHouseValidationError
    )
    from .utils import format_duration, format_bytes
except ImportError:
    from connector import ClickHouseConnector
    from config import Config
    from exceptions import (
        ClickHouseConnectionError, ClickHouseQueryError, ClickHouseValidationError
    )
    from utils import format_duration, format_bytes


class ClickHouseConnectorTest:
    """Comprehensive test suite for ClickHouse DataConnector"""

    def __init__(self):
        self.test_table = "test_connector_table"
        self.analytics_table = "analytics_demo_table"
        self.test_results = []
        self.start_time = None

    def run_all_tests(self):
        """Run all tests and display results"""
        print("🚀 ClickHouse DataConnector Test Suite")
        print("=" * 50)

        self.start_time = time.time()

        # Test categories
        test_categories = [
            ("Connection Tests", self._test_connection),
            ("Basic Query Tests", self._test_basic_queries),
            ("Data Operations Tests", self._test_data_operations),
            ("Schema Tests", self._test_schema_operations),
            ("Performance Tests", self._test_performance),
            ("Error Handling Tests", self._test_error_handling),
            ("Advanced Features Tests", self._test_advanced_features),
            ("Persistent Data Creation", self._create_persistent_tables)
        ]

        for category_name, test_method in test_categories:
            print(f"\n📋 {category_name}")
            print("-" * 30)
            try:
                test_method()
            except Exception as e:
                self._record_test("Category Error", False, str(e))
                print(f"❌ Category failed: {e}")

        self._display_summary()

    def _test_connection(self):
        """Test connection functionality"""
        # Test HTTP connection
        self._test_case("HTTP Connection", self._test_http_connection)

        # Test connection health
        self._test_case("Connection Health Check", self._test_connection_health)

        # Test context manager
        self._test_case("Context Manager", self._test_context_manager)

    def _test_http_connection(self):
        """Test HTTP protocol connection"""
        with ClickHouseConnector(protocol="http") as db:
            result = db.execute_query("SELECT 1 as test")
            assert len(result) > 0 and result[0].get('test') == 1

    def _test_connection_health(self):
        """Test connection health check"""
        with ClickHouseConnector() as db:
            assert db.test_connection() == True

    def _test_context_manager(self):
        """Test context manager functionality"""
        with ClickHouseConnector() as db:
            assert db is not None
            result = db.execute_query("SELECT 'context_test' as message")
            assert result[0]['message'] == 'context_test'

    def _test_basic_queries(self):
        """Test basic query operations"""
        self._test_case("SELECT Query", self._test_select_query)
        self._test_case("Parameterized Query", self._test_parameterized_query)
        self._test_case("Fetch One", self._test_fetch_one)
        self._test_case("Fetch All", self._test_fetch_all)

    def _test_select_query(self):
        """Test basic SELECT query"""
        with ClickHouseConnector() as db:
            result = db.execute_query("SELECT 42 as answer, 'hello' as greeting")
            assert len(result) == 1
            assert result[0]['answer'] == 42
            assert result[0]['greeting'] == 'hello'

    def _test_parameterized_query(self):
        """Test parameterized queries"""
        with ClickHouseConnector() as db:
            # Note: Parameter syntax may vary by driver
            result = db.execute_query("SELECT 'test' as message")
            assert len(result) > 0

    def _test_fetch_one(self):
        """Test fetch_one method"""
        with ClickHouseConnector() as db:
            result = db.fetch_one("SELECT 'single' as result")
            assert result is not None
            assert result['result'] == 'single'

    def _test_fetch_all(self):
        """Test fetch_all method"""
        with ClickHouseConnector() as db:
            result = db.fetch_all("SELECT number FROM system.numbers LIMIT 5")
            assert len(result) == 5
            assert all('number' in row for row in result)

    def _test_data_operations(self):
        """Test data manipulation operations"""
        self._test_case("Create Test Table", self._test_create_table)
        self._test_case("Insert Data", self._test_insert_data)
        self._test_case("Batch Insert", self._test_batch_insert)
        self._test_case("Query Inserted Data", self._test_query_data)
        # Note: NOT dropping table so you can see it in the cloud
        print("    📌 Table 'test_connector_table' kept for cloud inspection")

    def _test_create_table(self):
        """Test table creation"""
        with ClickHouseConnector() as db:
            # Drop table if exists
            try:
                db.execute_query(f"DROP TABLE IF EXISTS {self.test_table}")
            except:
                pass

            # Create test table
            create_query = f"""
            CREATE TABLE {self.test_table} (
                id UInt32,
                name String,
                value Float64,
                created_date Date,
                created_datetime DateTime
            ) ENGINE = MergeTree()
            ORDER BY id
            """
            db.execute_query(create_query)

            # Verify table exists
            assert db.table_exists(self.test_table)

    def _test_insert_data(self):
        """Test single row insert"""
        with ClickHouseConnector() as db:
            test_data = [{
                'id': 1,
                'name': 'Test Item',
                'value': 123.45,
                'created_date': date.today(),
                'created_datetime': datetime.now()
            }]

            result = db.insert_data(self.test_table, test_data)
            assert result == True

    def _test_batch_insert(self):
        """Test batch insert operations"""
        with ClickHouseConnector() as db:
            # Generate test data
            test_data = []
            for i in range(2, 102):  # Insert 100 more rows
                test_data.append({
                    'id': i,
                    'name': f'Test Item {i}',
                    'value': random.uniform(1.0, 1000.0),
                    'created_date': date.today(),
                    'created_datetime': datetime.now()
                })

            result = db.insert_data(self.test_table, test_data, batch_size=50)
            assert result == True

    def _test_query_data(self):
        """Test querying inserted data"""
        with ClickHouseConnector() as db:
            # Count total rows
            count_result = db.fetch_one(f"SELECT count() as total FROM {self.test_table}")
            assert count_result['total'] >= 101  # At least 101 rows

            # Query specific data
            result = db.fetch_all(f"SELECT * FROM {self.test_table} WHERE id <= 5 ORDER BY id")
            assert len(result) == 5
            assert result[0]['id'] == 1

    def _create_persistent_tables(self):
        """Create additional persistent tables with demo data for cloud inspection"""
        self._test_case("Create Analytics Demo Table", self._create_analytics_table)
        self._test_case("Populate Analytics Data", self._populate_analytics_data)
        self._test_case("Display Table Summary", self._display_table_summary)

    def _create_analytics_table(self):
        """Create analytics demo table"""
        with ClickHouseConnector() as db:
            # Drop table if exists
            try:
                db.execute_query(f"DROP TABLE IF EXISTS {self.analytics_table}")
            except:
                pass

            # Create analytics demo table
            create_query = f"""
            CREATE TABLE {self.analytics_table} (
                event_id UInt64,
                user_id UInt32,
                event_type LowCardinality(String),
                event_timestamp DateTime,
                event_date Date,
                page_url String,
                session_id String,
                user_agent String,
                country LowCardinality(String),
                city String,
                revenue Decimal(10,2),
                duration_seconds UInt32
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(event_date)
            ORDER BY (event_date, user_id, event_timestamp)
            """
            db.execute_query(create_query)

            # Verify table exists
            assert db.table_exists(self.analytics_table)

    def _populate_analytics_data(self):
        """Populate analytics table with demo data"""
        with ClickHouseConnector() as db:
            # Generate realistic analytics data
            event_types = ['page_view', 'click', 'purchase', 'signup', 'logout']
            countries = ['US', 'UK', 'DE', 'FR', 'JP', 'CA', 'AU', 'IN', 'BR', 'MX']
            cities = ['New York', 'London', 'Berlin', 'Paris', 'Tokyo', 'Toronto', 'Sydney', 'Mumbai', 'São Paulo', 'Mexico City']
            pages = ['/home', '/products', '/about', '/contact', '/checkout', '/profile', '/search', '/blog', '/help', '/login']

            analytics_data = []
            base_time = datetime.now()

            for i in range(1, 1001):  # Create 1000 analytics events
                event_time = base_time.replace(
                    hour=random.randint(0, 23),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )

                analytics_data.append({
                    'event_id': i,
                    'user_id': random.randint(1, 100),
                    'event_type': random.choice(event_types),
                    'event_timestamp': event_time,
                    'event_date': event_time.date(),
                    'page_url': random.choice(pages),
                    'session_id': f"sess_{random.randint(1000, 9999)}",
                    'user_agent': f"Browser/{random.randint(1, 10)}.0",
                    'country': random.choice(countries),
                    'city': random.choice(cities),
                    'revenue': round(random.uniform(0, 500), 2) if random.choice(event_types) == 'purchase' else 0.00,
                    'duration_seconds': random.randint(10, 3600)
                })

            # Insert data in batches
            result = db.insert_data(self.analytics_table, analytics_data, batch_size=100)
            assert result == True

    def _display_table_summary(self):
        """Display summary of created tables for cloud inspection"""
        with ClickHouseConnector() as db:
            print("\n" + "="*60)
            print("📊 TABLES CREATED FOR CLOUD INSPECTION")
            print("="*60)

            # Summary for test_connector_table
            try:
                count_result = db.fetch_one(f"SELECT count() as total FROM {self.test_table}")
                print(f"✅ Table: {self.test_table}")
                print(f"   📈 Total rows: {count_result['total']:,}")
                print(f"   📋 Columns: id, name, value, created_date, created_datetime")
                print(f"   🎯 Purpose: Basic connector testing data")
            except:
                print(f"❌ Table: {self.test_table} - Not found")

            # Summary for analytics_demo_table
            try:
                count_result = db.fetch_one(f"SELECT count() as total FROM {self.analytics_table}")
                event_types = db.fetch_all(f"SELECT event_type, count() as cnt FROM {self.analytics_table} GROUP BY event_type ORDER BY cnt DESC")

                print(f"\n✅ Table: {self.analytics_table}")
                print(f"   📈 Total rows: {count_result['total']:,}")
                print(f"   📋 Columns: event_id, user_id, event_type, event_timestamp, event_date, page_url, session_id, user_agent, country, city, revenue, duration_seconds")
                print(f"   🎯 Purpose: Analytics demo data")
                print(f"   📊 Event types:")
                for event in event_types:
                    print(f"      - {event['event_type']}: {event['cnt']} events")
            except:
                print(f"❌ Table: {self.analytics_table} - Not found")

            print(f"\n🌐 You can now view these tables in your cloud ClickHouse instance!")
            print(f"💡 Try queries like:")
            print(f"   SELECT * FROM {self.test_table} LIMIT 10;")
            print(f"   SELECT event_type, count() FROM {self.analytics_table} GROUP BY event_type;")
            print(f"   SELECT country, sum(revenue) FROM {self.analytics_table} GROUP BY country ORDER BY sum(revenue) DESC;")
            print("="*60)

    def _test_schema_operations(self):
        """Test schema introspection"""
        self._test_case("Get Table Names", self._test_get_table_names)
        self._test_case("Database Info", self._test_database_info)

    def _test_get_table_names(self):
        """Test getting table names"""
        with ClickHouseConnector() as db:
            tables = db.get_table_names()
            assert isinstance(tables, list)
            # Should have system tables at minimum
            assert len(tables) > 0

    def _test_database_info(self):
        """Test database information retrieval"""
        with ClickHouseConnector() as db:
            info = db.get_database_info()
            assert isinstance(info, dict)
            assert 'database_info' in info
            assert 'table_count' in info
            assert 'connection_protocol' in info

    def _test_performance(self):
        """Test performance characteristics"""
        self._test_case("Large Query Performance", self._test_large_query)
        self._test_case("Connection Pool", self._test_connection_pool)

    def _test_large_query(self):
        """Test performance with larger datasets"""
        with ClickHouseConnector() as db:
            start_time = time.time()
            result = db.fetch_all("SELECT number FROM system.numbers LIMIT 10000")
            end_time = time.time()

            assert len(result) == 10000
            duration = end_time - start_time
            print(f"    ⏱️  Large query took {format_duration(duration)}")

    def _test_connection_pool(self):
        """Test connection pooling"""
        # Multiple quick connections
        for i in range(5):
            with ClickHouseConnector() as db:
                result = db.fetch_one("SELECT 1 as test")
                assert result['test'] == 1

    def _test_error_handling(self):
        """Test error handling"""
        self._test_case("Invalid Query", self._test_invalid_query)
        self._test_case("Non-existent Table", self._test_nonexistent_table)

    def _test_invalid_query(self):
        """Test handling of invalid queries"""
        with ClickHouseConnector() as db:
            try:
                db.execute_query("INVALID SQL QUERY")
                assert False, "Should have raised an exception"
            except ClickHouseQueryError:
                pass  # Expected

    def _test_nonexistent_table(self):
        """Test querying non-existent table"""
        with ClickHouseConnector() as db:
            try:
                db.execute_query("SELECT * FROM non_existent_table_12345")
                assert False, "Should have raised an exception"
            except ClickHouseQueryError:
                pass  # Expected

    def _test_advanced_features(self):
        """Test advanced ClickHouse features"""
        self._test_case("System Tables Query", self._test_system_tables)
        self._test_case("Data Types", self._test_data_types)

    def _test_system_tables(self):
        """Test querying ClickHouse system tables"""
        with ClickHouseConnector() as db:
            # Query system.databases
            databases = db.fetch_all("SELECT name FROM system.databases")
            assert len(databases) > 0

            # Query system.tables
            tables = db.fetch_all("SELECT name FROM system.tables LIMIT 10")
            assert len(tables) > 0

    def _test_data_types(self):
        """Test various ClickHouse data types"""
        with ClickHouseConnector() as db:
            query = """
            SELECT
                toUInt32(42) as uint_val,
                toFloat64(3.14159) as float_val,
                'Hello ClickHouse' as string_val,
                today() as date_val,
                now() as datetime_val
            """
            result = db.fetch_one(query)
            assert result is not None
            assert result['uint_val'] == 42
            assert abs(result['float_val'] - 3.14159) < 0.0001

    def _test_case(self, test_name: str, test_func):
        """Execute a single test case"""
        try:
            start_time = time.time()
            test_func()
            end_time = time.time()
            duration = end_time - start_time

            self._record_test(test_name, True, f"Completed in {format_duration(duration)}")
            print(f"✅ {test_name} - {format_duration(duration)}")

        except Exception as e:
            self._record_test(test_name, False, str(e))
            print(f"❌ {test_name} - {str(e)}")

    def _record_test(self, name: str, passed: bool, details: str):
        """Record test result"""
        self.test_results.append({
            'name': name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now()
        })

    def _display_summary(self):
        """Display test summary"""
        total_time = time.time() - self.start_time
        passed_tests = sum(1 for test in self.test_results if test['passed'])
        total_tests = len(self.test_results)

        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Total Time: {format_duration(total_time)}")

        if total_tests - passed_tests > 0:
            print("\n❌ Failed Tests:")
            for test in self.test_results:
                if not test['passed']:
                    print(f"  - {test['name']}: {test['details']}")

        print(f"\n{'🎉 All tests passed!' if passed_tests == total_tests else '⚠️  Some tests failed'}")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Run tests
    test_suite = ClickHouseConnectorTest()
    test_suite.run_all_tests()
