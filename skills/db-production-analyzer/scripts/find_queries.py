#!/usr/bin/env python3
"""
Extract all database queries from source code.
Supports multiple languages and ORMs.
"""

import re
import os
import json
from pathlib import Path
from typing import List, Dict, Tuple

# SQL keywords that indicate a query
SQL_KEYWORDS = [
    'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 
    'ALTER', 'TRUNCATE', 'MERGE', 'UPSERT'
]

# ORM patterns for different frameworks
ORM_PATTERNS = {
    # JavaScript/TypeScript - SQL
    'prisma': [
        r'prisma\.\w+\.(?:findMany|findUnique|findFirst|create|update|delete|upsert|count|aggregate)',
        r'prisma\.\$(?:queryRaw|executeRaw)',
    ],
    'typeorm': [
        r'\.(?:find|findOne|findAndCount|save|update|delete|remove|insert|query)',
        r'createQueryBuilder\(',
    ],
    'sequelize': [
        r'\.(?:findAll|findOne|findByPk|create|update|destroy|count|bulkCreate)',
        r'sequelize\.query\(',
    ],
    
    # JavaScript/TypeScript - NoSQL
    'mongoose': [
        r'\.(?:find|findOne|findById|create|updateOne|deleteOne|aggregate)',
    ],
    'mongodb': [
        r'\.(?:find|findOne|insertOne|updateOne|deleteOne|aggregate)',
    ],
    'redis': [
        r'redis\.(?:get|set|setex|del|hget|hset|lpush|rpush|zadd)',
    ],
    
    # JavaScript/TypeScript - VectorDB
    'pinecone': [
        r'index\.(?:query|upsert|delete|fetch|update)',
        r'pinecone\.(?:createIndex|describeIndex)',
    ],
    'chromadb': [
        r'collection\.(?:query|add|update|delete|get)',
    ],
    'weaviate': [
        r'client\.(?:query|data)\.(?:get|create|update|delete)',
    ],
    
    # JavaScript/TypeScript - GraphDB
    'neo4j': [
        r'session\.(?:run|readTransaction|writeTransaction)',
        r'MATCH\s+\(',
        r'CREATE\s+\(',
    ],
    'arangodb': [
        r'db\._query\(',
        r'FOR\s+\w+\s+IN\s+',
    ],
    
    # Knex (SQL Query Builder)
    'knex': [
        r'knex\([\'"`]\w+[\'"`]\)',
        r'\.(?:select|insert|update|delete|where|join)',
    ],
    
    # Python - SQL
    'sqlalchemy': [
        r'session\.(?:query|add|commit|delete|execute)',
        r'\.(?:filter|filter_by|all|first|one|join|group_by|order_by)',
    ],
    'django': [
        r'\.objects\.(?:all|get|filter|create|update|delete|bulk_create)',
        r'\.save\(',
        r'Q\(',
    ],
    'peewee': [
        r'\.(?:select|insert|update|delete|where|join|get|create)',
    ],
    
    # Python - NoSQL
    'pymongo': [
        r'collection\.(?:find|find_one|insert_one|update_one|delete_one|aggregate)',
    ],
    'redis-py': [
        r'redis\.(?:get|set|setex|delete|hget|hset)',
    ],
    
    # Python - VectorDB
    'pinecone-python': [
        r'index\.(?:query|upsert|delete|fetch|update)',
    ],
    'chromadb-python': [
        r'collection\.(?:query|add|update|delete|get)',
    ],
    'weaviate-python': [
        r'client\.(?:query|data_object)\.(?:get|create)',
    ],
    'milvus': [
        r'collection\.(?:query|search|insert|delete)',
    ],
    'qdrant': [
        r'client\.(?:search|upsert|delete|retrieve)',
    ],
    
    # Python - GraphDB
    'neo4j-python': [
        r'session\.(?:run|read_transaction|write_transaction)',
    ],
    'pyarango': [
        r'db\.AQLQuery\(',
    ],
    
    # Ruby
    'activerecord': [
        r'\.(?:find|find_by|where|create|update|destroy|all|first|last)',
    ],
    
    # Go
    'gorm': [
        r'\.(?:Find|First|Last|Create|Update|Delete|Where|Joins)',
    ],
    
    # Java
    'jpa': [
        r'entityManager\.(?:find|persist|merge|remove|createQuery)',
        r'@Query',
    ],
}

