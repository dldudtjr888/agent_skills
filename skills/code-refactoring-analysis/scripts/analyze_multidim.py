#!/usr/bin/env python3
"""
Multi-Dimensional Code Analysis for Python Projects
Analyzes code across 5 dimensions: Maintainability, Performance, Security, Scalability, Reusability
"""

import argparse
import ast
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Check for required packages
REQUIRED_PACKAGES = {
    'maintainability': ['radon', 'pylint', 'rope'],
    'performance': ['line_profiler', 'memory_profiler'],
    'security': ['bandit', 'safety'],
    'scalability': ['pydeps'],
    'reusability': ['pylint']  # Uses similarity checker
}

def check_package_installed(package: str) -> bool:
    """Check if a Python package is installed"""
    spec = importlib.util.find_spec(package.replace('-', '_'))
    return spec is not None

def check_dependencies(dimensions: List[str]) -> Dict[str, bool]:
    """Check which analysis tools are available"""
    available = {}
    
    for dim in dimensions:
        if dim not in REQUIRED_PACKAGES:
            continue
        
        dim_available = True
        for pkg in REQUIRED_PACKAGES[dim]:
            if not check_package_installed(pkg):
                print(f"⚠️  {pkg} not installed - {dim} analysis may be limited")
                dim_available = False
        
        available[dim] = dim_available
    
    return available


