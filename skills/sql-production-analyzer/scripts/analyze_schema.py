#!/usr/bin/env python3
"""
Analyze database schema for production readiness.
Supports multiple schema definition formats.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict


class SchemaAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.tables = {}
        self.indexes = defaultdict(list)
        self.foreign_keys = defaultdict(list)
        self.issues = []
        
    def analyze(self):
        """Main analysis entry point"""
        # Try different schema formats
        self.find_prisma_schema()
        self.find_sql_migrations()
        self.find_typeorm_entities()
        self.find_sqlalchemy_models()
        
        # Analyze findings
        self.check_indexes()
        self.check_foreign_keys()
        self.check_constraints()
        
        return self.generate_report()
    
    def find_prisma_schema(self):
        """Parse Prisma schema files"""
        for schema_file in self.project_path.rglob('schema.prisma'):
            with open(schema_file, 'r') as f:
                content = f.read()
            
            # Extract models
            model_pattern = r'model\s+(\w+)\s*\{([^}]+)\}'
            for match in re.finditer(model_pattern, content):
                table_name = match.group(1)
                fields = match.group(2)
                
                self.tables[table_name] = {
                    'source': str(schema_file.relative_to(self.project_path)),
                    'columns': self.parse_prisma_fields(fields),
                }
                
                # Extract indexes
                index_pattern = r'@@index\(\[([^\]]+)\]'
                for idx_match in re.finditer(index_pattern, fields):
                    columns = [c.strip() for c in idx_match.group(1).split(',')]
                    self.indexes[table_name].append({
                        'columns': columns,
                        'type': 'index'
                    })
    
    def parse_prisma_fields(self, fields_text: str) -> List[Dict]:
        """Parse Prisma field definitions"""
        columns = []
        for line in fields_text.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('@@') or line.startswith('//'):
                continue
            
            # Parse: fieldName Type @attributes
            parts = line.split()
            if len(parts) >= 2:
                col = {
                    'name': parts[0],
                    'type': parts[1],
                    'nullable': '?' in parts[1],
                    'unique': '@unique' in line,
                    'default': '@default' in line,
                }
                columns.append(col)
        
        return columns
    
    def find_sql_migrations(self):
        """Parse SQL migration files"""
        migration_dirs = ['migrations', 'db/migrate', 'alembic/versions']
        
        for dir_name in migration_dirs:
            migration_path = self.project_path / dir_name
            if not migration_path.exists():
                continue
            
            for sql_file in migration_path.rglob('*.sql'):
                self.parse_sql_file(sql_file)
    
    def parse_sql_file(self, sql_file: Path):
        """Extract table definitions from SQL"""
        with open(sql_file, 'r') as f:
            content = f.read()
        
        # Extract CREATE TABLE statements
        create_table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\(([^;]+)\)'
        for match in re.finditer(create_table_pattern, content, re.IGNORECASE | re.DOTALL):
            table_name = match.group(1)
            columns_def = match.group(2)
            
            if table_name not in self.tables:
                self.tables[table_name] = {
                    'source': str(sql_file.relative_to(self.project_path)),
                    'columns': self.parse_sql_columns(columns_def),
                }
        
        # Extract CREATE INDEX statements
        index_pattern = r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(\w+)\s+ON\s+(\w+)\s*\(([^)]+)\)'
        for match in re.finditer(index_pattern, content, re.IGNORECASE):
            index_name = match.group(1)
            table_name = match.group(2)
            columns = [c.strip() for c in match.group(3).split(',')]
            
            self.indexes[table_name].append({
                'name': index_name,
                'columns': columns,
                'type': 'UNIQUE' if 'UNIQUE' in match.group(0).upper() else 'INDEX'
            })
    
    def parse_sql_columns(self, columns_def: str) -> List[Dict]:
        """Parse SQL column definitions"""
        columns = []
        for line in columns_def.split(','):
            line = line.strip()
            if not line or line.upper().startswith(('PRIMARY', 'FOREIGN', 'UNIQUE', 'CHECK', 'CONSTRAINT')):
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                col = {
                    'name': parts[0],
                    'type': parts[1],
                    'nullable': 'NOT NULL' not in line.upper(),
                    'primary': 'PRIMARY KEY' in line.upper(),
                    'unique': 'UNIQUE' in line.upper(),
                }
                columns.append(col)
        
        return columns
    
    def find_typeorm_entities(self):
        """Find TypeORM entity files"""
        for entity_file in self.project_path.rglob('*.entity.ts'):
            with open(entity_file, 'r') as f:
                content = f.read()
            
            # Extract @Entity decorator
            entity_pattern = r'@Entity\([\'"]?(\w+)?[\'"]?\)'
            entity_match = re.search(entity_pattern, content)
            if entity_match:
                table_name = entity_match.group(1) or entity_file.stem.replace('.entity', '')
                
                # Extract @Column decorators
                columns = []
                column_pattern = r'@Column\(([^)]*)\)[\s\n]+(\w+):'
                for col_match in re.finditer(column_pattern, content):
                    col_name = col_match.group(2)
                    columns.append({'name': col_name, 'type': 'unknown'})
                
                self.tables[table_name] = {
                    'source': str(entity_file.relative_to(self.project_path)),
                    'columns': columns,
                }
    
    def find_sqlalchemy_models(self):
        """Find SQLAlchemy model files"""
        for py_file in self.project_path.rglob('*.py'):
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                # Look for SQLAlchemy models
                if 'Base' not in content or 'Column' not in content:
                    continue
                
                # Extract table definitions
                class_pattern = r'class\s+(\w+)\([^)]*\):\s*\n\s*__tablename__\s*=\s*[\'"](\w+)[\'"]'
                for match in re.finditer(class_pattern, content):
                    class_name = match.group(1)
                    table_name = match.group(2)
                    
                    # Find columns in this class
                    columns = []
                    column_pattern = r'(\w+)\s*=\s*Column\('
                    for col_match in re.finditer(column_pattern, content):
                        columns.append({'name': col_match.group(1), 'type': 'unknown'})
                    
                    self.tables[table_name] = {
                        'source': str(py_file.relative_to(self.project_path)),
                        'columns': columns,
                    }
            except:
                continue
    
    def check_indexes(self):
        """Check for missing or redundant indexes"""
        for table_name, table_info in self.tables.items():
            columns = table_info['columns']
            indexes = self.indexes.get(table_name, [])
            
            # Check for tables without any indexes
            if not indexes and len(columns) > 2:
                self.issues.append({
                    'severity': 'MEDIUM',
                    'type': 'missing_indexes',
                    'table': table_name,
                    'message': f'Table {table_name} has no indexes defined',
                    'file': table_info['source']
                })
            
            # Check for duplicate indexes
            index_cols = [tuple(idx['columns']) for idx in indexes]
            if len(index_cols) != len(set(index_cols)):
                self.issues.append({
                    'severity': 'LOW',
                    'type': 'duplicate_index',
                    'table': table_name,
                    'message': f'Table {table_name} has duplicate indexes',
                    'file': table_info['source']
                })
    
    def check_foreign_keys(self):
        """Check foreign key definitions"""
        for table_name, table_info in self.tables.items():
            columns = table_info['columns']
            
            # Look for columns that look like foreign keys but aren't defined
            for col in columns:
                col_name = col['name'].lower()
                if col_name.endswith('_id') or col_name.endswith('id'):
                    # Should have a foreign key or index
                    has_index = any(
                        col['name'] in idx['columns'] 
                        for idx in self.indexes.get(table_name, [])
                    )
                    
                    if not has_index:
                        self.issues.append({
                            'severity': 'HIGH',
                            'type': 'missing_fk_index',
                            'table': table_name,
                            'column': col['name'],
                            'message': f'Foreign key column {col["name"]} in {table_name} lacks an index',
                            'file': table_info['source']
                        })
    
    def check_constraints(self):
        """Check for missing constraints"""
        for table_name, table_info in self.tables.items():
            columns = table_info['columns']
            
            # Check for primary keys
            has_pk = any(col.get('primary') for col in columns)
            if not has_pk and 'id' in [col['name'] for col in columns]:
                self.issues.append({
                    'severity': 'CRITICAL',
                    'type': 'missing_primary_key',
                    'table': table_name,
                    'message': f'Table {table_name} may be missing primary key constraint',
                    'file': table_info['source']
                })
    
    def generate_report(self) -> Dict:
        """Generate analysis report"""
        return {
            'summary': {
                'tables_found': len(self.tables),
                'indexes_found': sum(len(idx) for idx in self.indexes.values()),
                'issues_found': len(self.issues),
            },
            'tables': self.tables,
            'indexes': dict(self.indexes),
            'issues': sorted(self.issues, key=lambda x: {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}[x['severity']])
        }


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python analyze_schema.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    print(f"Analyzing database schema in {project_path}...")
    analyzer = SchemaAnalyzer(project_path)
    report = analyzer.analyze()
    
    # Save report
    output_file = 'schema_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nAnalysis complete!")
    print(f"Tables found: {report['summary']['tables_found']}")
    print(f"Indexes found: {report['summary']['indexes_found']}")
    print(f"Issues found: {report['summary']['issues_found']}")
    print(f"\nDetailed report saved to {output_file}")
    
    # Print critical issues
    critical = [i for i in report['issues'] if i['severity'] == 'CRITICAL']
    if critical:
        print(f"\n⚠️  {len(critical)} CRITICAL issues found:")
        for issue in critical:
            print(f"  - {issue['message']} ({issue['file']})")


if __name__ == '__main__':
    main()
