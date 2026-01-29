#!/bin/bash
# 민감한 파일 보호 - Rust 프로젝트용
# Edit/Write 작업 전에 실행되어 민감한 파일 수정을 차단

[[ -n "$CLAUDE_HOOKS_DISABLED" ]] && exit 0

# stdin에서 JSON 읽기
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# 민감한 파일 패턴
SENSITIVE_PATTERNS=(
    "\.env$"
    "\.env\..*"
    "secrets?\.toml$"
    "credentials?\.toml$"
    "\.pem$"
    "\.key$"
    "private.*\.toml$"
    "config/production\.toml$"
    "\.cargo/credentials$"
)

for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if echo "$FILE_PATH" | grep -qE "$pattern"; then
        cat << EOF
{
  "decision": "block",
  "reason": "민감한 파일 수정 차단: $FILE_PATH\n이 파일은 시크릿이나 인증 정보를 포함할 수 있습니다."
}
EOF
        exit 0
    fi
done

exit 0
