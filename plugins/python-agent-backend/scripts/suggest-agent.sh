#!/bin/bash
# 코드 변경에 따라 적절한 에이전트 추천

[[ -n "$CLAUDE_HOOKS_DISABLED" ]] && exit 0

FILE_PATH=$(jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]] || [[ ! -f "$FILE_PATH" ]]; then
    exit 0
fi

# Python 파일만 처리
if [[ "$FILE_PATH" != *.py ]]; then
    exit 0
fi

SUGGESTIONS=""

# 1. 라우트 파일 → python-route-tester 추천
if echo "$FILE_PATH" | grep -qE '(routes?|endpoints?|api).*\.py$'; then
    SUGGESTIONS="$SUGGESTIONS\n- python-route-tester: 라우트 테스트 권장"
fi

# 2. 보안 관련 코드 감지 → python-security-reviewer 추천
if grep -qE '(password|secret|token|api_key|credential|auth)' "$FILE_PATH" 2>/dev/null; then
    SUGGESTIONS="$SUGGESTIONS\n- python-security-reviewer: 보안 민감 코드 감지"
fi

# 3. 변경량이 큰 경우 → python-diff-reviewer 추천
LINES_CHANGED=$(wc -l < "$FILE_PATH" 2>/dev/null | tr -d ' ')
if [[ "$LINES_CHANGED" -gt 50 ]]; then
    SUGGESTIONS="$SUGGESTIONS\n- python-diff-reviewer: 코드 리뷰 권장 (${LINES_CHANGED}줄)"
fi

# 4. 리팩토링 패턴 감지 → python-refactor-master 추천
if grep -qE '(# TODO|# FIXME|# REFACTOR|deprecated)' "$FILE_PATH" 2>/dev/null; then
    SUGGESTIONS="$SUGGESTIONS\n- python-refactor-master: 리팩토링 대상 감지"
fi

# 5. 테스트 파일 → pytest 스킬 참조 추천
if echo "$FILE_PATH" | grep -qE '(test_|_test\.py|tests/)'; then
    SUGGESTIONS="$SUGGESTIONS\n- pytest-tdd-guide 스킬 참조 권장"
fi

# 추천사항이 있으면 출력
if [[ -n "$SUGGESTIONS" ]]; then
    cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "🤖 에이전트 추천:$SUGGESTIONS"
  }
}
EOF
fi

exit 0
