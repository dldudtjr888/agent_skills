#!/bin/bash
# Rust 파일 자동 린팅: cargo fmt, cargo clippy
# Edit/Write 작업 후에 실행

[[ -n "$CLAUDE_HOOKS_DISABLED" ]] && exit 0

# stdin에서 JSON 읽기
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Rust 파일만 처리
if [[ "$FILE_PATH" != *.rs ]]; then
    exit 0
fi

# 파일 존재 확인
if [[ ! -f "$FILE_PATH" ]]; then
    exit 0
fi

# Cargo.toml 위치 찾기 (프로젝트 루트)
CARGO_DIR=$(dirname "$FILE_PATH")
while [[ "$CARGO_DIR" != "/" ]]; do
    if [[ -f "$CARGO_DIR/Cargo.toml" ]]; then
        break
    fi
    CARGO_DIR=$(dirname "$CARGO_DIR")
done

if [[ ! -f "$CARGO_DIR/Cargo.toml" ]]; then
    exit 0
fi

cd "$CARGO_DIR" || exit 0

MESSAGES=""

# cargo fmt 실행 (자동 포맷팅)
if command -v cargo &> /dev/null; then
    FMT_OUTPUT=$(cargo fmt 2>&1)
    if [[ $? -eq 0 ]]; then
        # 포맷팅 변경이 있었는지 확인
        if [[ -n "$FMT_OUTPUT" ]]; then
            MESSAGES="$MESSAGES[fmt] 코드가 포맷팅되었습니다.\n"
        fi
    fi
fi

# cargo clippy 실행 (린트 검사)
if command -v cargo &> /dev/null; then
    CLIPPY_OUTPUT=$(cargo clippy --message-format=short 2>&1 | grep -E "^(warning|error)" | head -5)
    if [[ -n "$CLIPPY_OUTPUT" ]]; then
        MESSAGES="$MESSAGES[clippy]\n$CLIPPY_OUTPUT\n"
    fi
fi

# 메시지가 있으면 출력
if [[ -n "$MESSAGES" ]]; then
    # JSON 이스케이프
    ESCAPED_MESSAGES=$(echo -e "$MESSAGES" | jq -Rs '.')
    cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": $ESCAPED_MESSAGES
  }
}
EOF
fi

exit 0
