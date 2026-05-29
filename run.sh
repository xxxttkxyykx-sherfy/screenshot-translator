#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

source "$SCRIPT_DIR/venv/bin/activate" 2>/dev/null || true

if [ ! -f "bin/ocr_helper" ]; then
    echo "❌  OCR 工具未编译，请先运行: bash setup.sh"
    exit 1
fi

exec python3 app.py
