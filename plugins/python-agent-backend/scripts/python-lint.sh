#!/bin/bash
# Python 파일 자동 린팅: ruff format, ruff check, ty, bandit

[[ -n "$CLAUDE_HOOKS_DISABLED" ]] && exit 0

FILE_PATH=$(jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Python 파일만 처리
if [[ "$FILE_PATH" != *.py ]]; then
    exit 0
fi

# 파일 존재 확인
if [[ ! -f "$FILE_PATH" ]]; then
    exit 0
fi

# ruff format (자동 포맷팅)
if command -v ruff &> /dev/null; then
    ruff format "$FILE_PATH" 2>/dev/null
    ruff check --fix "$FILE_PATH" 2>/dev/null
fi

# ty check (타입 체크) - 에러만 표시
if command -v ty &> /dev/null; then
    ERRORS=$(ty check "$FILE_PATH" 2>&1 | head -5)
    if [[ -n "$ERRORS" ]]; then
        echo "[ty] $ERRORS"
    fi
fi

# bandit (보안 검사) - 경고만 표시
if command -v bandit &> /dev/null; then
    WARNINGS=$(bandit -q "$FILE_PATH" 2>/dev/null | head -5)
    if [[ -n "$WARNINGS" ]]; then
        echo "[bandit] $WARNINGS"
    fi
fi

exit 0