class QueryFinder:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.queries = []
        
    def scan_project(self, extensions: List[str] = None) -> List[Dict]:
        """Scan project for database queries"""
        if extensions is None:
            extensions = ['.js', '.ts', '.py', '.rb', '.go', '.java', '.php']
        
        for ext in extensions:
            for file_path in self.project_path.rglob(f'*{ext}'):
                # Skip node_modules, venv, etc.
                if any(skip in str(file_path) for skip in ['node_modules', 'venv', '__pycache__', '.git', 'dist', 'build']):
                    continue
                
                self.analyze_file(file_path)
        
        return self.queries
    
    def analyze_file(self, file_path: Path):
        """Analyze a single file for queries"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Find raw SQL queries
            self.find_raw_sql(file_path, content, lines)
            
            # Find ORM queries
            self.find_orm_queries(file_path, content, lines)
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    def find_raw_sql(self, file_path: Path, content: str, lines: List[str]):
        """Find raw SQL queries in strings"""
        # Pattern for SQL in strings (single/double/template quotes)
        sql_pattern = r'["\`\'](.*?(?:' + '|'.join(SQL_KEYWORDS) + r').*?)["\`\']'
        
        for match in re.finditer(sql_pattern, content, re.IGNORECASE | re.DOTALL):
            query_text = match.group(1)
            
            # Skip if it's just a keyword in a comment
            if len(query_text) < 10:
                continue
            
            # Find line number
            line_num = content[:match.start()].count('\n') + 1
            
            # Check for SQL injection risk (string interpolation/concatenation)
            has_interpolation = self.check_sql_injection_risk(query_text, lines, line_num)
            
            self.queries.append({
                'type': 'raw_sql',
                'file': str(file_path.relative_to(self.project_path)),
                'line': line_num,
                'query': query_text[:200],  # Truncate long queries
                'sql_injection_risk': has_interpolation,
                'context': lines[max(0, line_num-2):min(len(lines), line_num+2)]
            })
    
    def find_orm_queries(self, file_path: Path, content: str, lines: List[str]):
        """Find ORM method calls"""
        for orm, patterns in ORM_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, content):
                    line_num = content[:match.start()].count('\n') + 1
                    
                    self.queries.append({
                        'type': f'orm_{orm}',
                        'file': str(file_path.relative_to(self.project_path)),
                        'line': line_num,
                        'query': match.group(0),
                        'context': lines[max(0, line_num-1):min(len(lines), line_num+1)]
                    })
    
    def check_sql_injection_risk(self, query: str, lines: List[str], line_num: int) -> bool:
        """Check if query uses string interpolation (injection risk)"""
        # Template literals with ${}, f-strings, string concatenation
        injection_patterns = [
            r'\$\{',  # JavaScript template literal
            r'\%s',   # Python old-style formatting
            r'\{.*?\}',  # Python f-string or .format()
            r'\+.*?["\']',  # String concatenation
        ]
        
        # Check the query and surrounding lines
        context = '\n'.join(lines[max(0, line_num-2):min(len(lines), line_num+2)])
        
        return any(re.search(pattern, context) for pattern in injection_patterns)
    
    def generate_report(self) -> str:
        """Generate a summary report"""
        total = len(self.queries)
        raw_sql = len([q for q in self.queries if q['type'] == 'raw_sql'])
        injection_risks = len([q for q in self.queries if q.get('sql_injection_risk')])
        
        # Categorize by DB type
        sql_dbs = ['prisma', 'typeorm', 'sequelize', 'sqlalchemy', 'django', 'peewee', 'activerecord', 'gorm', 'jpa', 'knex']
        nosql_dbs = ['mongoose', 'mongodb', 'pymongo', 'redis', 'redis-py']
        vector_dbs = ['pinecone', 'chromadb', 'weaviate', 'milvus', 'qdrant', 'pinecone-python', 'chromadb-python', 'weaviate-python']
        graph_dbs = ['neo4j', 'arangodb', 'neo4j-python', 'pyarango']
        
        sql_queries = len([q for q in self.queries if any(db in q['type'] for db in sql_dbs)])
        nosql_queries = len([q for q in self.queries if any(db in q['type'] for db in nosql_dbs)])
        vector_queries = len([q for q in self.queries if any(db in q['type'] for db in vector_dbs)])
        graph_queries = len([q for q in self.queries if any(db in q['type'] for db in graph_dbs)])
        
        report = f"""
Query Analysis Report
=====================
Total queries found: {total}
Raw SQL queries: {raw_sql}
ORM queries: {total - raw_sql}
SQL injection risks: {injection_risks}

By Database Type:
  SQL databases: {sql_queries}
  NoSQL databases: {nosql_queries}
  VectorDB: {vector_queries}
  GraphDB: {graph_queries}

Files with most queries:
"""
        # Group by file
        file_counts = {}
        for q in self.queries:
            file_counts[q['file']] = file_counts.get(q['file'], 0) + 1
        
        for file, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            report += f"  {file}: {count} queries\n"
        
        return report


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python find_queries.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    print(f"Scanning {project_path} for database queries...")
    finder = QueryFinder(project_path)
    queries = finder.scan_project()
    
    # Save results
    output_file = 'queries_found.json'
    with open(output_file, 'w') as f:
        json.dump(queries, f, indent=2)
    
    print(finder.generate_report())
    print(f"\nDetailed results saved to {output_file}")


if __name__ == '__main__':
    main()
