#!/usr/bin/env python3
"""
Multi-Dimensional Code Analysis for Python Projects
Analyzes code across 5 dimensions: Maintainability, Performance, Security, Scalability, Reusability
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import ast
import importlib.util

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
    
    def __init__(self, project_path: str, dimensions: List[str]):
        self.project_path = Path(project_path)
        self.dimensions = dimensions
        self.results = {
            'project': str(project_path),
            'dimensions': {},
            'overall_health': 0,
            'priority_actions': []
        }
    
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
                complexity_data = json.loads(radon_output.stdout)
                
                # Calculate average complexity
                total_complexity = 0
                func_count = 0
                high_complexity = []
                
                for file, functions in complexity_data.items():
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
                    
        except Exception as e:
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
            'score': 70,  # Default neutral score
            'bottlenecks': [],
            'improvements': [],
            'algorithmic_issues': []
        }
        
        # Static analysis for algorithmic complexity
        python_files = list(self.project_path.rglob('*.py'))
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                # Look for nested loops (potential O(n²) or worse)
                nested_loops = self._find_nested_loops(tree, str(py_file))
                result['algorithmic_issues'].extend(nested_loops)
                
            except Exception as e:
                continue
        
        # Score based on algorithmic issues
        if len(result['algorithmic_issues']) == 0:
            result['score'] = 90
        elif len(result['algorithmic_issues']) < 5:
            result['score'] = 70
        else:
            result['score'] = 50
        
        result['improvements'].append({
            'type': 'static_analysis',
            'message': 'Use profiling tools (cProfile, memory_profiler) for runtime analysis',
            'action': 'Install: pip install line-profiler memory-profiler'
        })
        
        print(f"  ✓ Performance score: {result['score']}/100")
        print(f"  Found {len(result['algorithmic_issues'])} potential algorithmic issues")
        
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
    
    def analyze_security(self) -> Dict[str, Any]:
        """Analyze security dimension"""
        print("🔒 Analyzing Security...")
        
        result = {
            'score': 100,  # Start with perfect score
            'vulnerabilities': [],
            'severity': 'none'
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
                bandit_data = json.loads(bandit_output.stdout)
                
                vulnerabilities = bandit_data.get('results', [])
                result['vulnerabilities'] = [
                    {
                        'file': v.get('filename'),
                        'line': v.get('line_number'),
                        'severity': v.get('issue_severity'),
                        'confidence': v.get('issue_confidence'),
                        'message': v.get('issue_text'),
                        'cwe': v.get('issue_cwe', {}).get('id')
                    }
                    for v in vulnerabilities
                ]
                
                # Calculate severity
                high_severity = sum(1 for v in result['vulnerabilities'] if v['severity'] == 'HIGH')
                medium_severity = sum(1 for v in result['vulnerabilities'] if v['severity'] == 'MEDIUM')
                
                if high_severity > 0:
                    result['severity'] = 'high'
                    result['score'] = max(30, 90 - (high_severity * 15))
                elif medium_severity > 0:
                    result['severity'] = 'medium'
                    result['score'] = max(50, 90 - (medium_severity * 5))
                else:
                    result['severity'] = 'low'
                    result['score'] = 85
                
        except FileNotFoundError:
            result['score'] = 0
            result['vulnerabilities'].append({
                'message': 'Bandit not installed - install with: pip install bandit --break-system-packages',
                'severity': 'INFO'
            })
        except Exception as e:
            print(f"  Warning: Bandit analysis failed - {e}")
        
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
                        'message': f'Found {len(safety_data)} vulnerable dependencies'
                    })
                    result['score'] = min(result['score'], 70)
                    
        except FileNotFoundError:
            pass  # Safety not installed, skip
        except Exception as e:
            print(f"  Warning: Safety check failed - {e}")
        
        print(f"  ✓ Security score: {result['score']}/100")
        print(f"  Found {len(result['vulnerabilities'])} security issues")
        
        return result
    
    def analyze_scalability(self) -> Dict[str, Any]:
        """Analyze scalability/extensibility dimension"""
        print("📈 Analyzing Scalability...")
        
        result = {
            'score': 75,  # Default neutral score
            'coupling_issues': [],
            'solid_violations': [],
            'circular_dependencies': []
        }
        
        # Analyze imports and dependencies
        python_files = list(self.project_path.rglob('*.py'))
        
        import_graph = {}
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.append(node.module)
                
                import_graph[str(py_file)] = imports
                
            except Exception:
                continue
        
        # Detect god classes (classes with too many methods)
        god_classes = self._find_god_classes(python_files)
        result['solid_violations'].extend(god_classes)
        
        # Score based on violations
        violation_count = len(result['solid_violations'])
        if violation_count == 0:
            result['score'] = 90
        elif violation_count < 5:
            result['score'] = 75
        elif violation_count < 10:
            result['score'] = 60
        else:
            result['score'] = 40
        
        print(f"  ✓ Scalability score: {result['score']}/100")
        print(f"  Found {violation_count} SOLID violations")
        
        return result
    
    def _find_god_classes(self, python_files: List[Path]) -> List[Dict]:
        """Find classes with too many methods (God Class anti-pattern)"""
        god_classes = []
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Count methods
                        method_count = sum(1 for item in node.body if isinstance(item, ast.FunctionDef))
                        
                        if method_count > 20:  # Threshold for god class
                            god_classes.append({
                                'file': str(py_file),
                                'class': node.name,
                                'line': node.lineno,
                                'method_count': method_count,
                                'violation': 'Single Responsibility Principle',
                                'message': f'Class has {method_count} methods - consider splitting'
                            })
                
            except Exception:
                continue
        
        return god_classes
    
    def analyze_reusability(self) -> Dict[str, Any]:
        """Analyze reusability dimension"""
        print("♻️  Analyzing Reusability...")
        
        result = {
            'score': 80,  # Default good score
            'duplication_percentage': 0,
            'duplicate_blocks': [],
            'extractable_patterns': []
        }
        
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
                            'message': msg.get('message')
                        }
                        for msg in similar_code
                    ]
                    
                    # Estimate duplication percentage
                    if len(result['duplicate_blocks']) > 0:
                        result['duplication_percentage'] = min(len(result['duplicate_blocks']) * 2, 50)
                        result['score'] = max(50, 100 - (len(result['duplicate_blocks']) * 5))
                    
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            print(f"  Warning: Similarity analysis failed - {e}")
        
        print(f"  ✓ Reusability score: {result['score']}/100")
        print(f"  Found {len(result['duplicate_blocks'])} duplicate code blocks")
        
        return result
    
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
        default='/mnt/user-data/outputs/multidim-analysis.json',
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
    available = check_dependencies(dimensions)
    
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
