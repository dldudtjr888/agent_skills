#!/usr/bin/env python3
"""
Python Code Analysis Script for Refactoring

Performs comprehensive static analysis on Python projects to identify
refactoring opportunities, code smells, and technical debt.

Dependencies:
    pip install pylint radon rope --break-system-packages
"""

import argparse
import ast
import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any
import re


@dataclass
class AnalysisIssue:
    """Represents a single refactoring issue found during analysis"""
    severity: str  # critical, high, medium, low
    category: str  # complexity, smell, maintainability, architecture, performance
    title: str
    description: str
    file: str
    line: int
    end_line: int
    suggested_refactoring: str
    automated: bool
    risk: str  # high, medium, low
    impact: str  # high, medium, low
    metrics: Dict[str, Any]


class PythonAnalyzer:
    """Main analyzer for Python projects"""
    
    def __init__(self, project_path: str, config: Dict[str, Any]):
        self.project_path = Path(project_path).absolute()
        self.config = config
        self.issues: List[AnalysisIssue] = []
        self.metrics = {
            "total_files": 0,
            "total_lines": 0,
            "avg_complexity": 0,
            "avg_maintainability": 0,
            "duplicate_lines": 0
        }
    
    def analyze(self) -> Dict[str, Any]:
        """Run comprehensive analysis"""
        print(f"🔍 Analyzing Python project: {self.project_path}")
        
        python_files = self._find_python_files()
        self.metrics["total_files"] = len(python_files)
        
        print(f"📁 Found {len(python_files)} Python files")
        
        # Phase 1: Complexity Analysis
        print("\n🧮 Analyzing complexity...")
        complexity_issues = self._analyze_complexity(python_files)
        self.issues.extend(complexity_issues)
        
        # Phase 2: Code Smells Detection
        print("👃 Detecting code smells...")
        smell_issues = self._detect_code_smells(python_files)
        self.issues.extend(smell_issues)
        
        # Phase 3: AST-based Analysis
        print("🌳 Performing AST analysis...")
        ast_issues = self._analyze_ast(python_files)
        self.issues.extend(ast_issues)
        
        # Phase 4: Maintainability Index
        print("📊 Calculating maintainability...")
        maint_issues = self._analyze_maintainability(python_files)
        self.issues.extend(maint_issues)
        
        # Generate report
        return self._generate_report()
    
    def _find_python_files(self) -> List[Path]:
        """Find all Python files in the project"""
        python_files = []
        exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', 'node_modules', 'build', 'dist'}
        
        for root, dirs, files in os.walk(self.project_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        return python_files
    
    def _analyze_complexity(self, files: List[Path]) -> List[AnalysisIssue]:
        """Analyze cyclomatic complexity using Radon"""
        issues = []
        
        for file in files:
            try:
                # Run radon cc for cyclomatic complexity
                result = subprocess.run(
                    ['radon', 'cc', str(file), '-s', '-j'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    continue
                
                data = json.loads(result.stdout)
                
                for item in data.get(str(file), []):
                    complexity = item.get('complexity', 0)
                    
                    if complexity > self.config.get('max_complexity', 10):
                        severity = 'critical' if complexity > 20 else 'high' if complexity > 15 else 'medium'
                        
                        issues.append(AnalysisIssue(
                            severity=severity,
                            category='complexity',
                            title=f"High cyclomatic complexity: {complexity}",
                            description=f"Function '{item['name']}' has complexity {complexity}, threshold is {self.config.get('max_complexity', 10)}",
                            file=str(file.relative_to(self.project_path)),
                            line=item['lineno'],
                            end_line=item['endline'],
                            suggested_refactoring='extract_method',
                            automated=True,
                            risk='low',
                            impact='high',
                            metrics={'complexity': complexity, 'type': item['type']}
                        ))
            
            except Exception as e:
                print(f"⚠️  Error analyzing {file}: {e}")
        
        return issues
    
    def _detect_code_smells(self, files: List[Path]) -> List[AnalysisIssue]:
        """Detect code smells through AST analysis"""
        issues = []
        
        for file in files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    source = f.read()
                    tree = ast.parse(source, filename=str(file))
                
                # Detect long methods
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_length = node.end_lineno - node.lineno + 1
                        
                        if func_length > self.config.get('max_method_length', 50):
                            issues.append(AnalysisIssue(
                                severity='medium',
                                category='smell',
                                title=f"Long method: {func_length} lines",
                                description=f"Method '{node.name}' is {func_length} lines, should be < {self.config.get('max_method_length', 50)}",
                                file=str(file.relative_to(self.project_path)),
                                line=node.lineno,
                                end_line=node.end_lineno,
                                suggested_refactoring='extract_method',
                                automated=True,
                                risk='low',
                                impact='medium',
                                metrics={'length': func_length}
                            ))
                        
                        # Detect too many parameters
                        param_count = len(node.args.args)
                        if param_count > 5:
                            issues.append(AnalysisIssue(
                                severity='low',
                                category='smell',
                                title=f"Too many parameters: {param_count}",
                                description=f"Method '{node.name}' has {param_count} parameters, should be < 5",
                                file=str(file.relative_to(self.project_path)),
                                line=node.lineno,
                                end_line=node.end_lineno,
                                suggested_refactoring='introduce_parameter_object',
                                automated=False,
                                risk='medium',
                                impact='low',
                                metrics={'param_count': param_count}
                            ))
                    
                    # Detect large classes
                    if isinstance(node, ast.ClassDef):
                        class_length = node.end_lineno - node.lineno + 1
                        
                        if class_length > self.config.get('max_class_length', 300):
                            issues.append(AnalysisIssue(
                                severity='high',
                                category='smell',
                                title=f"Large class: {class_length} lines",
                                description=f"Class '{node.name}' is {class_length} lines, should be < {self.config.get('max_class_length', 300)}",
                                file=str(file.relative_to(self.project_path)),
                                line=node.lineno,
                                end_line=node.end_lineno,
                                suggested_refactoring='extract_class',
                                automated=False,
                                risk='medium',
                                impact='high',
                                metrics={'length': class_length}
                            ))
            
            except Exception as e:
                print(f"⚠️  Error detecting smells in {file}: {e}")
        
        return issues
    
    def _analyze_ast(self, files: List[Path]) -> List[AnalysisIssue]:
        """Perform deeper AST-based analysis"""
        issues = []
        
        for file in files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    source = f.read()
                    tree = ast.parse(source, filename=str(file))
                
                # Detect nested conditionals
                for node in ast.walk(tree):
                    if isinstance(node, (ast.If, ast.For, ast.While)):
                        depth = self._get_nesting_depth(node)
                        
                        if depth > 3:
                            issues.append(AnalysisIssue(
                                severity='medium',
                                category='complexity',
                                title=f"Deep nesting: {depth} levels",
                                description=f"Conditional nesting depth is {depth}, should be < 3",
                                file=str(file.relative_to(self.project_path)),
                                line=node.lineno,
                                end_line=node.end_lineno,
                                suggested_refactoring='decompose_conditional',
                                automated=True,
                                risk='low',
                                impact='medium',
                                metrics={'nesting_depth': depth}
                            ))
            
            except Exception as e:
                print(f"⚠️  Error in AST analysis of {file}: {e}")
        
        return issues
    
    def _get_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Calculate nesting depth for control flow structures"""
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While)):
                child_depth = self._get_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def _analyze_maintainability(self, files: List[Path]) -> List[AnalysisIssue]:
        """Analyze maintainability index using Radon"""
        issues = []
        
        for file in files:
            try:
                result = subprocess.run(
                    ['radon', 'mi', str(file), '-s', '-j'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    continue
                
                data = json.loads(result.stdout)
                
                for item in data.get(str(file), []):
                    mi_score = item.get('mi', 100)
                    
                    if mi_score < self.config.get('min_maintainability_index', 65):
                        severity = 'critical' if mi_score < 20 else 'high' if mi_score < 40 else 'medium'
                        
                        issues.append(AnalysisIssue(
                            severity=severity,
                            category='maintainability',
                            title=f"Low maintainability: {mi_score:.1f}",
                            description=f"File has maintainability index {mi_score:.1f}, threshold is {self.config.get('min_maintainability_index', 65)}",
                            file=str(file.relative_to(self.project_path)),
                            line=1,
                            end_line=1,
                            suggested_refactoring='comprehensive_refactoring',
                            automated=False,
                            risk='high',
                            impact='high',
                            metrics={'maintainability_index': mi_score, 'rank': item.get('rank', 'C')}
                        ))
            
            except Exception as e:
                print(f"⚠️  Error analyzing maintainability of {file}: {e}")
        
        return issues
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate final analysis report"""
        # Sort issues by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        self.issues.sort(key=lambda x: (priority_order[x.severity], x.file, x.line))
        
        # Calculate summary statistics
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        category_counts = {}
        automated_count = 0
        
        for issue in self.issues:
            severity_counts[issue.severity] += 1
            category_counts[issue.category] = category_counts.get(issue.category, 0) + 1
            if issue.automated:
                automated_count += 1
        
        report = {
            "project_path": str(self.project_path),
            "analysis_version": "1.0.0",
            "summary": {
                "total_issues": len(self.issues),
                "by_severity": severity_counts,
                "by_category": category_counts,
                "automated_count": automated_count,
                "manual_count": len(self.issues) - automated_count
            },
            "metrics": self.metrics,
            "issues": [asdict(issue) for issue in self.issues],
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate high-level recommendations"""
        recommendations = []
        
        critical_count = sum(1 for i in self.issues if i.severity == 'critical')
        if critical_count > 0:
            recommendations.append(f"Address {critical_count} critical issues immediately - these represent major technical debt")
        
        complexity_issues = [i for i in self.issues if i.category == 'complexity']
        if len(complexity_issues) > 10:
            recommendations.append(f"Focus on complexity reduction - {len(complexity_issues)} functions need simplification")
        
        automated_issues = [i for i in self.issues if i.automated]
        if len(automated_issues) > 0:
            recommendations.append(f"Run automated refactoring on {len(automated_issues)} issues that can be safely automated")
        
        return recommendations


def main():
    parser = argparse.ArgumentParser(description='Analyze Python project for refactoring opportunities')
    parser.add_argument('project_path', help='Path to the Python project')
    parser.add_argument('--output', '-o', default='./refactoring-analysis.json',
                       help='Output file for analysis report')
    parser.add_argument('--max-complexity', type=int, default=10,
                       help='Maximum allowed cyclomatic complexity')
    parser.add_argument('--max-method-length', type=int, default=50,
                       help='Maximum allowed method length in lines')
    parser.add_argument('--max-class-length', type=int, default=300,
                       help='Maximum allowed class length in lines')
    parser.add_argument('--min-maintainability', type=int, default=65,
                       help='Minimum maintainability index')
    
    args = parser.parse_args()
    
    config = {
        'max_complexity': args.max_complexity,
        'max_method_length': args.max_method_length,
        'max_class_length': args.max_class_length,
        'min_maintainability_index': args.min_maintainability
    }
    
    analyzer = PythonAnalyzer(args.project_path, config)
    report = analyzer.analyze()
    
    # Write report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Analysis complete!")
    print(f"📊 Found {report['summary']['total_issues']} issues")
    print(f"   - Critical: {report['summary']['by_severity']['critical']}")
    print(f"   - High: {report['summary']['by_severity']['high']}")
    print(f"   - Medium: {report['summary']['by_severity']['medium']}")
    print(f"   - Low: {report['summary']['by_severity']['low']}")
    print(f"\n🤖 {report['summary']['automated_count']} issues can be automatically refactored")
    print(f"📝 Report saved to: {output_path}")
    
    if report['recommendations']:
        print("\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"   - {rec}")


if __name__ == "__main__":
    main()
