#!/bin/bash
# Rust 코드 변경에 따라 적절한 에이전트 추천
# Edit/Write 작업 후에 실행

[[ -n "$CLAUDE_HOOKS_DISABLED" ]] && exit 0

# stdin에서 JSON 읽기
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]] || [[ ! -f "$FILE_PATH" ]]; then
    exit 0
fi

# Rust 파일만 처리
if [[ "$FILE_PATH" != *.rs ]]; then
    exit 0
fi

SUGGESTIONS=""

# 1. API/라우트 파일 → rust-route-tester 추천
if echo "$FILE_PATH" | grep -qE '(routes?|handlers?|api|endpoints?).*\.rs$'; then
    SUGGESTIONS="$SUGGESTIONS- rust-route-tester: 라우트 테스트 권장\n"
fi

# 2. unsafe 코드 감지 → rust-diff-reviewer 추천
if grep -q 'unsafe' "$FILE_PATH" 2>/dev/null; then
    SUGGESTIONS="$SUGGESTIONS- rust-diff-reviewer: unsafe 코드 리뷰 필요\n"
fi

# 3. unwrap() 많으면 → 에러 핸들링 개선 권장
UNWRAP_COUNT=$(grep -c 'unwrap()' "$FILE_PATH" 2>/dev/null || echo "0")
if [[ "$UNWRAP_COUNT" -gt 5 ]]; then
    SUGGESTIONS="$SUGGESTIONS- rust-diff-reviewer: unwrap() ${UNWRAP_COUNT}개 - 에러 핸들링 개선 권장\n"
fi

# 4. 테스트 파일 → rust-testing-guide 스킬 참조 추천
if echo "$FILE_PATH" | grep -qE '(test|tests|_test).*\.rs$'; then
    SUGGESTIONS="$SUGGESTIONS- rust-testing-guide 스킬 참조 권장\n"
fi

# 5. mod.rs 또는 lib.rs → rust-workspace-patterns 스킬 참조
if echo "$FILE_PATH" | grep -qE '(mod|lib)\.rs$'; then
    SUGGESTIONS="$SUGGESTIONS- rust-workspace-patterns 스킬 참조 권장\n"
fi

# 6. Axum 관련 코드 → rust-axum-architect 추천
if grep -qE '(axum::|Router|IntoResponse)' "$FILE_PATH" 2>/dev/null; then
    SUGGESTIONS="$SUGGESTIONS- rust-axum-architect: Axum 아키텍처 검토 권장\n"
fi

# 7. 에이전트/LLM 관련 코드 → rust-agent-builder 추천
if grep -qE '(rig::|langchain|llm|agent|Agent)' "$FILE_PATH" 2>/dev/null; then
    SUGGESTIONS="$SUGGESTIONS- rust-agent-builder: AI 에이전트 구현 검토 권장\n"
fi

# 8. DB 관련 코드 → rust-db-patterns 스킬 참조
if grep -qE '(sqlx::|diesel::|sea_orm::|Pool|query)' "$FILE_PATH" 2>/dev/null; then
    SUGGESTIONS="$SUGGESTIONS- rust-db-patterns 스킬 참조 권장\n"
fi

# 추천사항이 있으면 출력
if [[ -n "$SUGGESTIONS" ]]; then
    # JSON 이스케이프
    ESCAPED=$(echo -e "Rust 에이전트/스킬 추천:\n$SUGGESTIONS" | jq -Rs '.')
    cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": $ESCAPED
  }
}
EOF
fi

exit 0
