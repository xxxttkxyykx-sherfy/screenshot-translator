#!/bin/bash
# setup.sh — run once after cloning
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo ""
echo "🌸  截屏翻译器 · 安装向导"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── 1. 检查依赖 ───────────────────────────────────────────────────────────────
command -v python3 >/dev/null || { echo "❌  未找到 python3，请先安装 Python 3.10+"; exit 1; }
command -v swiftc  >/dev/null || { echo "❌  未找到 swiftc，请先安装 Xcode Command Line Tools:"; echo "    xcode-select --install"; exit 1; }

# ── 2. Python 虚拟环境 ────────────────────────────────────────────────────────
echo "📦  安装 Python 依赖..."
python3 -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "    ✓ 依赖安装完成"
echo ""

# ── 3. 编译 Swift OCR 工具 ────────────────────────────────────────────────────
echo "🔨  编译 OCR 工具..."
mkdir -p bin

cat > /tmp/_ocr_helper.swift << 'SWIFT'
import Vision
import Foundation

let args = CommandLine.arguments
guard args.count > 1 else { fputs("Usage: ocr_helper <image>\n", stderr); exit(1) }

let url = URL(fileURLWithPath: args[1])
let handler = try VNImageRequestHandler(url: url, options: [:])
let req = VNRecognizeTextRequest()
req.recognitionLanguages = ["zh-Hans", "zh-Hant", "en-US", "ja-JP"]
req.recognitionLevel = .accurate
req.usesLanguageCorrection = true
if #available(macOS 13, *) { req.automaticallyDetectsLanguage = true }
try handler.perform([req])
let lines = (req.results ?? []).compactMap { $0.topCandidates(1).first?.string }
print(lines.joined(separator: "\n"))
SWIFT

swiftc -O /tmp/_ocr_helper.swift -o bin/ocr_helper
echo "    ✓ bin/ocr_helper"

# ── 4. 编译 Swift 菜单栏 App ──────────────────────────────────────────────────
echo "🔨  编译菜单栏工具..."
swiftc -O MenuBar.swift -o bin/menubar
echo "    ✓ bin/menubar"
echo ""

# ── 5. 配置 API Key ───────────────────────────────────────────────────────────
if [ ! -f config.py ]; then
    echo "🔑  配置 DeepSeek API Key"
    echo "    获取地址: https://platform.deepseek.com/api_keys"
    echo ""
    read -rp "    请粘贴你的 API Key (sk-...): " api_key
    echo ""

    echo "📖  生词本保存路径（直接回车使用默认 ~/Documents/生词本.md）"
    echo "    Obsidian 用户示例: /Users/yourname/Obsidian/Notes/生词本.md"
    read -rp "    路径: " vocab_path
    echo ""

    cat > config.py << PYEOF
DEEPSEEK_API_KEY = "${api_key}"
VOCAB_FILE = "${vocab_path}"
PYEOF
    echo "    ✓ config.py 已生成"
else
    echo "    ℹ️  config.py 已存在，跳过配置"
fi
echo ""

# ── 6. 完成提示 ───────────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅  安装完成！"
echo ""
echo "📋  使用前请开启屏幕录制权限:"
echo "    系统设置 → 隐私与安全性 → 屏幕录制 → 开启「终端」"
echo ""
echo "🚀  启动:"
echo "    bash run_worker.sh"
echo ""
