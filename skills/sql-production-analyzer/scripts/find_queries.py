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
    # JavaScript/TypeScript - SQL ORMs
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
    'knex': [
        r'knex\([\'"`]\w+[\'"`]\)',
        r'\.(?:select|insert|update|delete|where|join)',
    ],
    'drizzle': [
        r'db\.(?:select|insert|update|delete)',
        r'\.from\(',
    ],

    # Python - SQL ORMs
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
    'tortoise': [
        r'\.(?:filter|all|get|create|update|delete|first)',
        r'await\s+\w+\.save\(',
    ],

    # Python - Async Raw SQL Drivers
    'aiomysql': [
        r'await\s+\w+\.execute\(',
        r'await\s+\w+\.executemany\(',
        r'pool\.acquire\(',
        r'aiomysql\.create_pool\(',
        r'cursor\.fetchone\(',
        r'cursor\.fetchall\(',
    ],
    'asyncpg': [
        r'await\s+\w+\.fetch\(',
        r'await\s+\w+\.fetchrow\(',
        r'await\s+\w+\.execute\(',
        r'asyncpg\.create_pool\(',
        r'pool\.acquire\(',
    ],
    'pymysql': [
        r'cursor\.execute\(',
        r'cursor\.executemany\(',
        r'pymysql\.connect\(',
        r'connection\.cursor\(',
    ],

    # Ruby - SQL
    'activerecord': [
        r'\.(?:find|find_by|where|create|update|destroy|all|first|last)',
    ],

    # Go - SQL
    'gorm': [
        r'\.(?:Find|First|Last|Create|Update|Delete|Where|Joins)',
    ],

    # Java - SQL
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
        
        # Categorize by ORM framework
        js_orms = ['prisma', 'typeorm', 'sequelize', 'knex', 'drizzle']
        py_orms = ['sqlalchemy', 'django', 'peewee', 'tortoise', 'aiomysql', 'asyncpg', 'pymysql']
        other_orms = ['activerecord', 'gorm', 'jpa']

        js_queries = len([q for q in self.queries if any(orm in q['type'] for orm in js_orms)])
        py_queries = len([q for q in self.queries if any(orm in q['type'] for orm in py_orms)])
        other_queries = len([q for q in self.queries if any(orm in q['type'] for orm in other_orms)])

        report = f"""
SQL Query Analysis Report
=========================
Total queries found: {total}
Raw SQL queries: {raw_sql}
ORM queries: {total - raw_sql}
SQL injection risks: {injection_risks}

By ORM Framework:
  JavaScript/TypeScript (Prisma, TypeORM, Sequelize, Knex, Drizzle): {js_queries}
  Python (SQLAlchemy, Django, Peewee, Tortoise, aiomysql, asyncpg, pymysql): {py_queries}
  Other (ActiveRecord, GORM, JPA): {other_queries}

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
