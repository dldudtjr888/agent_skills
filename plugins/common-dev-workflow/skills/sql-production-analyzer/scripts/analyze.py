#!/usr/bin/env python3
"""
SQL Production Analyzer - Unified Orchestrator

Single entry point for all SQL database analysis.
AI-friendly design: one command, one JSON output.

Usage:
    # Static analysis only (no DB connection needed)
    python analyze.py /path/to/project

    # Full analysis with live DB
    python analyze.py /path/to/project --connection "postgresql://user:pass@host/db"
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

# Import analyzers
from find_queries import QueryFinder
from analyze_schema import SchemaAnalyzer
from detect_n_plus_one import NPlusOneDetector


def detect_project_type(project_path: str) -> dict:
    """Detect ORM type and project characteristics."""
    path = Path(project_path)

    detection = {
        "orm_type": "raw_sql",
        "orm_schema_path": None,
        "has_prisma": False,
        "has_typeorm": False,
        "has_sqlalchemy": False,
        "has_django": False,
        "has_raw_sql": False,
        "languages": set()
    }

    # Check for Prisma
    prisma_paths = list(path.rglob("schema.prisma"))
    if prisma_paths:
        detection["has_prisma"] = True
        detection["orm_type"] = "prisma"
        detection["orm_schema_path"] = str(prisma_paths[0])

    # Check for TypeORM (look for decorators)
    for ts_file in path.rglob("*.ts"):
        try:
            content = ts_file.read_text(errors='ignore')
            if "@Entity" in content or "typeorm" in content.lower():
                detection["has_typeorm"] = True
                if detection["orm_type"] == "raw_sql":
                    detection["orm_type"] = "typeorm"
                break
        except:
            pass

    # Check for Python ORMs
    for py_file in path.rglob("*.py"):
        try:
            content = py_file.read_text(errors='ignore')
            if "from sqlalchemy" in content or "import sqlalchemy" in content:
                detection["has_sqlalchemy"] = True
                if detection["orm_type"] == "raw_sql":
                    detection["orm_type"] = "sqlalchemy"
            if "from django.db" in content or "models.Model" in content:
                detection["has_django"] = True
                if detection["orm_type"] == "raw_sql":
                    detection["orm_type"] = "django"
            # Check for raw SQL patterns
            if any(kw in content.lower() for kw in ["aiomysql", "asyncpg", "pymysql", "psycopg", "cursor.execute"]):
                detection["has_raw_sql"] = True
        except:
            pass

    # Detect languages
    if list(path.rglob("*.py")):
        detection["languages"].add("python")
    if list(path.rglob("*.ts")) or list(path.rglob("*.js")):
        detection["languages"].add("javascript")

    detection["languages"] = list(detection["languages"])
    return detection


def run_static_analysis(project_path: str, detection: dict) -> dict:
    """Run all static analyses (no DB connection needed)."""
    results = {
        "queries": {"total": 0, "issues": []},
        "schema": {"tables": [], "issues": []},
        "n_plus_one": {"total": 0, "issues": []}
    }

    # 1. Find queries
    try:
        finder = QueryFinder(project_path)
        queries = finder.scan_project()
        report = finder.generate_report()
        results["queries"] = {
            "total": len(queries),
            "issues": report.get("security_issues", []),
            "queries_found": len(queries)
        }
    except Exception as e:
        results["queries"]["error"] = str(e)

    # 2. Analyze schema (ORM projects only)
    if detection["orm_type"] != "raw_sql":
        try:
            analyzer = SchemaAnalyzer(project_path)
            schema_data = analyzer.analyze()
            report = analyzer.generate_report()
            results["schema"] = {
                "tables": list(schema_data.keys()) if isinstance(schema_data, dict) else [],
                "issues": report.get("issues", [])
            }
        except Exception as e:
            results["schema"]["error"] = str(e)
    else:
        results["schema"]["note"] = "Raw SQL project - schema analysis requires live DB connection"

    # 3. Detect N+1 patterns
    try:
        detector = NPlusOneDetector(project_path)
        n_plus_one = detector.scan_project()
        report = detector.generate_report()
        results["n_plus_one"] = {
            "total": len(n_plus_one),
            "issues": report.get("issues", [])
        }
    except Exception as e:
        results["n_plus_one"]["error"] = str(e)

    return results


def run_live_analysis(project_path: str, connection: str, detection: dict) -> dict:
    """Run live DB analyses (requires connection)."""
    results = {
        "live_schema": {"tables": [], "issues": []},
        "query_performance": {"tested": 0, "slow_queries": []},
        "schema_drift": {"matches": True, "differences": []}
    }

    try:
        from inspect_live_schema import inspect_database
        schema = inspect_database(connection)
        results["live_schema"] = {
            "tables": list(schema.keys()) if isinstance(schema, dict) else [],
            "table_count": len(schema) if isinstance(schema, dict) else 0
        }
    except Exception as e:
        results["live_schema"]["error"] = str(e)

    try:
        from test_query_performance import test_query_performance
        # First extract queries if not already done
        finder = QueryFinder(project_path)
        queries = finder.scan_project()
        if queries:
            perf_results = test_query_performance(connection, queries)
            slow = [q for q in perf_results if q.get("execution_time_ms", 0) > 100]
            results["query_performance"] = {
                "tested": len(perf_results),
                "slow_queries": slow
            }
    except Exception as e:
        results["query_performance"]["error"] = str(e)

    # Schema drift check (ORM projects only)
    if detection["orm_type"] != "raw_sql":
        try:
            from compare_schema_code import compare_schema_code
            drift = compare_schema_code(project_path, connection)
            results["schema_drift"] = drift
        except Exception as e:
            results["schema_drift"]["error"] = str(e)

    return results


def generate_unified_report(
    project_path: str,
    detection: dict,
    static_results: dict,
    live_results: Optional[dict] = None
) -> dict:
    """Generate unified JSON report."""

    # Collect all issues
    all_issues = []

    # Security issues from queries
    for issue in static_results.get("queries", {}).get("issues", []):
        all_issues.append({
            "category": "security",
            "severity": issue.get("severity", "high"),
            "type": issue.get("type", "sql_injection_risk"),
            "file": issue.get("file", ""),
            "line": issue.get("line", 0),
            "message": issue.get("message", "")
        })

    # Schema issues
    for issue in static_results.get("schema", {}).get("issues", []):
        all_issues.append({
            "category": "schema",
            "severity": issue.get("severity", "medium"),
            "type": issue.get("type", "schema_issue"),
            "file": issue.get("file", ""),
            "line": issue.get("line", 0),
            "message": issue.get("message", "")
        })

    # N+1 issues
    for issue in static_results.get("n_plus_one", {}).get("issues", []):
        all_issues.append({
            "category": "performance",
            "severity": "high",
            "type": "n_plus_one",
            "file": issue.get("file", ""),
            "line": issue.get("line", 0),
            "message": issue.get("message", "Potential N+1 query pattern detected")
        })

    # Live analysis issues
    if live_results:
        for query in live_results.get("query_performance", {}).get("slow_queries", []):
            all_issues.append({
                "category": "performance",
                "severity": "medium",
                "type": "slow_query",
                "query": query.get("query", "")[:100],
                "execution_time_ms": query.get("execution_time_ms", 0),
                "message": f"Slow query: {query.get('execution_time_ms', 0)}ms"
            })

        drift = live_results.get("schema_drift", {})
        if not drift.get("matches", True):
            for diff in drift.get("differences", []):
                all_issues.append({
                    "category": "consistency",
                    "severity": "high",
                    "type": "schema_drift",
                    "message": diff
                })

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 4))

    # Build summary
    summary = {
        "total_issues": len(all_issues),
        "by_severity": {
            "critical": len([i for i in all_issues if i.get("severity") == "critical"]),
            "high": len([i for i in all_issues if i.get("severity") == "high"]),
            "medium": len([i for i in all_issues if i.get("severity") == "medium"]),
            "low": len([i for i in all_issues if i.get("severity") == "low"])
        },
        "by_category": {
            "security": len([i for i in all_issues if i.get("category") == "security"]),
            "performance": len([i for i in all_issues if i.get("category") == "performance"]),
            "schema": len([i for i in all_issues if i.get("category") == "schema"]),
            "consistency": len([i for i in all_issues if i.get("category") == "consistency"])
        }
    }

    return {
        "analysis_timestamp": datetime.now().isoformat(),
        "project_path": project_path,
        "project_type": detection,
        "summary": summary,
        "issues": all_issues,
        "static_analysis": static_results,
        "live_analysis": live_results,
        "analysis_notes": _generate_notes(detection, static_results, live_results)
    }


def _generate_notes(detection: dict, static_results: dict, live_results: Optional[dict]) -> list:
    """Generate analysis notes and recommendations."""
    notes = []

    if detection["orm_type"] == "raw_sql":
        notes.append({
            "type": "limitation",
            "message": "Raw SQL project detected. Static analysis has limitations for dynamic queries. Consider query centralization pattern."
        })

    if detection["has_raw_sql"] and detection["orm_type"] != "raw_sql":
        notes.append({
            "type": "warning",
            "message": "Mixed ORM and raw SQL detected. Review raw SQL queries for consistency with ORM schema."
        })

    if not live_results:
        notes.append({
            "type": "recommendation",
            "message": "Run with --connection for live DB analysis (performance testing, schema drift detection)."
        })

    return notes


def main():
    parser = argparse.ArgumentParser(
        description="SQL Production Analyzer - Unified analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Static analysis only
    python analyze.py /path/to/project

    # Full analysis with PostgreSQL
    python analyze.py /path/to/project --connection "postgresql://user:pass@localhost/db"

    # Full analysis with MySQL
    python analyze.py /path/to/project --connection "mysql://user:pass@localhost/db"

    # Output to file
    python analyze.py /path/to/project --output report.json
        """
    )
    parser.add_argument("project_path", help="Path to project root")
    parser.add_argument("--connection", "-c", help="Database connection string (enables live analysis)")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--pretty", "-p", action="store_true", help="Pretty print JSON output")

    args = parser.parse_args()

    # Validate project path
    if not os.path.isdir(args.project_path):
        print(f"Error: {args.project_path} is not a valid directory", file=sys.stderr)
        sys.exit(1)

    # Step 1: Detect project type
    detection = detect_project_type(args.project_path)

    # Step 2: Run static analysis
    static_results = run_static_analysis(args.project_path, detection)

    # Step 3: Run live analysis (if connection provided)
    live_results = None
    if args.connection:
        live_results = run_live_analysis(args.project_path, args.connection, detection)

    # Step 4: Generate unified report
    report = generate_unified_report(args.project_path, detection, static_results, live_results)

    # Output
    indent = 2 if args.pretty else None
    output = json.dumps(report, indent=indent, ensure_ascii=False, default=str)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Report saved to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
