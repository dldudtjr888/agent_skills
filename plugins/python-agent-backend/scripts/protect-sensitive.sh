#!/bin/bash
# 민감한 파일 수정 차단

[[ -n "$CLAUDE_HOOKS_DISABLED" ]] && exit 0

FILE_PATH=$(jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# 민감한 파일 패턴
if echo "$FILE_PATH" | grep -qE '(\.env|credentials|secrets|\.pem|\.key|password)'; then
    echo "Blocked: Cannot modify sensitive file: $FILE_PATH" >&2
    exit 2
fi

exit 0
