#!/usr/bin/env python3
"""
Schema-Code Comparison Tool.
Compares ORM models/code references against live database schema
to detect mismatches after DB changes.
"""

import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse


# ============================================================
# Code Schema Extractors (ORM Models → Tables/Columns)
# ============================================================

class CodeSchemaExtractor:
    """Base class for extracting schema from code"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.tables: Dict[str, Dict] = {}  # table_name -> {columns: [], file: str, line: int}

    def extract(self) -> Dict[str, Dict]:
        raise NotImplementedError


class PrismaExtractor(CodeSchemaExtractor):
    """Extract schema from Prisma schema.prisma file"""

    def extract(self) -> Dict[str, Dict]:
        schema_files = list(self.project_path.rglob('schema.prisma'))

        for schema_file in schema_files:
            try:
                content = schema_file.read_text()
                self._parse_prisma_schema(content, str(schema_file))
            except Exception as e:
                print(f"Error parsing {schema_file}: {e}")

        return self.tables

    def _parse_prisma_schema(self, content: str, file_path: str):
        # Find model definitions
        model_pattern = r'model\s+(\w+)\s*\{([^}]+)\}'

        for match in re.finditer(model_pattern, content, re.DOTALL):
            model_name = match.group(1)
            model_body = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            # Extract @@map for actual table name
            map_match = re.search(r'@@map\(["\'](\w+)["\']\)', model_body)
            table_name = map_match.group(1) if map_match else self._to_snake_case(model_name)

            # Extract columns
            columns = []
            for line in model_body.split('\n'):
                line = line.strip()
                if not line or line.startswith('//') or line.startswith('@@'):
                    continue

                # Parse field: name Type modifiers
                field_match = re.match(r'(\w+)\s+(\w+)(\?)?', line)
                if field_match:
                    col_name = field_match.group(1)
                    col_type = field_match.group(2)
                    nullable = bool(field_match.group(3))

                    # Skip relations
                    if col_type[0].isupper() and col_type not in ['String', 'Int', 'Float', 'Boolean', 'DateTime', 'Json', 'Bytes', 'BigInt', 'Decimal']:
                        continue

                    # Check for @map
                    map_col = re.search(r'@map\(["\'](\w+)["\']\)', line)
                    db_col_name = map_col.group(1) if map_col else col_name

                    columns.append({
                        'name': db_col_name,
                        'type': self._prisma_to_sql_type(col_type),
                        'nullable': nullable
                    })

            self.tables[table_name] = {
                'columns': columns,
                'file': file_path,
                'line': line_num,
                'orm': 'prisma'
            }

    def _to_snake_case(self, name: str) -> str:
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    def _prisma_to_sql_type(self, prisma_type: str) -> str:
        type_map = {
            'String': 'varchar',
            'Int': 'integer',
            'Float': 'float',
            'Boolean': 'boolean',
            'DateTime': 'timestamp',
            'Json': 'json',
            'BigInt': 'bigint',
            'Decimal': 'decimal',
            'Bytes': 'bytea'
        }
        return type_map.get(prisma_type, prisma_type.lower())


class TypeORMExtractor(CodeSchemaExtractor):
    """Extract schema from TypeORM entity files"""

    def extract(self) -> Dict[str, Dict]:
        entity_files = list(self.project_path.rglob('*.entity.ts')) + \
                       list(self.project_path.rglob('*.entity.js'))

        for entity_file in entity_files:
            if 'node_modules' in str(entity_file):
                continue
            try:
                content = entity_file.read_text()
                self._parse_typeorm_entity(content, str(entity_file))
            except Exception as e:
                print(f"Error parsing {entity_file}: {e}")

        return self.tables

    def _parse_typeorm_entity(self, content: str, file_path: str):
        # Find @Entity decorator with table name
        entity_match = re.search(r'@Entity\([\'"]?(\w+)?[\'"]?\)', content)
        class_match = re.search(r'class\s+(\w+)', content)

        if not class_match:
            return

        class_name = class_match.group(1)
        table_name = entity_match.group(1) if entity_match and entity_match.group(1) else self._to_snake_case(class_name)
        line_num = content[:class_match.start()].count('\n') + 1

        # Find columns with @Column decorator
        columns = []
        column_pattern = r'@Column\(([^)]*)\)[^@]*?(\w+)[\s:]+(\w+)'

        for match in re.finditer(column_pattern, content, re.DOTALL):
            col_options = match.group(1)
            col_name = match.group(2)
            col_type = match.group(3)

            # Check for name option in @Column
            name_match = re.search(r'name:\s*[\'"](\w+)[\'"]', col_options)
            db_col_name = name_match.group(1) if name_match else col_name

            nullable = 'nullable: true' in col_options

            columns.append({
                'name': db_col_name,
                'type': col_type.lower(),
                'nullable': nullable
            })

        # Also find @PrimaryGeneratedColumn
        pk_pattern = r'@PrimaryGeneratedColumn\([^)]*\)[^@]*?(\w+)'
        for match in re.finditer(pk_pattern, content):
            columns.append({
                'name': match.group(1),
                'type': 'integer',
                'nullable': False
            })

        if columns:
            self.tables[table_name] = {
                'columns': columns,
                'file': file_path,
                'line': line_num,
                'orm': 'typeorm'
            }

    def _to_snake_case(self, name: str) -> str:
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


class DjangoExtractor(CodeSchemaExtractor):
    """Extract schema from Django models.py files"""

    def extract(self) -> Dict[str, Dict]:
        model_files = list(self.project_path.rglob('models.py'))

        for model_file in model_files:
            if 'venv' in str(model_file) or 'site-packages' in str(model_file):
                continue
            try:
                content = model_file.read_text()
                self._parse_django_models(content, str(model_file))
            except Exception as e:
                print(f"Error parsing {model_file}: {e}")

        return self.tables

    def _parse_django_models(self, content: str, file_path: str):
        # Find class definitions that inherit from models.Model
        class_pattern = r'class\s+(\w+)\s*\(\s*(?:models\.Model|[\w.]+)\s*\)\s*:'

        for class_match in re.finditer(class_pattern, content):
            class_name = class_match.group(1)
            class_start = class_match.end()
            line_num = content[:class_match.start()].count('\n') + 1

            # Find next class or end of file
            next_class = re.search(r'\nclass\s+\w+', content[class_start:])
            class_end = class_start + next_class.start() if next_class else len(content)
            class_body = content[class_start:class_end]

            # Check for Meta class with db_table
            meta_match = re.search(r'class\s+Meta\s*:.*?db_table\s*=\s*[\'"](\w+)[\'"]', class_body, re.DOTALL)
            table_name = meta_match.group(1) if meta_match else f"{self._get_app_name(file_path)}_{class_name.lower()}"

            # Extract fields
            columns = []
            field_pattern = r'(\w+)\s*=\s*models\.(\w+Field)\s*\(([^)]*)\)'

            for field_match in re.finditer(field_pattern, class_body):
                col_name = field_match.group(1)
                field_type = field_match.group(2)
                options = field_match.group(3)

                # Check for db_column
                db_col_match = re.search(r'db_column\s*=\s*[\'"](\w+)[\'"]', options)
                db_col_name = db_col_match.group(1) if db_col_match else col_name

                nullable = 'null=True' in options

                columns.append({
                    'name': db_col_name,
                    'type': self._django_to_sql_type(field_type),
                    'nullable': nullable
                })

            if columns:
                self.tables[table_name] = {
                    'columns': columns,
                    'file': file_path,
                    'line': line_num,
                    'orm': 'django'
                }

    def _get_app_name(self, file_path: str) -> str:
        parts = Path(file_path).parts
        if 'models.py' in parts[-1]:
            return parts[-2] if len(parts) > 1 else 'app'
        return 'app'

    def _django_to_sql_type(self, django_type: str) -> str:
        type_map = {
            'CharField': 'varchar',
            'TextField': 'text',
            'IntegerField': 'integer',
            'BigIntegerField': 'bigint',
            'SmallIntegerField': 'smallint',
            'FloatField': 'float',
            'DecimalField': 'decimal',
            'BooleanField': 'boolean',
            'DateField': 'date',
            'DateTimeField': 'timestamp',
            'TimeField': 'time',
            'UUIDField': 'uuid',
            'JSONField': 'json',
            'ForeignKey': 'integer',
            'OneToOneField': 'integer',
        }
        return type_map.get(django_type, 'unknown')


class SQLAlchemyExtractor(CodeSchemaExtractor):
    """Extract schema from SQLAlchemy model files"""

    def extract(self) -> Dict[str, Dict]:
        py_files = list(self.project_path.rglob('*.py'))

        for py_file in py_files:
            if any(skip in str(py_file) for skip in ['venv', '__pycache__', 'site-packages', 'migrations']):
                continue
            try:
                content = py_file.read_text()
                if 'Column(' in content and ('Base' in content or 'declarative' in content):
                    self._parse_sqlalchemy_models(content, str(py_file))
            except Exception as e:
                pass  # Skip files that can't be read

        return self.tables

    def _parse_sqlalchemy_models(self, content: str, file_path: str):
        # Find class definitions with __tablename__
        class_pattern = r'class\s+(\w+)\s*\([^)]+\)\s*:'

        for class_match in re.finditer(class_pattern, content):
            class_name = class_match.group(1)
            class_start = class_match.end()
            line_num = content[:class_match.start()].count('\n') + 1

            # Find class body (until next class or dedent)
            next_class = re.search(r'\nclass\s+\w+', content[class_start:])
            class_end = class_start + next_class.start() if next_class else len(content)
            class_body = content[class_start:class_end]

            # Get table name
            tablename_match = re.search(r'__tablename__\s*=\s*[\'"](\w+)[\'"]', class_body)
            if not tablename_match:
                continue

            table_name = tablename_match.group(1)

            # Extract columns
            columns = []
            column_pattern = r'(\w+)\s*=\s*Column\s*\(\s*(\w+)'

            for col_match in re.finditer(column_pattern, class_body):
                col_name = col_match.group(1)
                col_type = col_match.group(2)

                # Check for nullable in the Column definition
                col_full = re.search(rf'{col_name}\s*=\s*Column\s*\([^)]+\)', class_body)
                nullable = 'nullable=False' not in (col_full.group(0) if col_full else '')

                columns.append({
                    'name': col_name,
                    'type': col_type.lower(),
                    'nullable': nullable
                })

            if columns:
                self.tables[table_name] = {
                    'columns': columns,
                    'file': file_path,
                    'line': line_num,
                    'orm': 'sqlalchemy'
                }


class RawSQLExtractor(CodeSchemaExtractor):
    """Extract table/column references from raw SQL queries in code"""

    def extract(self) -> Dict[str, Dict]:
        extensions = ['.js', '.ts', '.py', '.rb', '.go', '.java', '.php']

        for ext in extensions:
            for file_path in self.project_path.rglob(f'*{ext}'):
                if any(skip in str(file_path) for skip in ['node_modules', 'venv', '__pycache__', '.git']):
                    continue
                try:
                    content = file_path.read_text()
                    self._extract_sql_references(content, str(file_path))
                except Exception:
                    pass

        return self.tables

    def _extract_sql_references(self, content: str, file_path: str):
        # Find SQL statements in strings
        sql_patterns = [
            r'SELECT\s+.+?\s+FROM\s+[`"\']?(\w+)[`"\']?',
            r'INSERT\s+INTO\s+[`"\']?(\w+)[`"\']?',
            r'UPDATE\s+[`"\']?(\w+)[`"\']?',
            r'DELETE\s+FROM\s+[`"\']?(\w+)[`"\']?',
            r'JOIN\s+[`"\']?(\w+)[`"\']?',
        ]

        for pattern in sql_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                table_name = match.group(1).lower()
                line_num = content[:match.start()].count('\n') + 1

                if table_name not in self.tables:
                    self.tables[table_name] = {
                        'columns': [],  # Can't extract columns from raw SQL easily
                        'file': file_path,
                        'line': line_num,
                        'orm': 'raw_sql'
                    }


# ============================================================
# DB Schema Fetcher
# ============================================================

class DBSchemaFetcher:
    """Fetch actual schema from database"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.db_type = self._detect_db_type(connection_string)

    def _detect_db_type(self, conn_str: str) -> str:
        parsed = urlparse(conn_str)
        scheme = parsed.scheme.lower()

        if 'postgres' in scheme:
            return 'postgresql'
        elif 'mysql' in scheme:
            return 'mysql'
        elif 'sqlite' in scheme or conn_str.endswith('.db') or conn_str.endswith('.sqlite'):
            return 'sqlite'
        return 'unknown'

    def fetch(self) -> Dict[str, Dict]:
        if self.db_type == 'postgresql':
            return self._fetch_postgresql()
        elif self.db_type == 'mysql':
            return self._fetch_mysql()
        elif self.db_type == 'sqlite':
            return self._fetch_sqlite()
        else:
            return {'error': f'Unsupported database type: {self.db_type}'}

    def _fetch_postgresql(self) -> Dict[str, Dict]:
        try:
            import psycopg2
        except ImportError:
            return {'error': 'psycopg2 not installed'}

        try:
            conn = psycopg2.connect(self.connection_string)
            conn.set_session(readonly=True)  # 🔒 Read-only
            cur = conn.cursor()

            # Get all tables and columns
            cur.execute("""
                SELECT
                    table_name,
                    column_name,
                    data_type,
                    is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)

            tables = {}
            for row in cur.fetchall():
                table_name, col_name, col_type, nullable = row
                if table_name not in tables:
                    tables[table_name] = {'columns': []}
                tables[table_name]['columns'].append({
                    'name': col_name,
                    'type': col_type,
                    'nullable': nullable == 'YES'
                })

            cur.close()
            conn.close()
            return tables

        except Exception as e:
            return {'error': str(e)}

    def _fetch_mysql(self) -> Dict[str, Dict]:
        try:
            import mysql.connector
        except ImportError:
            return {'error': 'mysql-connector-python not installed'}

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
            cursor = conn.cursor()
            cursor.execute("SET SESSION TRANSACTION READ ONLY")  # 🔒 Read-only

            cursor.execute("""
                SELECT
                    table_name,
                    column_name,
                    data_type,
                    is_nullable
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                ORDER BY table_name, ordinal_position
            """)

            tables = {}
            for row in cursor.fetchall():
                table_name, col_name, col_type, nullable = row
                if table_name not in tables:
                    tables[table_name] = {'columns': []}
                tables[table_name]['columns'].append({
                    'name': col_name,
                    'type': col_type,
                    'nullable': nullable == 'YES'
                })

            cursor.close()
            conn.close()
            return tables

        except Exception as e:
            return {'error': str(e)}

    def _fetch_sqlite(self) -> Dict[str, Dict]:
        try:
            import sqlite3
        except ImportError:
            return {'error': 'sqlite3 not available'}

        try:
            # 🔒 Read-only mode
            if self.connection_string.startswith('file:'):
                uri = self.connection_string
            else:
                uri = f"file:{self.connection_string}?mode=ro"
            conn = sqlite3.connect(uri, uri=True)
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            table_names = [row[0] for row in cursor.fetchall()]

            tables = {}
            for table_name in table_names:
                cursor.execute(f"PRAGMA table_info('{table_name}')")
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        'name': row[1],
                        'type': row[2].lower() if row[2] else 'unknown',
                        'nullable': row[3] == 0  # notnull = 0 means nullable
                    })
                tables[table_name] = {'columns': columns}

            cursor.close()
            conn.close()
            return tables

        except Exception as e:
            return {'error': str(e)}


# ============================================================
# Schema Comparator
# ============================================================

class SchemaComparator:
    """Compare code schema with DB schema"""

    def __init__(self, code_schema: Dict, db_schema: Dict):
        self.code_schema = code_schema
        self.db_schema = db_schema
        self.mismatches = []

    def compare(self) -> List[Dict]:
        self.mismatches = []

        code_tables = set(self.code_schema.keys())
        db_tables = set(self.db_schema.keys())

        # Tables in code but not in DB
        for table in code_tables - db_tables:
            info = self.code_schema[table]
            self.mismatches.append({
                'type': 'missing_table_in_db',
                'severity': 'ERROR',
                'table': table,
                'message': f"Table '{table}' defined in code but NOT in database",
                'file': info.get('file'),
                'line': info.get('line'),
                'orm': info.get('orm'),
                'action': f"CREATE TABLE {table} or remove from code"
            })

        # Tables in DB but not in code (warning only)
        for table in db_tables - code_tables:
            self.mismatches.append({
                'type': 'extra_table_in_db',
                'severity': 'WARNING',
                'table': table,
                'message': f"Table '{table}' exists in database but not referenced in code",
                'action': "Add model or remove table if unused"
            })

        # Compare columns for matching tables
        for table in code_tables & db_tables:
            self._compare_columns(table)

        return self.mismatches

    def _compare_columns(self, table: str):
        code_info = self.code_schema[table]
        code_columns = {c['name'].lower(): c for c in code_info.get('columns', [])}
        db_columns = {c['name'].lower(): c for c in self.db_schema[table].get('columns', [])}

        code_col_names = set(code_columns.keys())
        db_col_names = set(db_columns.keys())

        # Columns in code but not in DB
        for col in code_col_names - db_col_names:
            self.mismatches.append({
                'type': 'missing_column_in_db',
                'severity': 'ERROR',
                'table': table,
                'column': col,
                'message': f"Column '{table}.{col}' defined in code but NOT in database",
                'file': code_info.get('file'),
                'line': code_info.get('line'),
                'action': f"ALTER TABLE {table} ADD COLUMN {col} or remove from model"
            })

        # Columns in DB but not in code
        for col in db_col_names - code_col_names:
            # Skip if code has no columns defined (e.g., raw SQL extraction)
            if not code_columns:
                continue
            self.mismatches.append({
                'type': 'extra_column_in_db',
                'severity': 'WARNING',
                'table': table,
                'column': col,
                'message': f"Column '{table}.{col}' exists in database but not in code model",
                'file': code_info.get('file'),
                'action': "Add to model or remove column if unused"
            })

    def generate_report(self) -> str:
        if not self.mismatches:
            return "✅ No schema mismatches found! Code and database are in sync."

        errors = [m for m in self.mismatches if m['severity'] == 'ERROR']
        warnings = [m for m in self.mismatches if m['severity'] == 'WARNING']

        report = f"""
Schema-Code Comparison Report
=============================
🚨 ERRORS (must fix): {len(errors)}
⚠️  WARNINGS (review): {len(warnings)}

"""

        if errors:
            report += "🚨 ERRORS - Code references that don't exist in DB:\n"
            report += "-" * 50 + "\n"
            for m in errors:
                report += f"\n❌ {m['message']}\n"
                if m.get('file'):
                    report += f"   📍 {m['file']}:{m.get('line', '?')}\n"
                report += f"   💡 {m['action']}\n"

        if warnings:
            report += "\n⚠️  WARNINGS - DB objects not referenced in code:\n"
            report += "-" * 50 + "\n"
            for m in warnings:
                report += f"\n⚠️  {m['message']}\n"
                report += f"   💡 {m['action']}\n"

        return report


# ============================================================
# Main Function
# ============================================================

def compare_schema_code(project_path: str, connection_string: str) -> Dict:
    """Main comparison function"""

    print("📂 Extracting schema from code...")

    # Extract from all supported ORMs
    code_schema = {}

    extractors = [
        PrismaExtractor(project_path),
        TypeORMExtractor(project_path),
        DjangoExtractor(project_path),
        SQLAlchemyExtractor(project_path),
        RawSQLExtractor(project_path),
    ]

    for extractor in extractors:
        try:
            tables = extractor.extract()
            # Merge, preferring ORM models over raw SQL
            for table, info in tables.items():
                if table not in code_schema or code_schema[table].get('orm') == 'raw_sql':
                    code_schema[table] = info
        except Exception as e:
            print(f"  ⚠️  {extractor.__class__.__name__}: {e}")

    print(f"  Found {len(code_schema)} tables in code")

    # Fetch DB schema
    print("\n🗄️  Fetching schema from database...")
    fetcher = DBSchemaFetcher(connection_string)
    db_schema = fetcher.fetch()

    if 'error' in db_schema:
        return {'error': db_schema['error']}

    print(f"  Found {len(db_schema)} tables in database")

    # Compare
    print("\n🔍 Comparing schemas...")
    comparator = SchemaComparator(code_schema, db_schema)
    mismatches = comparator.compare()

    return {
        'code_tables': list(code_schema.keys()),
        'db_tables': list(db_schema.keys()),
        'mismatches': mismatches,
        'report': comparator.generate_report(),
        'summary': {
            'code_table_count': len(code_schema),
            'db_table_count': len(db_schema),
            'errors': len([m for m in mismatches if m['severity'] == 'ERROR']),
            'warnings': len([m for m in mismatches if m['severity'] == 'WARNING'])
        }
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_schema_code.py <project_path> <connection_string>")
        print("\nSupported ORMs: Prisma, TypeORM, Django, SQLAlchemy")
        print("Supported DBs: PostgreSQL, MySQL, SQLite")
        print("\nExamples:")
        print("  python compare_schema_code.py ./my-project postgresql://user:pass@localhost/db")
        print("  python compare_schema_code.py ./my-project mysql://user:pass@localhost/db")
        print("  python compare_schema_code.py ./my-project ./database.db")
        sys.exit(1)

    project_path = sys.argv[1]
    connection_string = sys.argv[2]

    result = compare_schema_code(project_path, connection_string)

    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
        sys.exit(1)

    # Print report
    print(result['report'])

    # Save detailed results
    output_file = 'schema_comparison_results.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n📄 Detailed results saved to: {output_file}")

    # Exit with error code if mismatches found
    if result['summary']['errors'] > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