class MultiDimensionalAnalyzer:
    """Analyzes Python code across multiple dimensions"""

    VERSION = "1.1.0"

    def __init__(self, project_path: str, dimensions: List[str]):
        self.project_path = Path(project_path)
        self.dimensions = dimensions
        self.tools_used = []
        self.tools_failed = []
        self.files_analyzed = 0
        self.files_skipped = 0
        self.results = {
            'meta': {
                'analyzer_version': self.VERSION,
                'tools_used': [],
                'tools_failed': [],
                'coverage': {'files_analyzed': 0, 'files_skipped': 0},
                'confidence': 1.0
            },
            'project': str(project_path),
            'dimensions': {},
            'overall_health': 0,
            'priority_actions': []
        }

    def _track_tool(self, tool_name: str, success: bool, reason: str = None):
        """Track tool usage for meta output"""
        if success:
            if tool_name not in self.tools_used:
                self.tools_used.append(tool_name)
        else:
            if tool_name not in [t['tool'] for t in self.tools_failed]:
                self.tools_failed.append({'tool': tool_name, 'reason': reason or 'unknown'})

    def _finalize_meta(self):
        """Update meta section with final tracking data"""
        self.results['meta']['tools_used'] = self.tools_used
        self.results['meta']['tools_failed'] = [t['tool'] for t in self.tools_failed]
        self.results['meta']['coverage'] = {
            'files_analyzed': self.files_analyzed,
            'files_skipped': self.files_skipped
        }
        # Calculate confidence based on tool availability
        expected_tools = ['radon', 'bandit', 'pylint', 'pydeps']
        available_count = len([t for t in expected_tools if t in self.tools_used])
        failed_count = len(self.tools_failed)
        self.results['meta']['confidence'] = round(
            max(0.5, 1.0 - (failed_count * 0.1) - ((4 - available_count) * 0.05)), 2
        )

    def analyze(self) -> Dict[str, Any]:
        """Run analysis for all requested dimensions"""
        print(f"\n🔍 Analyzing {self.project_path} across {len(self.dimensions)} dimensions...\n")
        
        if 'maintainability' in self.dimensions:
            self.results['dimensions']['maintainability'] = self.analyze_maintainability()
        
        if 'performance' in self.dimensions:
            self.results['dimensions']['performance'] = self.analyze_performance()
        
        if 'security' in self.dimensions:
            self.results['dimensions']['security'] = self.analyze_security()
        
        if 'scalability' in self.dimensions:
            self.results['dimensions']['scalability'] = self.analyze_scalability()
        
        if 'reusability' in self.dimensions:
            self.results['dimensions']['reusability'] = self.analyze_reusability()
        
        # Calculate overall health
        self._calculate_overall_health()

        # Generate priority actions
        self._generate_priority_actions()

        # Finalize meta information
        self._finalize_meta()

        return self.results
    
    def analyze_maintainability(self) -> Dict[str, Any]:
        """Analyze maintainability dimension"""
        print("🔧 Analyzing Maintainability...")
        
        result = {
            'score': 0,
            'coverage': 'comprehensive',
            'metrics': {},
            'issues': []
        }
        
        # Run Radon for complexity
        try:
            radon_output = subprocess.run(
                ['radon', 'cc', str(self.project_path), '-a', '--json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if radon_output.returncode == 0:
                self._track_tool('radon', True)
                complexity_data = json.loads(radon_output.stdout)

                # Calculate average complexity
                total_complexity = 0
                func_count = 0
                high_complexity = []

                for file, functions in complexity_data.items():
                    self.files_analyzed += 1
                    for func in functions:
                        total_complexity += func.get('complexity', 0)
                        func_count += 1

                        if func.get('complexity', 0) > 10:
                            high_complexity.append({
                                'file': file,
                                'function': func.get('name'),
                                'complexity': func.get('complexity'),
                                'line': func.get('lineno')
                            })

                avg_complexity = total_complexity / func_count if func_count > 0 else 0
                result['metrics']['average_complexity'] = round(avg_complexity, 2)
                result['metrics']['high_complexity_functions'] = len(high_complexity)
                result['issues'].extend(high_complexity)

                # Score based on complexity
                if avg_complexity <= 5:
                    result['score'] = 100
                elif avg_complexity <= 10:
                    result['score'] = 80
                elif avg_complexity <= 15:
                    result['score'] = 60
                else:
                    result['score'] = 40
            else:
                self._track_tool('radon', False, 'non-zero exit code')

        except Exception as e:
            self._track_tool('radon', False, str(e))
            print(f"  Warning: Radon analysis failed - {e}")
        
        # Run Radon for maintainability index
        try:
            radon_mi = subprocess.run(
                ['radon', 'mi', str(self.project_path), '--json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if radon_mi.returncode == 0:
                mi_data = json.loads(radon_mi.stdout)
                
                mi_scores = []
                for file, data in mi_data.items():
                    mi_scores.append(data.get('mi', 0))
                
                avg_mi = sum(mi_scores) / len(mi_scores) if mi_scores else 0
                result['metrics']['maintainability_index'] = round(avg_mi, 2)
                
        except Exception as e:
            print(f"  Warning: MI calculation failed - {e}")
        
        print(f"  ✓ Maintainability score: {result['score']}/100")
        return result
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance dimension"""
        print("⚡ Analyzing Performance...")

        result = {
            'score': 100,  # Start with perfect score
            'bottlenecks': [],
            'improvements': [],
            'algorithmic_issues': [],
            'metrics': {
                'nested_loops': 0,
                'sync_operations': 0,
                'memory_risks': 0,
                'inefficient_patterns': 0
            }
        }

        python_files = list(self.project_path.rglob('*.py'))
        # Skip common non-source directories
        python_files = [f for f in python_files if not any(
            part in str(f) for part in ['venv', '.venv', '__pycache__', 'node_modules', '.git', 'build', 'dist']
        )]

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)

                relative_path = str(py_file.relative_to(self.project_path))

                # Nested loops (O(n²) complexity)
                nested_loops = self._find_nested_loops(tree, relative_path)
                result['algorithmic_issues'].extend(nested_loops)
                result['metrics']['nested_loops'] += len(nested_loops)

                # Synchronous blocking operations
                sync_issues = self._find_sync_operations(content, relative_path)
                result['bottlenecks'].extend(sync_issues)
                result['metrics']['sync_operations'] += len(sync_issues)

                # Memory risk patterns
                memory_issues = self._find_memory_risks(tree, content, relative_path)
                result['bottlenecks'].extend(memory_issues)
                result['metrics']['memory_risks'] += len(memory_issues)

                # Inefficient patterns
                inefficient = self._find_inefficient_patterns(tree, content, relative_path)
                result['algorithmic_issues'].extend(inefficient)
                result['metrics']['inefficient_patterns'] += len(inefficient)

            except Exception:
                continue

        # Calculate score
        total_issues = (
            len(result['algorithmic_issues']) +
            len(result['bottlenecks'])
        )

        # Severity-based scoring
        high_severity = sum(1 for i in result['algorithmic_issues'] + result['bottlenecks']
                          if i.get('severity') == 'high')
        medium_severity = sum(1 for i in result['algorithmic_issues'] + result['bottlenecks']
                             if i.get('severity') == 'medium')
        low_severity = sum(1 for i in result['algorithmic_issues'] + result['bottlenecks']
                          if i.get('severity') == 'low')

        penalty = (high_severity * 8) + (medium_severity * 3) + (low_severity * 1)
        result['score'] = max(20, 100 - penalty)

        print(f"  ✓ Performance score: {result['score']}/100")
        print(f"  Found {total_issues} performance issues")
        print(f"    - High severity: {high_severity}")
        print(f"    - Medium severity: {medium_severity}")
        print(f"    - Low severity: {low_severity}")

        return result

    def _find_nested_loops(self, tree: ast.AST, filename: str) -> List[Dict]:
        """Find nested loops that may indicate O(n²) complexity"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Check if there's a nested loop
                for child in ast.walk(node):
                    if child != node and isinstance(child, (ast.For, ast.While)):
                        issues.append({
                            'file': filename,
                            'line': node.lineno,
                            'type': 'nested_loop',
                            'message': 'Nested loop detected - potential O(n²) complexity',
                            'severity': 'medium'
                        })
                        break

        return issues

    def _find_sync_operations(self, content: str, filename: str) -> List[Dict]:
        """Find synchronous blocking operations"""
        import re
        issues = []

        patterns = [
            (r'time\.sleep\s*\(', 'time.sleep() blocks thread', 'medium'),
            (r'subprocess\.run\s*\([^)]*\)', 'subprocess.run() blocks execution', 'low'),
            (r'os\.system\s*\(', 'os.system() blocks and is security risk', 'high'),
            (r'urllib\.request\.urlopen\s*\(', 'Synchronous HTTP request', 'medium'),
            (r'requests\.(get|post|put|delete|patch)\s*\(', 'Synchronous HTTP request', 'low'),
            (r'input\s*\(', 'input() blocks waiting for user', 'low'),
        ]

        lines = content.split('\n')
        for pattern, message, severity in patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': filename,
                    'line': line_num,
                    'type': 'sync_operation',
                    'message': message,
                    'severity': severity,
                    'code': lines[line_num - 1].strip()[:80] if line_num <= len(lines) else ''
                })

        return issues

    def _find_memory_risks(self, tree: ast.AST, content: str, filename: str) -> List[Dict]:
        """Find potential memory leak patterns"""
        import re
        issues = []
        lines = content.split('\n')

        # Check for large list comprehensions without limits
        for node in ast.walk(tree):
            if isinstance(node, ast.ListComp):
                # Check if iterating over potentially large generator
                if hasattr(node, 'lineno'):
                    line_content = lines[node.lineno - 1] if node.lineno <= len(lines) else ''
                    if 'range(' in line_content and not any(x in line_content for x in ['[:',  'limit', 'max']):
                        issues.append({
                            'file': filename,
                            'line': node.lineno,
                            'type': 'memory_risk',
                            'message': 'List comprehension may create large list in memory',
                            'severity': 'low',
                            'code': line_content.strip()[:80]
                        })

        # Global variable accumulation
        global_patterns = [
            (r'^[A-Z_]+\s*=\s*\[\]', 'Global list that may accumulate data'),
            (r'^[A-Z_]+\s*=\s*\{\}', 'Global dict that may accumulate data'),
        ]

        for pattern, message in global_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': filename,
                    'line': line_num,
                    'type': 'memory_risk',
                    'message': message,
                    'severity': 'low'
                })

        return issues

    def _find_inefficient_patterns(self, tree: ast.AST, content: str, filename: str) -> List[Dict]:
        """Find inefficient code patterns"""
        import re
        issues = []

        # String concatenation in loop
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.Add):
                        if isinstance(child.target, ast.Name):
                            issues.append({
                                'file': filename,
                                'line': child.lineno,
                                'type': 'inefficient_string',
                                'message': 'String concatenation in loop - consider list.append and join',
                                'severity': 'low'
                            })

        # Repeated regex compilation
        regex_patterns = [
            (r're\.(match|search|findall|sub)\s*\([^,]+,', 'Regex pattern compiled on each call - consider re.compile()'),
        ]

        for pattern, message in regex_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': filename,
                    'line': line_num,
                    'type': 'inefficient_regex',
                    'message': message,
                    'severity': 'low'
                })

        # Inefficient list operations
        inefficient_list = [
            (r'\.append\([^)]+\)\s*$.*\n.*\.append\([^)]+\)\s*$', 'Multiple appends - consider extend()'),
            (r'if\s+\w+\s+in\s+\[[^\]]+\]:', 'Membership test on list literal - use set or tuple'),
        ]

        for pattern, message in inefficient_list:
            for match in re.finditer(pattern, content, re.MULTILINE):
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': filename,
                    'line': line_num,
                    'type': 'inefficient_list',
                    'message': message,
                    'severity': 'low'
                })

        return issues
    
    def analyze_security(self) -> Dict[str, Any]:
        """Analyze security dimension"""
        print("🔒 Analyzing Security...")

        result = {
            'score': 100,  # Start with perfect score
            'vulnerabilities': [],
            'static_issues': [],
            'severity': 'none',
            'metrics': {
                'bandit_issues': 0,
                'static_pattern_issues': 0,
                'dependency_issues': 0
            }
        }

        # Run Bandit for security issues
        try:
            bandit_output = subprocess.run(
                ['bandit', '-r', str(self.project_path), '-f', 'json'],
                capture_output=True,
                text=True,
                timeout=60
            )

            # Bandit returns non-zero when it finds issues
            if bandit_output.stdout:
                self._track_tool('bandit', True)
                bandit_data = json.loads(bandit_output.stdout)

                vulnerabilities = bandit_data.get('results', [])
                result['vulnerabilities'] = [
                    {
                        'file': v.get('filename'),
                        'line': v.get('line_number'),
                        'severity': v.get('issue_severity'),
                        'confidence': v.get('issue_confidence'),
                        'message': v.get('issue_text'),
                        'cwe': v.get('issue_cwe', {}).get('id'),
                        'source': 'bandit'
                    }
                    for v in vulnerabilities
                ]
                result['metrics']['bandit_issues'] = len(result['vulnerabilities'])
            else:
                self._track_tool('bandit', False, 'no output')

        except FileNotFoundError:
            self._track_tool('bandit', False, 'not installed')
            print("  ⚠️  Bandit not installed - using static pattern analysis")
        except Exception as e:
            self._track_tool('bandit', False, str(e))
            print(f"  Warning: Bandit analysis failed - {e}")

        # Always run static security pattern analysis (supplements Bandit)
        python_files = list(self.project_path.rglob('*.py'))
        python_files = [f for f in python_files if not any(
            part in str(f) for part in ['venv', '.venv', '__pycache__', 'node_modules', '.git', 'build', 'dist', 'test']
        )]

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                relative_path = str(py_file.relative_to(self.project_path))

                # Static security patterns
                static_issues = self._find_security_patterns(content, relative_path)
                result['static_issues'].extend(static_issues)

            except Exception:
                continue

        result['metrics']['static_pattern_issues'] = len(result['static_issues'])

        # Check for safety (dependency vulnerabilities)
        try:
            safety_output = subprocess.run(
                ['safety', 'check', '--json'],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.project_path)
            )

            if safety_output.stdout:
                safety_data = json.loads(safety_output.stdout)
                if safety_data:
                    result['vulnerabilities'].append({
                        'type': 'dependency',
                        'count': len(safety_data),
                        'message': f'Found {len(safety_data)} vulnerable dependencies',
                        'source': 'safety'
                    })
                    result['metrics']['dependency_issues'] = len(safety_data)

        except FileNotFoundError:
            pass  # Safety not installed, skip
        except Exception as e:
            print(f"  Warning: Safety check failed - {e}")

        # Calculate score based on all findings
        all_issues = result['vulnerabilities'] + result['static_issues']

        high_severity = sum(1 for v in all_issues if v.get('severity') in ['HIGH', 'high'])
        medium_severity = sum(1 for v in all_issues if v.get('severity') in ['MEDIUM', 'medium'])
        low_severity = sum(1 for v in all_issues if v.get('severity') in ['LOW', 'low'])

        # Severity-based scoring
        penalty = (high_severity * 15) + (medium_severity * 5) + (low_severity * 1)
        result['score'] = max(20, 100 - penalty)

        if high_severity > 0:
            result['severity'] = 'high'
        elif medium_severity > 0:
            result['severity'] = 'medium'
        elif low_severity > 0:
            result['severity'] = 'low'
        else:
            result['severity'] = 'none'

        print(f"  ✓ Security score: {result['score']}/100")
        print(f"  Found {len(all_issues)} security issues")
        print(f"    - Bandit: {result['metrics']['bandit_issues']}")
        print(f"    - Static patterns: {result['metrics']['static_pattern_issues']}")
        print(f"    - Dependencies: {result['metrics']['dependency_issues']}")

        return result

    def _find_security_patterns(self, content: str, filename: str) -> List[Dict]:
        """Find security issues via static pattern analysis"""
        import re
        issues = []
        lines = content.split('\n')

        # Security patterns to detect
        patterns = [
            # SQL Injection risks
            (r'execute\s*\(\s*["\'].*%s.*["\']', 'Potential SQL injection - use parameterized queries', 'high'),
            (r'execute\s*\(\s*f["\']', 'Potential SQL injection with f-string', 'high'),
            (r'execute\s*\(\s*["\'].*\+', 'Potential SQL injection with string concatenation', 'high'),
            (r'cursor\.execute\s*\(\s*[^,]+\s*%\s*', 'Potential SQL injection with % formatting', 'high'),

            # Command Injection risks
            (r'os\.system\s*\(', 'os.system() is vulnerable to command injection - use subprocess', 'high'),
            (r'os\.popen\s*\(', 'os.popen() is vulnerable to command injection', 'high'),
            (r'subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True', 'shell=True enables command injection', 'high'),
            (r'eval\s*\(', 'eval() can execute arbitrary code', 'high'),
            (r'exec\s*\(', 'exec() can execute arbitrary code', 'high'),

            # Hardcoded credentials
            (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password detected', 'high'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key detected', 'high'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret detected', 'high'),
            (r'token\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']', 'Potential hardcoded token', 'medium'),
            (r'AWS_SECRET_ACCESS_KEY\s*=\s*["\']', 'Hardcoded AWS credentials', 'high'),

            # Unsafe deserialization
            (r'pickle\.loads?\s*\(', 'Unsafe pickle deserialization - can execute arbitrary code', 'high'),
            (r'yaml\.load\s*\([^)]*\)(?!\s*,\s*Loader)', 'Unsafe YAML load - use yaml.safe_load()', 'high'),
            (r'marshal\.loads?\s*\(', 'Unsafe marshal deserialization', 'medium'),

            # Path traversal
            (r'open\s*\([^)]*\+[^)]*\)', 'Potential path traversal - validate file paths', 'medium'),
            (r'os\.path\.join\s*\([^)]*request', 'Potential path traversal with user input', 'medium'),

            # Insecure random
            (r'random\.(random|randint|choice|randrange)\s*\(', 'Insecure random for security use - use secrets module', 'low'),

            # Debug/Assert in production
            (r'^assert\s+', 'Assert can be disabled with -O flag', 'low'),
            (r'app\.run\s*\([^)]*debug\s*=\s*True', 'Debug mode enabled - disable in production', 'medium'),

            # Weak cryptography
            (r'hashlib\.(md5|sha1)\s*\(', 'Weak hash algorithm - use SHA-256 or better', 'medium'),
            (r'from\s+Crypto\.Cipher\s+import\s+DES', 'DES is weak - use AES', 'high'),

            # SSRF potential
            (r'requests\.(get|post)\s*\([^)]*\+', 'Potential SSRF with dynamic URL', 'medium'),
            (r'urllib\.request\.urlopen\s*\([^)]*\+', 'Potential SSRF with dynamic URL', 'medium'),

            # Temporary file issues
            (r'tempfile\.mktemp\s*\(', 'mktemp is insecure - use mkstemp()', 'medium'),

            # XML vulnerabilities
            (r'xml\.etree\.ElementTree\.parse\s*\(', 'XML parsing may be vulnerable to XXE', 'low'),
            (r'lxml\.etree\.parse\s*\(', 'XML parsing may be vulnerable to XXE', 'low'),
        ]

        for pattern, message, severity in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': filename,
                    'line': line_num,
                    'severity': severity,
                    'message': message,
                    'code': lines[line_num - 1].strip()[:80] if line_num <= len(lines) else '',
                    'source': 'static_analysis'
                })

        return issues
    
    def analyze_scalability(self) -> Dict[str, Any]:
        """Analyze scalability/extensibility dimension"""
        print("📈 Analyzing Scalability...")

        result = {
            'score': 100,  # Start with perfect score
            'coupling_issues': [],
            'solid_violations': [],
            'circular_dependencies': [],
            'metrics': {
                'god_classes': 0,
                'tight_coupling': 0,
                'circular_deps': 0,
                'ocp_violations': 0,
                'dip_violations': 0
            }
        }

        # Analyze imports and dependencies
        python_files = list(self.project_path.rglob('*.py'))
        python_files = [f for f in python_files if not any(
            part in str(f) for part in ['venv', '.venv', '__pycache__', 'node_modules', '.git', 'build', 'dist']
        )]

        # Build import graph for circular dependency detection
        import_graph = {}
        module_to_file = {}

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)

                relative_path = str(py_file.relative_to(self.project_path))
                module_name = relative_path.replace('/', '.').replace('.py', '')

                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.append(node.module)

                import_graph[module_name] = imports
                module_to_file[module_name] = relative_path

            except Exception:
                continue

        # Detect circular dependencies
        circular_deps = self._detect_circular_dependencies(import_graph)
        result['circular_dependencies'] = circular_deps
        result['metrics']['circular_deps'] = len(circular_deps)

        # Detect god classes (SRP violation)
        god_classes = self._find_god_classes(python_files)
        result['solid_violations'].extend(god_classes)
        result['metrics']['god_classes'] = len(god_classes)

        # Detect tight coupling
        coupling_issues = self._find_tight_coupling(python_files)
        result['coupling_issues'].extend(coupling_issues)
        result['metrics']['tight_coupling'] = len(coupling_issues)

        # Detect OCP violations (Open/Closed Principle)
        ocp_violations = self._find_ocp_violations(python_files)
        result['solid_violations'].extend(ocp_violations)
        result['metrics']['ocp_violations'] = len(ocp_violations)

        # Detect DIP violations (Dependency Inversion Principle)
        dip_violations = self._find_dip_violations(python_files)
        result['solid_violations'].extend(dip_violations)
        result['metrics']['dip_violations'] = len(dip_violations)

        # Calculate score based on all findings
        total_issues = (
            len(result['solid_violations']) +
            len(result['coupling_issues']) +
            len(result['circular_dependencies'])
        )

        # Severity-based scoring
        circular_penalty = len(result['circular_dependencies']) * 10  # High penalty
        god_class_penalty = result['metrics']['god_classes'] * 5
        coupling_penalty = result['metrics']['tight_coupling'] * 3
        other_penalty = (result['metrics']['ocp_violations'] + result['metrics']['dip_violations']) * 2

        total_penalty = circular_penalty + god_class_penalty + coupling_penalty + other_penalty
        result['score'] = max(20, 100 - total_penalty)

        print(f"  ✓ Scalability score: {result['score']}/100")
        print(f"  Found {total_issues} scalability issues")
        print(f"    - Circular dependencies: {result['metrics']['circular_deps']}")
        print(f"    - God classes (SRP): {result['metrics']['god_classes']}")
        print(f"    - Tight coupling: {result['metrics']['tight_coupling']}")
        print(f"    - OCP violations: {result['metrics']['ocp_violations']}")
        print(f"    - DIP violations: {result['metrics']['dip_violations']}")

        return result

    def _detect_circular_dependencies(self, import_graph: Dict[str, List[str]]) -> List[Dict]:
        """Detect circular dependencies using DFS"""
        circular_deps = []
        visited = set()
        rec_stack = set()

        def dfs(module: str, path: List[str]) -> Optional[List[str]]:
            if module in rec_stack:
                # Found cycle - return the cycle path
                cycle_start = path.index(module)
                return path[cycle_start:]

            if module in visited:
                return None

            visited.add(module)
            rec_stack.add(module)
            path.append(module)

            for imported in import_graph.get(module, []):
                # Only check internal modules
                if imported in import_graph:
                    cycle = dfs(imported, path.copy())
                    if cycle:
                        return cycle

            rec_stack.remove(module)
            return None

        for module in import_graph:
            if module not in visited:
                cycle = dfs(module, [])
                if cycle:
                    circular_deps.append({
                        'cycle': cycle,
                        'message': f'Circular dependency: {" → ".join(cycle)} → {cycle[0]}',
                        'severity': 'high'
                    })

        return circular_deps

    def _find_god_classes(self, python_files: List[Path]) -> List[Dict]:
        """Find classes with too many methods (God Class anti-pattern)"""
        god_classes = []

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())

                relative_path = str(py_file.relative_to(self.project_path))

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Count methods
                        method_count = sum(1 for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)))

                        # Count class lines
                        class_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0

                        if method_count > 20 or class_lines > 500:
                            god_classes.append({
                                'file': relative_path,
                                'class': node.name,
                                'line': node.lineno,
                                'method_count': method_count,
                                'class_lines': class_lines,
                                'violation': 'Single Responsibility Principle',
                                'message': f'Class has {method_count} methods and {class_lines} lines - consider splitting',
                                'severity': 'medium'
                            })

            except Exception:
                continue

        return god_classes

    def _find_tight_coupling(self, python_files: List[Path]) -> List[Dict]:
        """Find tightly coupled classes"""
        coupling_issues = []

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)

                relative_path = str(py_file.relative_to(self.project_path))

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Count external class instantiations in __init__
                        init_instantiations = 0
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                                for child in ast.walk(item):
                                    if isinstance(child, ast.Call):
                                        if isinstance(child.func, ast.Name):
                                            # Check if it's a class instantiation (capitalized)
                                            if child.func.id[0].isupper():
                                                init_instantiations += 1

                        if init_instantiations > 5:
                            coupling_issues.append({
                                'file': relative_path,
                                'class': node.name,
                                'line': node.lineno,
                                'instantiations': init_instantiations,
                                'message': f'Class creates {init_instantiations} dependencies in __init__ - consider dependency injection',
                                'severity': 'medium'
                            })

            except Exception:
                continue

        return coupling_issues

    def _find_ocp_violations(self, python_files: List[Path]) -> List[Dict]:
        """Find Open/Closed Principle violations (long if-elif chains)"""
        import re
        violations = []

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)

                relative_path = str(py_file.relative_to(self.project_path))

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check for long elif chains
                        for child in ast.walk(node):
                            if isinstance(child, ast.If):
                                # Count elif branches
                                current = child
                                chain_length = 1
                                while current.orelse:
                                    if len(current.orelse) == 1 and isinstance(current.orelse[0], ast.If):
                                        chain_length += 1
                                        current = current.orelse[0]
                                    else:
                                        break

                                if chain_length >= 5:
                                    violations.append({
                                        'file': relative_path,
                                        'function': node.name,
                                        'line': child.lineno,
                                        'elif_count': chain_length,
                                        'violation': 'Open/Closed Principle',
                                        'message': f'Long if-elif chain ({chain_length} branches) - consider polymorphism or strategy pattern',
                                        'severity': 'low'
                                    })
                                    break  # Only report once per function

            except Exception:
                continue

        return violations

    def _find_dip_violations(self, python_files: List[Path]) -> List[Dict]:
        """Find Dependency Inversion Principle violations (concrete dependencies)"""
        violations = []

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)

                relative_path = str(py_file.relative_to(self.project_path))

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check for concrete class attributes (not dependency injection)
                        concrete_deps = []

                        for item in node.body:
                            # Class-level instantiations (not in __init__)
                            if isinstance(item, ast.Assign):
                                for target in item.targets:
                                    if isinstance(item.value, ast.Call):
                                        if isinstance(item.value.func, ast.Name):
                                            if item.value.func.id[0].isupper():
                                                concrete_deps.append(item.value.func.id)

                        if len(concrete_deps) >= 3:
                            violations.append({
                                'file': relative_path,
                                'class': node.name,
                                'line': node.lineno,
                                'concrete_deps': concrete_deps,
                                'violation': 'Dependency Inversion Principle',
                                'message': f'Class has {len(concrete_deps)} concrete dependencies at class level - use dependency injection',
                                'severity': 'low'
                            })

            except Exception:
                continue

        return violations
    
    def analyze_reusability(self) -> Dict[str, Any]:
        """Analyze reusability dimension"""
        print("♻️  Analyzing Reusability...")

        result = {
            'score': 100,  # Start with perfect score
            'duplication_percentage': 0,
            'duplicate_blocks': [],
            'dead_code': [],
            'extractable_patterns': [],
            'metrics': {
                'duplicate_blocks': 0,
                'dead_code_items': 0,
                'extractable_patterns': 0
            }
        }

        python_files = list(self.project_path.rglob('*.py'))
        python_files = [f for f in python_files if not any(
            part in str(f) for part in ['venv', '.venv', '__pycache__', 'node_modules', '.git', 'build', 'dist', 'test']
        )]

        pylint_used = False

        # Run Pylint similarity checker
        try:
            pylint_output = subprocess.run(
                ['pylint', '--disable=all', '--enable=similarities',
                 str(self.project_path), '--output-format=json'],
                capture_output=True,
                text=True,
                timeout=60
            )

            if pylint_output.stdout:
                try:
                    pylint_data = json.loads(pylint_output.stdout)

                    similar_code = [msg for msg in pylint_data if msg.get('symbol') == 'duplicate-code']
                    result['duplicate_blocks'] = [
                        {
                            'file': msg.get('path'),
                            'line': msg.get('line'),
                            'message': msg.get('message'),
                            'source': 'pylint'
                        }
                        for msg in similar_code
                    ]
                    pylint_used = True

                except json.JSONDecodeError:
                    pass

        except FileNotFoundError:
            print("  ⚠️  Pylint not installed - using hash-based duplication detection")
        except Exception as e:
            print(f"  Warning: Similarity analysis failed - {e}")

        # Fallback: Hash-based duplication detection if pylint not available
        if not pylint_used:
            hash_duplicates = self._detect_duplicates_with_hashing(python_files)
            result['duplicate_blocks'].extend(hash_duplicates)

        result['metrics']['duplicate_blocks'] = len(result['duplicate_blocks'])

        # Detect dead code (unused imports, functions, classes)
        dead_code = self._detect_dead_code(python_files)
        result['dead_code'] = dead_code
        result['metrics']['dead_code_items'] = len(dead_code)

        # Detect extractable patterns
        extractable = self._detect_extractable_patterns(python_files)
        result['extractable_patterns'] = extractable
        result['metrics']['extractable_patterns'] = len(extractable)

        # Calculate score
        duplication_penalty = len(result['duplicate_blocks']) * 3
        dead_code_penalty = len(result['dead_code']) * 1
        extractable_bonus = min(len(result['extractable_patterns']) * 2, 10)  # Bonus for identifying patterns

        total_penalty = duplication_penalty + dead_code_penalty - extractable_bonus
        result['score'] = max(20, 100 - total_penalty)

        # Estimate duplication percentage
        if len(result['duplicate_blocks']) > 0:
            result['duplication_percentage'] = min(len(result['duplicate_blocks']) * 2, 50)

        print(f"  ✓ Reusability score: {result['score']}/100")
        print(f"  Found {len(result['duplicate_blocks'])} duplicate code blocks")
        print(f"  Found {len(result['dead_code'])} dead code items")
        print(f"  Found {len(result['extractable_patterns'])} extractable patterns")

        return result

    def _detect_duplicates_with_hashing(self, python_files: List[Path]) -> List[Dict]:
        """Fallback duplication detection using hash comparison"""
        duplicates = []
        block_hashes: Dict[int, List[Dict]] = {}

        def simple_hash(text: str) -> int:
            """Simple DJB2-style hash"""
            h = 5381
            for char in text:
                h = ((h << 5) + h) + ord(char)
            return h & 0xFFFFFFFF

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                relative_path = str(py_file.relative_to(self.project_path))

                # Check blocks of 5+ lines
                block_size = 5
                for i in range(len(lines) - block_size + 1):
                    block = ''.join(lines[i:i + block_size])
                    # Normalize whitespace
                    normalized = ' '.join(block.split())

                    # Skip empty or trivial blocks
                    if len(normalized) < 50:
                        continue

                    block_hash = simple_hash(normalized)

                    if block_hash in block_hashes:
                        # Found potential duplicate
                        for existing in block_hashes[block_hash]:
                            if existing['file'] != relative_path or abs(existing['line'] - (i + 1)) > block_size:
                                duplicates.append({
                                    'file': relative_path,
                                    'line': i + 1,
                                    'similar_to': existing['file'],
                                    'similar_line': existing['line'],
                                    'message': f'Similar code block ({block_size} lines)',
                                    'source': 'hash_detection'
                                })
                                break
                    else:
                        block_hashes[block_hash] = []

                    block_hashes[block_hash].append({
                        'file': relative_path,
                        'line': i + 1
                    })

            except Exception:
                continue

        return duplicates[:50]  # Limit results

    def _detect_dead_code(self, python_files: List[Path]) -> List[Dict]:
        """Detect dead code: unused imports, functions, classes"""
        dead_code = []

        # Collect all definitions and usages
        all_definitions: Dict[str, Dict] = {}
        all_usages: set = set()

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)

                relative_path = str(py_file.relative_to(self.project_path))

                # Collect function and class definitions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Skip private/magic methods
                        if not node.name.startswith('_'):
                            key = f"{relative_path}:{node.name}"
                            all_definitions[key] = {
                                'file': relative_path,
                                'name': node.name,
                                'line': node.lineno,
                                'type': 'function'
                            }

                    elif isinstance(node, ast.ClassDef):
                        if not node.name.startswith('_'):
                            key = f"{relative_path}:{node.name}"
                            all_definitions[key] = {
                                'file': relative_path,
                                'name': node.name,
                                'line': node.lineno,
                                'type': 'class'
                            }

                    elif isinstance(node, ast.Name):
                        all_usages.add(node.id)

                    elif isinstance(node, ast.Attribute):
                        all_usages.add(node.attr)

                    elif isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            all_usages.add(node.func.id)
                        elif isinstance(node.func, ast.Attribute):
                            all_usages.add(node.func.attr)

                # Detect unused imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            name = alias.asname or alias.name.split('.')[0]
                            if name not in all_usages and not name.startswith('_'):
                                dead_code.append({
                                    'file': relative_path,
                                    'line': node.lineno,
                                    'type': 'unused_import',
                                    'name': alias.name,
                                    'message': f'Unused import: {alias.name}',
                                    'severity': 'low'
                                })

                    elif isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            name = alias.asname or alias.name
                            if name not in all_usages and name != '*' and not name.startswith('_'):
                                dead_code.append({
                                    'file': relative_path,
                                    'line': node.lineno,
                                    'type': 'unused_import',
                                    'name': f'{node.module}.{alias.name}' if node.module else alias.name,
                                    'message': f'Unused import: {alias.name}',
                                    'severity': 'low'
                                })

            except Exception:
                continue

        # Check for potentially unused functions/classes (heuristic)
        for key, defn in all_definitions.items():
            if defn['name'] not in all_usages:
                # Skip common entry points and test functions
                if defn['name'] not in ['main', 'setup', 'teardown', 'run']:
                    dead_code.append({
                        'file': defn['file'],
                        'line': defn['line'],
                        'type': f'potentially_unused_{defn["type"]}',
                        'name': defn['name'],
                        'message': f'Potentially unused {defn["type"]}: {defn["name"]}',
                        'severity': 'low'
                    })

        return dead_code[:100]  # Limit results

    def _detect_extractable_patterns(self, python_files: List[Path]) -> List[Dict]:
        """Detect patterns that could be extracted into reusable utilities"""
        import re
        patterns = []

        # Common patterns that could be extracted
        extractable_patterns = [
            (r'try:\s*\n\s+.*\n\s*except\s+\w+.*:\s*\n\s+pass', 'Silent exception handling - consider logging utility'),
            (r'for\s+\w+\s+in\s+range\(len\(\w+\)\):', 'range(len()) pattern - consider enumerate()'),
            (r'if\s+\w+\s+is\s+not\s+None\s+and\s+len\(\w+\)\s*>', 'None and length check - consider utility function'),
            (r'with\s+open\([^)]+\)\s+as\s+\w+:\s*\n\s+\w+\.read\(\)', 'File read pattern - consider read_file utility'),
            (r'datetime\.now\(\)\.strftime', 'DateTime formatting - consider date utility'),
            (r'os\.path\.join\([^)]+\)', 'Path joining - consider pathlib.Path'),
            (r'json\.loads?\([^)]+\)', 'JSON parsing appears multiple times - consider wrapper'),
        ]

        pattern_counts: Dict[str, List[Dict]] = {}

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                relative_path = str(py_file.relative_to(self.project_path))

                for pattern, message in extractable_patterns:
                    matches = list(re.finditer(pattern, content))
                    if matches:
                        if pattern not in pattern_counts:
                            pattern_counts[pattern] = []
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            pattern_counts[pattern].append({
                                'file': relative_path,
                                'line': line_num,
                                'message': message
                            })

            except Exception:
                continue

        # Only report patterns that appear 3+ times
        for pattern, occurrences in pattern_counts.items():
            if len(occurrences) >= 3:
                patterns.append({
                    'pattern': occurrences[0]['message'],
                    'occurrences': len(occurrences),
                    'locations': occurrences[:5],  # First 5 locations
                    'message': f'Pattern appears {len(occurrences)} times - consider extracting to utility'
                })

        return patterns
    
    def _calculate_overall_health(self):
        """Calculate overall health score from dimension scores"""
        scores = []
        weights = {
            'maintainability': 0.35,
            'performance': 0.20,
            'security': 0.25,
            'scalability': 0.10,
            'reusability': 0.10
        }
        
        for dim, weight in weights.items():
            if dim in self.results['dimensions']:
                dim_score = self.results['dimensions'][dim].get('score', 70)
                scores.append(dim_score * weight)
        
        self.results['overall_health'] = round(sum(scores))
    
    def _generate_priority_actions(self):
        """Generate prioritized list of actions"""
        actions = []
        
        for dim, data in self.results['dimensions'].items():
            score = data.get('score', 0)
            
            if score < 60:
                actions.append({
                    'dimension': dim,
                    'priority': 'high',
                    'score': score,
                    'action': f'Address critical {dim} issues immediately'
                })
            elif score < 75:
                actions.append({
                    'dimension': dim,
                    'priority': 'medium',
                    'score': score,
                    'action': f'Improve {dim} in next iteration'
                })
        
        # Sort by score (lowest first)
        actions.sort(key=lambda x: x['score'])
        
        self.results['priority_actions'] = actions[:5]  # Top 5 priorities


