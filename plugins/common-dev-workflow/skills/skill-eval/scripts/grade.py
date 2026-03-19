#!/usr/bin/env python3
"""
Skill eval grading script.
eval-config.json의 assertions를 읽고 각 출력 파일을 채점하여 grading.json 생성.

사용법:
    python grade.py <iteration-dir>

예시:
    python grade.py axum-backend-pattern-workspace/iteration-1
"""

import json
import re
import sys
from pathlib import Path


def check_pattern(content: str, pattern: str) -> bool:
    """패턴이 content에 존재하는지 검사. regex 실패 시 literal fallback."""
    # JSON에서 읽으면 \| → | 로 디코딩됨. 둘 다 처리.
    parts = pattern.split("\\|") if "\\|" in pattern else pattern.split("|")
    for p in parts:
        p = p.strip()
        try:
            if re.search(p, content, re.IGNORECASE):
                return True
        except re.error:
            if p.lower() in content.lower():
                return True
    return False


def strip_comments(content: str) -> str:
    """코멘트 라인을 제거한 content를 반환. grep_negative가 코멘트의 anti-pattern 언급을 잡는 false positive를 방지.

    Core Rules를 SKILL.md에 추가하면 에이전트가 규칙을 주석으로 복사함:
      // .unwrap() 금지 — ? + .context() 사용
      // Server::bind 대신 axum::serve 사용
    이 주석이 grep_negative에 잡혀 false positive 발생.
    """
    lines = content.split("\n")
    filtered = []
    in_block_comment = False
    for line in lines:
        stripped = line.strip()
        # Block comment tracking
        if not in_block_comment and "/*" in stripped:
            in_block_comment = True
        if in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
            continue
        # Skip single-line comments (// , /// , //! )
        if stripped.startswith("//"):
            continue
        # Skip markdown-style lines in code (e.g., "3. Avoid .unwrap()")
        # These appear when agents write skill rules as doc headers
        if re.match(r'^\d+\.\s+', stripped):
            continue
        filtered.append(line)
    return "\n".join(filtered)


def strip_test_blocks(content: str, exclude_patterns: list = None) -> str:
    """테스트 블록을 제거한 content를 반환. exclude_patterns에 매칭되는 라인 이후 블록을 제거."""
    if not exclude_patterns:
        return content
    lines = content.split("\n")
    filtered = []
    skip_depth = 0
    in_excluded = False
    for line in lines:
        # Check if this line matches an exclude pattern
        if not in_excluded:
            for pat in exclude_patterns:
                try:
                    if re.search(pat, line):
                        in_excluded = True
                        skip_depth = 0
                        break
                except re.error:
                    if pat in line:
                        in_excluded = True
                        skip_depth = 0
                        break
        if in_excluded:
            skip_depth += line.count("{") - line.count("}")
            if skip_depth <= 0 and "}" in line:
                in_excluded = False
            continue
        filtered.append(line)
    return "\n".join(filtered)


