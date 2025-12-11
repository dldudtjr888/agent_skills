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
        elif 'mongodb' in scheme or 'mongo' in scheme:
            return 'mongodb'
        elif 'redis' in scheme:
            return 'redis'
        elif 'neo4j' in scheme or 'bolt' in scheme:
            return 'neo4j'
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


class MongoDBInspector(DatabaseInspector):
    """MongoDB inspector"""
    
    def inspect(self) -> Dict:
        try:
            from pymongo import MongoClient
        except ImportError:
            return {'error': 'pymongo not installed. Run: pip install pymongo'}
        
        try:
            client = MongoClient(self.connection_string)
            
            # Get database name from connection string
            parsed = urlparse(self.connection_string)
            db_name = parsed.path.lstrip('/')
            
            if not db_name:
                # List all databases
                dbs = client.list_database_names()
                return {
                    'db_type': 'mongodb',
                    'error': 'No database specified',
                    'available_databases': dbs
                }
            
            db = client[db_name]
            
            # Get collections
            collections = db.list_collection_names()
            
            # Get indexes and stats for each collection
            collection_data = {}
            
            for coll_name in collections:
                collection = db[coll_name]
                
                # Get indexes
                indexes = []
                for idx in collection.list_indexes():
                    indexes.append({
                        'name': idx['name'],
                        'keys': list(idx['key'].keys())
                    })
                
                # Get collection stats
                stats = db.command("collStats", coll_name)
                
                collection_data[coll_name] = {
                    'indexes': indexes,
                    'count': stats.get('count', 0),
                    'size': stats.get('size', 0),
                    'avg_doc_size': stats.get('avgObjSize', 0)
                }
            
            client.close()
            
            return {
                'db_type': 'mongodb',
                'database': db_name,
                'collections': collection_data,
                'total_collections': len(collections)
            }
            
        except Exception as e:
            return {'error': str(e)}


class RedisInspector(DatabaseInspector):
    """Redis inspector"""
    
    def inspect(self) -> Dict:
        try:
            import redis
        except ImportError:
            return {'error': 'redis not installed. Run: pip install redis'}
        
        try:
            r = redis.Redis.from_url(self.connection_string)
            
            # Get basic info
            info = r.info()
            
            # Sample keys (WARNING: SCAN in production, limited to 100)
            keys_sample = []
            keys_without_ttl = []
            
            for key in r.scan_iter(count=100):
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                key_type = r.type(key).decode('utf-8')
                ttl = r.ttl(key)
                
                keys_sample.append({
                    'key': key_str,
                    'type': key_type,
                    'ttl': ttl
                })
                
                if ttl == -1:  # No TTL set
                    keys_without_ttl.append(key_str)
            
            r.close()
            
            return {
                'db_type': 'redis',
                'memory_used': info.get('used_memory_human'),
                'total_keys': info.get('db0', {}).get('keys', 0),
                'keys_sample': keys_sample[:10],  # First 10
                'keys_without_ttl': len(keys_without_ttl),
                'keys_without_ttl_sample': keys_without_ttl[:10]
            }
            
        except Exception as e:
            return {'error': str(e)}


def inspect_database(connection_string: str) -> Dict:
    """Main inspection function"""
    inspector = DatabaseInspector(connection_string)
    db_type = inspector.db_type
    
    if db_type == 'postgresql':
        inspector = PostgreSQLInspector(connection_string)
    elif db_type == 'mysql':
        inspector = MySQLInspector(connection_string)
    elif db_type == 'mongodb':
        inspector = MongoDBInspector(connection_string)
    elif db_type == 'redis':
        inspector = RedisInspector(connection_string)
    else:
        return {'error': f'Unsupported database type: {db_type}'}
    
    return inspector.inspect()


def main():
    if len(sys.argv) < 2:
        print("Usage: python inspect_live_schema.py <connection_string>")
        print("\nExamples:")
        print("  PostgreSQL: postgresql://user:pass@localhost:5432/dbname")
        print("  MySQL: mysql://user:pass@localhost:3306/dbname")
        print("  MongoDB: mongodb://localhost:27017/dbname")
        print("  Redis: redis://localhost:6379/0")
        sys.exit(1)
    
    # Get connection string from args or env
    connection_string = sys.argv[1]
    
    print(f"Inspecting database...")
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
    
    if result['db_type'] in ['postgresql', 'mysql']:
        print(f"Total tables: {result.get('total_tables', 0)}")
        print(f"Results saved to: {output_file}")
        
        # Print tables with no indexes
        no_indexes = [
            table['name'] for table in result.get('tables', [])
            if table['name'] not in result.get('indexes', {}) or not result['indexes'][table['name']]
        ]
        if no_indexes:
            print(f"\n⚠️  Tables without indexes: {', '.join(no_indexes)}")
    
    elif result['db_type'] == 'mongodb':
        print(f"Total collections: {result.get('total_collections', 0)}")
    
    elif result['db_type'] == 'redis':
        print(f"Total keys: {result.get('total_keys', 0)}")
        keys_no_ttl = result.get('keys_without_ttl', 0)
        if keys_no_ttl > 0:
            print(f"⚠️  Keys without TTL: {keys_no_ttl}")


if __name__ == '__main__':
    main()
