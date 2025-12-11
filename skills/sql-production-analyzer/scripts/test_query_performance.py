#!/usr/bin/env python3
"""
Live query performance testing.
Tests actual query execution and generates performance reports.
"""

import json
import sys
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse


class QueryPerformanceTester:
    """Base class for query performance testing"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.db_type = self.detect_db_type(connection_string)
        self.results = []
    
    def detect_db_type(self, conn_str: str) -> str:
        """Detect database type from connection string"""
        parsed = urlparse(conn_str)
        scheme = parsed.scheme.lower()

        if 'postgres' in scheme:
            return 'postgresql'
        elif 'mysql' in scheme:
            return 'mysql'
        elif 'sqlite' in scheme or conn_str.endswith('.db') or conn_str.endswith('.sqlite'):
            return 'sqlite'
        else:
            return 'unknown'
    
    def test_queries(self, queries: List[Dict]) -> List[Dict]:
        """Test queries - override in subclasses"""
        raise NotImplementedError


class PostgreSQLTester(QueryPerformanceTester):
    """PostgreSQL performance tester"""
    
    def test_queries(self, queries: List[Dict]) -> List[Dict]:
        try:
            import psycopg2
        except ImportError:
            return [{'error': 'psycopg2 not installed'}]
        
        try:
            conn = psycopg2.connect(self.connection_string)
            conn.set_session(readonly=True)  # 🔒 Read-only mode
            cur = conn.cursor()
            
            results = []
            
            for query_info in queries:
                query = query_info.get('query', '')
                
                # Skip non-SELECT queries for safety
                if not query.strip().upper().startswith('SELECT'):
                    results.append({
                        'query': query,
                        'file': query_info.get('file'),
                        'line': query_info.get('line'),
                        'skipped': 'Non-SELECT query (safety)'
                    })
                    continue
                
                try:
                    # Run EXPLAIN ANALYZE
                    explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
                    cur.execute(explain_query)
                    explain_result = cur.fetchone()[0][0]
                    
                    plan = explain_result.get('Plan', {})
                    execution_time = explain_result.get('Execution Time', 0)
                    planning_time = explain_result.get('Planning Time', 0)
                    total_cost = plan.get('Total Cost', 0)
                    
                    # Check for issues
                    issues = []
                    
                    # Check for sequential scans
                    if self._has_seq_scan(plan):
                        issues.append('Sequential scan detected')
                    
                    # Check execution time
                    if execution_time > 100:
                        issues.append(f'Slow query: {execution_time:.2f}ms')
                    
                    # Check rows examined vs returned
                    rows_examined = plan.get('Actual Rows', 0)
                    # This is simplified - full analysis would walk the tree
                    
                    result = {
                        'query': query[:200],  # Truncate
                        'file': query_info.get('file'),
                        'line': query_info.get('line'),
                        'execution_time_ms': round(execution_time, 2),
                        'planning_time_ms': round(planning_time, 2),
                        'total_cost': round(total_cost, 2),
                        'issues': issues,
                        'plan_type': plan.get('Node Type'),
                        'has_index_scan': self._has_index_scan(plan)
                    }
                    
                    results.append(result)
                    
                    # Rollback to avoid side effects
                    conn.rollback()
                    
                except Exception as e:
                    results.append({
                        'query': query[:200],
                        'file': query_info.get('file'),
                        'line': query_info.get('line'),
                        'error': str(e)
                    })
            
            cur.close()
            conn.close()
            
            return results
            
        except Exception as e:
            return [{'error': f'Connection failed: {str(e)}'}]
    
    def _has_seq_scan(self, plan: Dict) -> bool:
        """Check if plan contains sequential scan"""
        if plan.get('Node Type') == 'Seq Scan':
            return True
        
        # Check children
        for child in plan.get('Plans', []):
            if self._has_seq_scan(child):
                return True
        
        return False
    
    def _has_index_scan(self, plan: Dict) -> bool:
        """Check if plan uses index scan"""
        node_type = plan.get('Node Type', '')
        if 'Index' in node_type:
            return True
        
        # Check children
        for child in plan.get('Plans', []):
            if self._has_index_scan(child):
                return True
        
        return False


class MySQLTester(QueryPerformanceTester):
    """MySQL performance tester"""
    
    def test_queries(self, queries: List[Dict]) -> List[Dict]:
        try:
            import mysql.connector
        except ImportError:
            return [{'error': 'mysql-connector-python not installed'}]
        
        try:
            parsed = urlparse(self.connection_string)
            config = {
                'host': parsed.hostname,
                'port': parsed.port or 3306,
                'user': parsed.username,
                'password': parsed.password,
                'database': parsed.path.lstrip('/')
            }
            
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SET SESSION TRANSACTION READ ONLY")  # 🔒 Read-only mode
            
            results = []
            
            for query_info in queries:
                query = query_info.get('query', '')
                
                # Skip non-SELECT queries
                if not query.strip().upper().startswith('SELECT'):
                    results.append({
                        'query': query,
                        'file': query_info.get('file'),
                        'line': query_info.get('line'),
                        'skipped': 'Non-SELECT query'
                    })
                    continue
                
                try:
                    # Run EXPLAIN
                    explain_query = f"EXPLAIN {query}"
                    cursor.execute(explain_query)
                    explain_result = cursor.fetchall()
                    
                    issues = []
                    
                    for row in explain_result:
                        # Check type
                        if row['type'] == 'ALL':
                            issues.append('Full table scan (type=ALL)')
                        
                        # Check rows examined
                        if row['rows'] and row['rows'] > 10000:
                            issues.append(f'High row count: {row["rows"]}')
                        
                        # Check if using index
                        if not row['key']:
                            issues.append('No index used')
                    
                    # Time the actual query
                    start = time.time()
                    cursor.execute(query)
                    cursor.fetchall()
                    execution_time = (time.time() - start) * 1000
                    
                    results.append({
                        'query': query[:200],
                        'file': query_info.get('file'),
                        'line': query_info.get('line'),
                        'execution_time_ms': round(execution_time, 2),
                        'issues': issues,
                        'explain': explain_result
                    })
                    
                except Exception as e:
                    results.append({
                        'query': query[:200],
                        'file': query_info.get('file'),
                        'line': query_info.get('line'),
                        'error': str(e)
                    })
            
            cursor.close()
            conn.close()
            
            return results
            
        except Exception as e:
            return [{'error': f'Connection failed: {str(e)}'}]


class SQLiteTester(QueryPerformanceTester):
    """SQLite performance tester"""

    def test_queries(self, queries: List[Dict]) -> List[Dict]:
        try:
            import sqlite3
        except ImportError:
            return [{'error': 'sqlite3 not available'}]

        try:
            # 🔒 Read-only mode: use URI with mode=ro
            if self.connection_string.startswith('file:'):
                uri = self.connection_string
            else:
                uri = f"file:{self.connection_string}?mode=ro"
            conn = sqlite3.connect(uri, uri=True)
            cursor = conn.cursor()

            results = []

            for query_info in queries:
                query = query_info.get('query', '')

                # Skip non-SELECT queries
                if not query.strip().upper().startswith('SELECT'):
                    results.append({
                        'query': query,
                        'file': query_info.get('file'),
                        'line': query_info.get('line'),
                        'skipped': 'Non-SELECT query'
                    })
                    continue

                try:
                    # Run EXPLAIN QUERY PLAN
                    explain_query = f"EXPLAIN QUERY PLAN {query}"
                    cursor.execute(explain_query)
                    explain_result = cursor.fetchall()

                    issues = []

                    for row in explain_result:
                        detail = row[3] if len(row) > 3 else str(row)
                        # Check for table scan
                        if 'SCAN' in detail.upper() and 'INDEX' not in detail.upper():
                            issues.append('Full table scan detected')

                    # Time the actual query
                    start = time.time()
                    cursor.execute(query)
                    cursor.fetchall()
                    execution_time = (time.time() - start) * 1000

                    if execution_time > 100:
                        issues.append(f'Slow query: {execution_time:.2f}ms')

                    results.append({
                        'query': query[:200],
                        'file': query_info.get('file'),
                        'line': query_info.get('line'),
                        'execution_time_ms': round(execution_time, 2),
                        'issues': issues,
                        'explain': [str(r) for r in explain_result]
                    })

                except Exception as e:
                    results.append({
                        'query': query[:200],
                        'file': query_info.get('file'),
                        'line': query_info.get('line'),
                        'error': str(e)
                    })

            cursor.close()
            conn.close()

            return results

        except Exception as e:
            return [{'error': f'Connection failed: {str(e)}'}]


def test_query_performance(connection_string: str, queries_file: str) -> Dict:
    """Main testing function"""
    
    # Load queries
    try:
        with open(queries_file, 'r') as f:
            queries = json.load(f)
    except Exception as e:
        return {'error': f'Failed to load queries: {str(e)}'}
    
    # Filter for SQL queries only
    sql_queries = [q for q in queries if q.get('type') == 'raw_sql']
    
    if not sql_queries:
        return {'error': 'No SQL queries found to test'}
    
    # Create tester
    tester = QueryPerformanceTester(connection_string)

    if tester.db_type == 'postgresql':
        tester = PostgreSQLTester(connection_string)
    elif tester.db_type == 'mysql':
        tester = MySQLTester(connection_string)
    elif tester.db_type == 'sqlite':
        tester = SQLiteTester(connection_string)
    else:
        return {'error': f'Unsupported database type: {tester.db_type}. Supported: postgresql, mysql, sqlite'}
    
    # Test queries
    results = tester.test_queries(sql_queries[:20])  # Limit to first 20 for safety
    
    # Generate summary
    successful_tests = [r for r in results if 'error' not in r and 'skipped' not in r]
    slow_queries = [r for r in successful_tests if r.get('execution_time_ms', 0) > 100]
    with_issues = [r for r in successful_tests if r.get('issues')]
    
    return {
        'db_type': tester.db_type,
        'total_queries_tested': len(results),
        'successful_tests': len(successful_tests),
        'slow_queries': len(slow_queries),
        'queries_with_issues': len(with_issues),
        'results': results,
        'summary': {
            'avg_execution_time': sum(r.get('execution_time_ms', 0) for r in successful_tests) / max(len(successful_tests), 1),
            'max_execution_time': max((r.get('execution_time_ms', 0) for r in successful_tests), default=0),
            'slow_queries_list': [
                {
                    'file': r['file'],
                    'line': r['line'],
                    'time_ms': r['execution_time_ms']
                }
                for r in slow_queries
            ]
        }
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python test_query_performance.py <connection_string> <queries_file>")
        print("\nSupported SQL Databases:")
        print("  PostgreSQL: postgresql://user:pass@localhost/db queries_found.json")
        print("  MySQL: mysql://user:pass@localhost/db queries_found.json")
        print("  SQLite: /path/to/database.db queries_found.json")
        sys.exit(1)
    
    connection_string = sys.argv[1]
    queries_file = sys.argv[2]
    
    print(f"Testing query performance...")
    print(f"Connection: {connection_string.split('@')[0]}@***")  # Hide credentials
    print(f"Queries file: {queries_file}")
    
    result = test_query_performance(connection_string, queries_file)
    
    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
        sys.exit(1)
    
    # Save detailed results
    output_file = 'query_performance_results.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    # Print summary
    print(f"\n✅ Performance testing complete!")
    print(f"\nSummary:")
    print(f"  Total queries tested: {result['total_queries_tested']}")
    print(f"  Successful tests: {result['successful_tests']}")
    print(f"  Slow queries (>100ms): {result['slow_queries']}")
    print(f"  Queries with issues: {result['queries_with_issues']}")
    print(f"\nPerformance:")
    print(f"  Average execution time: {result['summary']['avg_execution_time']:.2f}ms")
    print(f"  Max execution time: {result['summary']['max_execution_time']:.2f}ms")
    
    # Print slow queries
    if result['summary']['slow_queries_list']:
        print(f"\n⚠️  Slow queries detected:")
        for sq in result['summary']['slow_queries_list'][:5]:
            print(f"  - {sq['file']}:{sq['line']} ({sq['time_ms']:.2f}ms)")
    
    print(f"\nDetailed results saved to: {output_file}")


if __name__ == '__main__':
    main()