def grade_output(content: str, assertions: list, eval_id: str = None, exclude_patterns: list = None) -> dict:
    """단일 출력 파일을 assertions로 채점. eval_id가 있으면 해당 eval에 매핑된 assertion만 사용."""
    # 1. 코멘트 라인 제거 (Core Rules 주석 false positive 방지)
    grading_content = strip_comments(content)
    # 2. exclude_patterns가 있으면 테스트 블록 제거
    grading_content = strip_test_blocks(grading_content, exclude_patterns) if exclude_patterns else grading_content

    passed = 0
    failed = 0
    total_weight = 0
    passed_weight = 0
    failures = []

    for assertion in assertions:
        # eval별 assertion 매핑: evals 필드가 있으면 해당 eval만 적용
        applicable_evals = assertion.get("evals")
        if applicable_evals and eval_id and eval_id not in applicable_evals:
            continue

        check_type = assertion.get("check_type", "grep")
        pattern = assertion.get("pattern", "")
        text = assertion.get("text", "")
        weight = assertion.get("weight", 1)
        total_weight += weight

        if check_type == "grep_negative":
            hit = check_pattern(grading_content, pattern)
            ok = not hit
        elif check_type == "grep":
            ok = check_pattern(grading_content, pattern)
        elif check_type == "manual":
            ok = True
        else:
            ok = True

        if ok:
            passed += 1
            passed_weight += weight
        else:
            failed += 1
            failures.append(f"❌ {text} (w={weight})")

    weighted_rate = round(passed_weight / total_weight * 100, 1) if total_weight > 0 else 0

    return {
        "passed": passed,
        "failed": failed,
        "total": passed + failed,
        "weighted_rate": weighted_rate,
        "failures": failures,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python grade.py <iteration-dir>")
        print("  iteration-dir should contain e1/, e2/, e3/ with with_skill/ and baseline/ subdirs")
        print("  eval-config.json should be in the parent (workspace) directory")
        sys.exit(1)

    iter_dir = Path(sys.argv[1]).resolve()
    workspace_dir = iter_dir.parent

    # Load eval config
    config_file = workspace_dir / "eval-config.json"
    if not config_file.exists():
        print(f"ERROR: eval-config.json not found at {config_file}")
        sys.exit(1)

    config = json.loads(config_file.read_text())
    assertions = config.get("assertions", [])
    evals_list = config.get("evals", [])
    exclude_patterns = config.get("exclude_patterns", [])

    if not assertions:
        print("ERROR: No assertions found in eval-config.json")
        sys.exit(1)

    results = {"evals": {}, "summary": {}}

    total_w_weight = 0
    total_b_weight = 0
    eval_count = 0

    for eval_item in evals_list:
        eval_id = eval_item["id"]
        eval_result = {}

        for variant in ["with_skill", "baseline"]:
            out_dir = iter_dir / eval_id / variant / "outputs"
            output_files = list(out_dir.glob("output.*")) if out_dir.exists() else []

            if not output_files:
                eval_result[variant] = {
                    "passed": 0, "failed": len(assertions), "total": len(assertions),
                    "weighted_rate": 0, "failures": ["NO OUTPUT FILE"]
                }
                continue

            content = output_files[0].read_text()
            grade = grade_output(content, assertions, eval_id, exclude_patterns)
            eval_result[variant] = grade

        results["evals"][eval_id] = eval_result

        # Accumulate for summary
        w = eval_result.get("with_skill", {})
        b = eval_result.get("baseline", {})
        total_w_weight += w.get("weighted_rate", 0)
        total_b_weight += b.get("weighted_rate", 0)
        eval_count += 1

    # Summary
    w_avg = round(total_w_weight / eval_count, 1) if eval_count > 0 else 0
    b_avg = round(total_b_weight / eval_count, 1) if eval_count > 0 else 0

    results["summary"] = {
        "with_skill": {"weighted_rate": w_avg},
        "baseline": {"weighted_rate": b_avg},
        "delta": round(w_avg - b_avg, 1),
    }

    # Save
    grading_file = iter_dir / "grading.json"
    grading_file.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    # Print
    print(f"{'Eval':<6} {'With':>8} {'Base':>8} {'Delta':>8}  {'Fails (with)':>20} {'Fails (base)':>20}")
    print("-" * 75)
    for eval_id, data in results["evals"].items():
        w = data.get("with_skill", {})
        b = data.get("baseline", {})
        wr = w.get("weighted_rate", 0)
        br = b.get("weighted_rate", 0)
        d = round(wr - br, 1)
        sign = "+" if d > 0 else ""
        wf = str(w.get("failed", 0)) + "건" if w.get("failed", 0) else "-"
        bf = str(b.get("failed", 0)) + "건" if b.get("failed", 0) else "-"
        print(f"{eval_id:<6} {wr:>7.0f}% {br:>7.0f}% {sign}{d:>6.1f}%  {wf:>20} {bf:>20}")

    s = results["summary"]
    print("-" * 75)
    d = s["delta"]
    sign = "+" if d > 0 else ""
    print(f"{'합계':<6} {s['with_skill']['weighted_rate']:>7.0f}% {s['baseline']['weighted_rate']:>7.0f}% {sign}{d:>6.1f}%")
    print(f"\nSaved to {grading_file}")


if __name__ == "__main__":
    main()
