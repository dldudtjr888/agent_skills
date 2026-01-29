#!/usr/bin/env python3
"""
Live database schema inspector.
Connects to actual databases to verify schema, indexes, and statistics.
"""

import os
import json
import sys
from typing import Dict, List, Optional
from urllib.parse import urlparse


class DatabaseInspector:
    """Base class for database inspection"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.db_type = self.detect_db_type(connection_string)
    
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
    
    def inspect(self) -> Dict:
        """Main inspection method - override in subclasses"""
        raise NotImplementedError


class PostgreSQLInspector(DatabaseInspector):
    """PostgreSQL schema inspector"""

    def inspect(self) -> Dict:
        try:
            import psycopg2
        except ImportError:
            return {'error': 'psycopg2 not installed. Run: pip install psycopg2-binary'}

        try:
            conn = psycopg2.connect(self.connection_string)
            conn.set_session(readonly=True)  # 🔒 Read-only mode
            cur = conn.cursor()
            
            # Get tables
            cur.execute("""
                SELECT table_name, 
                       pg_size_pretty(pg_total_relation_size(quote_ident(table_name)::regclass)) as size
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                  AND table_type = 'BASE TABLE'
            """)
            tables = [{'name': row[0], 'size': row[1]} for row in cur.fetchall()]
            
            # Get indexes
            cur.execute("""
                SELECT 
                    t.tablename,
                    i.indexname,
                    array_agg(a.attname ORDER BY a.attnum) as columns,
                    pg_size_pretty(pg_relation_size(i.indexname::regclass)) as size
                FROM pg_indexes i
                JOIN pg_class c ON c.relname = i.indexname
                JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0
                JOIN pg_tables t ON t.tablename = i.tablename
                WHERE t.schemaname = 'public'
                GROUP BY t.tablename, i.indexname
                ORDER BY t.tablename, i.indexname
            """)
            indexes = {}
            for row in cur.fetchall():
                table = row[0]
                if table not in indexes:
                    indexes[table] = []
                indexes[table].append({
                    'name': row[1],
                    'columns': row[2],
                    'size': row[3]
                })
            
            # Get foreign keys
            cur.execute("""
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table,
                    ccu.column_name AS foreign_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = 'public'
            """)
            foreign_keys = {}
            for row in cur.fetchall():
                table = row[0]
                if table not in foreign_keys:
                    foreign_keys[table] = []
                foreign_keys[table].append({
                    'column': row[1],
                    'references_table': row[2],
                    'references_column': row[3]
                })
            
            # Get table statistics
            cur.execute("""
                SELECT 
                    tablename,
                    n_live_tup as row_count,
                    n_dead_tup as dead_rows,
                    last_vacuum,
                    last_autovacuum
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
            """)
            stats = {}
            for row in cur.fetchall():
                stats[row[0]] = {
                    'row_count': row[1],
                    'dead_rows': row[2],
                    'last_vacuum': str(row[3]) if row[3] else None,
                    'last_autovacuum': str(row[4]) if row[4] else None
                }
            
            # Get constraints
            cur.execute("""
                SELECT
                    tc.table_name,
                    tc.constraint_name,
                    tc.constraint_type
                FROM information_schema.table_constraints tc
                WHERE tc.table_schema = 'public'
                  AND tc.constraint_type IN ('UNIQUE', 'PRIMARY KEY', 'CHECK')
            """)
            constraints = {}
            for row in cur.fetchall():
                table = row[0]
                if table not in constraints:
                    constraints[table] = []
                constraints[table].append({
                    'name': row[1],
                    'type': row[2]
                })
            
            cur.close()
            conn.close()
            
            return {
                'db_type': 'postgresql',
                'tables': tables,
                'indexes': indexes,
                'foreign_keys': foreign_keys,
                'statistics': stats,
                'constraints': constraints,
                'total_tables': len(tables)
            }
            
        except Exception as e:
            return {'error': str(e)}


class MySQLInspector(DatabaseInspector):
    """MySQL schema inspector"""
    
    def inspect(self) -> Dict:
        try:
            import mysql.connector
        except ImportError:
            return {'error': 'mysql-connector-python not installed. Run: pip install mysql-connector-python'}
        
        try:
            # Parse connection string
            parsed = urlparse(self.connection_string)
            config = {
                'host': parsed.hostname,
                'port': parsed.port or 3306,
                'user': parsed.username,
                'password': parsed.password,
                'database': parsed.path.lstrip('/')
            }
            
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            cursor.execute("SET SESSION TRANSACTION READ ONLY")  # 🔒 Read-only mode
            
            # Get tables
            cursor.execute("SHOW TABLES")
            tables = [{'name': row[0]} for row in cursor.fetchall()]
            
            # Get indexes and stats for each table
            indexes = {}
            stats = {}
            
            for table in tables:
                table_name = table['name']
                
                # Get indexes
                cursor.execute(f"SHOW INDEX FROM {table_name}")
                table_indexes = {}
                for row in cursor.fetchall():
                    idx_name = row[2]
                    if idx_name not in table_indexes:
                        table_indexes[idx_name] = []
                    table_indexes[idx_name].append(row[4])  # Column name
                
                indexes[table_name] = [
                    {'name': name, 'columns': cols}
                    for name, cols in table_indexes.items()
                ]
                
                # Get table stats
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                stats[table_name] = {'row_count': row_count}
            
            cursor.close()
            conn.close()
            
            return {
                'db_type': 'mysql',
                'tables': tables,
                'indexes': indexes,
                'statistics': stats,
                'total_tables': len(tables)
            }
            
        except Exception as e:
            return {'error': str(e)}


class SQLiteInspector(DatabaseInspector):
    """SQLite schema inspector"""

    def inspect(self) -> Dict:
        try:
            import sqlite3
        except ImportError:
            return {'error': 'sqlite3 not available'}

        try:
            # 🔒 Read-only mode: use URI with mode=ro
            if self.connection_string.startswith('file:'):
                uri = self.connection_string
            else:
                uri = f"file:{self.connection_string}?mode=ro"
            conn = sqlite3.connect(uri, uri=True)
            cursor = conn.cursor()

            # Get tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [{'name': row[0]} for row in cursor.fetchall()]

            # Get indexes and stats for each table
            indexes = {}
            stats = {}

            for table in tables:
                table_name = table['name']

                # Get indexes
                cursor.execute(f"PRAGMA index_list('{table_name}')")
                table_indexes = []
                for row in cursor.fetchall():
                    idx_name = row[1]
                    cursor.execute(f"PRAGMA index_info('{idx_name}')")
                    idx_columns = [r[2] for r in cursor.fetchall()]
                    table_indexes.append({
                        'name': idx_name,
                        'columns': idx_columns,
                        'unique': bool(row[2])
                    })

                indexes[table_name] = table_indexes

                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
                row_count = cursor.fetchone()[0]
                stats[table_name] = {'row_count': row_count}

            # Get foreign keys
            foreign_keys = {}
            for table in tables:
                table_name = table['name']
                cursor.execute(f"PRAGMA foreign_key_list('{table_name}')")
                fks = cursor.fetchall()
                if fks:
                    foreign_keys[table_name] = [
                        {
                            'column': fk[3],
                            'references_table': fk[2],
                            'references_column': fk[4]
                        }
                        for fk in fks
                    ]

            cursor.close()
            conn.close()

            return {
                'db_type': 'sqlite',
                'tables': tables,
                'indexes': indexes,
                'foreign_keys': foreign_keys,
                'statistics': stats,
                'total_tables': len(tables)
            }

        except Exception as e:
            return {'error': str(e)}


def inspect_database(connection_string: str) -> Dict:
    """Main inspection function for SQL databases"""
    inspector = DatabaseInspector(connection_string)
    db_type = inspector.db_type

    if db_type == 'postgresql':
        inspector = PostgreSQLInspector(connection_string)
    elif db_type == 'mysql':
        inspector = MySQLInspector(connection_string)
    elif db_type == 'sqlite':
        inspector = SQLiteInspector(connection_string)
    else:
        return {'error': f'Unsupported database type: {db_type}. Supported: postgresql, mysql, sqlite'}

    return inspector.inspect()


def main():
    if len(sys.argv) < 2:
        print("Usage: python inspect_live_schema.py <connection_string>")
        print("\nSupported SQL Databases:")
        print("  PostgreSQL: postgresql://user:pass@localhost:5432/dbname")
        print("  MySQL: mysql://user:pass@localhost:3306/dbname")
        print("  SQLite: /path/to/database.db or sqlite:///path/to/database.db")
        sys.exit(1)

    # Get connection string from args or env
    connection_string = sys.argv[1]

    print(f"Inspecting SQL database...")
    result = inspect_database(connection_string)

    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        sys.exit(1)

    # Save to file
    output_file = 'live_schema_inspection.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    # Print summary
    print(f"\n✅ Inspection complete!")
    print(f"Database type: {result.get('db_type')}")
    print(f"Total tables: {result.get('total_tables', 0)}")
    print(f"Results saved to: {output_file}")

    # Print tables with no indexes
    no_indexes = [
        table['name'] for table in result.get('tables', [])
        if table['name'] not in result.get('indexes', {}) or not result['indexes'][table['name']]
    ]
    if no_indexes:
        print(f"\n⚠️  Tables without indexes: {', '.join(no_indexes)}")

    # Print foreign key info
    fk_count = sum(len(fks) for fks in result.get('foreign_keys', {}).values())
    print(f"Foreign keys found: {fk_count}")


if __name__ == '__main__':
    main()
