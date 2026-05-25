#!/bin/bash
# Test Docs Platform - Launcher Script
# 用法: ./run.sh --help
#       ./run.sh --interactive "https://example.com" --session-name "My Test"
#       ./run.sh --list

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

# 確保數據庫已初始化
"$VENV_PYTHON" "$SCRIPT_DIR/main.py" --init-db 2>/dev/null

# 執行主程序，傳遞所有參數
exec "$VENV_PYTHON" "$SCRIPT_DIR/main.py" "$@"