#!/usr/bin/env python3
"""
Detect N+1 query patterns in source code.
Identifies loops with database queries inside.
"""

import re
import ast
from pathlib import Path
from typing import List, Dict


class NPlusOneDetector:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.n_plus_one_patterns = []
        
    def scan_project(self) -> List[Dict]:
        """Scan project for N+1 patterns"""
        # JavaScript/TypeScript files
        for ext in ['.js', '.ts', '.jsx', '.tsx']:
            for file_path in self.project_path.rglob(f'*{ext}'):
                if 'node_modules' in str(file_path):
                    continue
                self.analyze_js_file(file_path)
        
        # Python files
        for file_path in self.project_path.rglob('*.py'):
            if any(skip in str(file_path) for skip in ['venv', '__pycache__', '.git']):
                continue
            self.analyze_python_file(file_path)
        
        return self.n_plus_one_patterns
    
    def analyze_js_file(self, file_path: Path):
        """Analyze JavaScript/TypeScript for N+1 patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except:
            return
        
        # Pattern 1: for/forEach with await query inside
        loop_patterns = [
            (r'for\s*\([^)]+of\s+(\w+)\)', 'for-of'),
            (r'\.forEach\(\s*(?:async\s*)?\(?\s*(\w+)', 'forEach'),
            (r'\.map\(\s*(?:async\s*)?\(?\s*(\w+)', 'map'),
            (r'for\s*\(.*?<\s*(\w+)\.length', 'for-loop'),
        ]
        
        for pattern, loop_type in loop_patterns:
            for match in re.finditer(pattern, content):
                loop_start = match.start()
                line_num = content[:loop_start].count('\n') + 1
                
                # Find the block of this loop
                block_end = self.find_block_end(content, loop_start)
                if block_end == -1:
                    continue
                
                block = content[loop_start:block_end]
                
                # Check for query patterns in the block
                if self.has_query_pattern(block):
                    # Extract context
                    context_start = max(0, line_num - 2)
                    context_end = min(len(lines), line_num + 10)
                    
                    self.n_plus_one_patterns.append({
                        'file': str(file_path.relative_to(self.project_path)),
                        'line': line_num,
                        'loop_type': loop_type,
                        'severity': 'HIGH',
                        'message': f'Potential N+1 query in {loop_type} loop',
                        'context': lines[context_start:context_end],
                        'suggestion': 'Use JOIN, eager loading, or dataloader pattern'
                    })
    
    def analyze_python_file(self, file_path: Path):
        """Analyze Python for N+1 patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            tree = ast.parse(content)
        except:
            return
        
        # Find for loops
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Check if there are query calls in the loop body
                for child in ast.walk(node):
                    if self.is_query_call(child):
                        line_num = node.lineno
                        
                        # Extract context
                        context_start = max(0, line_num - 2)
                        context_end = min(len(lines), line_num + 10)
                        
                        self.n_plus_one_patterns.append({
                            'file': str(file_path.relative_to(self.project_path)),
                            'line': line_num,
                            'loop_type': 'for',
                            'severity': 'HIGH',
                            'message': 'Potential N+1 query in for loop',
                            'context': lines[context_start:context_end],
                            'suggestion': 'Use select_related/prefetch_related or join'
                        })
                        break  # Only report once per loop
    
    def find_block_end(self, content: str, start: int) -> int:
        """Find the end of a code block (simplified)"""
        # Look for opening brace
        open_brace = content.find('{', start)
        if open_brace == -1:
            return -1
        
        # Count braces to find matching close
        brace_count = 1
        pos = open_brace + 1
        
        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            pos += 1
        
        return pos if brace_count == 0 else -1
    
    def has_query_pattern(self, code_block: str) -> bool:
        """Check if code block contains query patterns"""
        query_indicators = [
            r'await\s+\w+\.(?:find|get|query|execute)',
            r'\.findOne\(',
            r'\.findMany\(',
            r'\.findById\(',
            r'\.query\(',
            r'\.get\(',
            r'\.filter\(',
            r'SELECT\s+',
            r'session\.query\(',
        ]
        
        return any(re.search(pattern, code_block, re.IGNORECASE) for pattern in query_indicators)
    
    def is_query_call(self, node) -> bool:
        """Check if AST node is a query call"""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                # Check method name
                method_names = ['filter', 'get', 'all', 'first', 'query', 'execute']
                if node.func.attr in method_names:
                    return True
        return False
    
    def generate_report(self) -> str:
        """Generate summary report"""
        if not self.n_plus_one_patterns:
            return "✅ No N+1 query patterns detected!"
        
        report = f"""
N+1 Query Pattern Detection Report
===================================
Total patterns found: {len(self.n_plus_one_patterns)}

Issues by severity:
  HIGH: {len([p for p in self.n_plus_one_patterns if p['severity'] == 'HIGH'])}

Files with N+1 patterns:
"""
        
        # Group by file
        by_file = {}
        for pattern in self.n_plus_one_patterns:
            file = pattern['file']
            by_file[file] = by_file.get(file, 0) + 1
        
        for file, count in sorted(by_file.items(), key=lambda x: x[1], reverse=True):
            report += f"  {file}: {count} pattern(s)\n"
        
        report += "\n⚠️  These patterns may cause performance issues under load.\n"
        report += "Consider using eager loading, JOINs, or DataLoader pattern.\n"
        
        return report


def main():
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python detect_n_plus_one.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    print(f"Scanning {project_path} for N+1 query patterns...")
    detector = NPlusOneDetector(project_path)
    patterns = detector.scan_project()
    
    # Save results
    output_file = 'n_plus_one_patterns.json'
    with open(output_file, 'w') as f:
        json.dump(patterns, f, indent=2)
    
    print(detector.generate_report())
    print(f"\nDetailed results saved to {output_file}")
    
    if patterns:
        print("\nSample issues:")
        for pattern in patterns[:3]:
            print(f"\n📍 {pattern['file']}:{pattern['line']}")
            print(f"   {pattern['message']}")
            print(f"   💡 {pattern['suggestion']}")


if __name__ == '__main__':
    main()