def main():
    parser = argparse.ArgumentParser(
        description='Multi-dimensional code analysis for Python projects'
    )
    parser.add_argument('project', help='Path to Python project')
    parser.add_argument(
        '--dimensions',
        default='all',
        help='Comma-separated dimensions: maintainability,performance,security,scalability,reusability (default: all)'
    )
    parser.add_argument(
        '--output',
        default='./multidim-analysis.json',
        help='Output file path'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Analyze all dimensions (same as --dimensions all)'
    )
    
    args = parser.parse_args()
    
    # Parse dimensions
    if args.all or args.dimensions == 'all':
        dimensions = ['maintainability', 'performance', 'security', 'scalability', 'reusability']
    else:
        dimensions = [d.strip() for d in args.dimensions.split(',')]
    
    # Check dependencies
    print("\n🔍 Checking analysis tools...")
    check_dependencies(dimensions)

    # Run analysis
    analyzer = MultiDimensionalAnalyzer(args.project, dimensions)
    results = analyzer.analyze()
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Analysis complete!")
    print(f"📊 Overall Health Score: {results['overall_health']}/100")
    print(f"📄 Full report: {output_path}")
    
    # Print priority actions
    if results['priority_actions']:
        print("\n🎯 Priority Actions:")
        for action in results['priority_actions']:
            print(f"  [{action['priority'].upper()}] {action['action']} (score: {action['score']})")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
