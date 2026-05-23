<h1 align="center">🌸 截屏翻译器</h1>

<p align="center">
  拖拽选区 → OCR → AI 翻译 → 粉色卡片弹出<br/>
  常驻 Mac 菜单栏，不打断工作流
</p>

<p align="center">
  <img src="https://img.shields.io/badge/macOS-13%2B-pink?style=flat-square"/>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square"/>
  <img src="https://img.shields.io/badge/powered_by-DeepSeek-purple?style=flat-square"/>
</p>

---

## ✨ 功能

| | |
|---|---|
| 🖱️ **拖拽截图翻译** | 点菜单栏「译」，框选任意屏幕区域，自动 OCR + 翻译 |
| 🃏 **粉色悬浮卡片** | 半透明卡片显示原文与译文，点外部关闭 |
| 🔄 **一键继续翻译** | 点卡片内按钮，立即进入下一次选区 |
| 📋 **一键复制译文** | 点「复制」直接写入剪贴板 |
| 📚 **记录生词** | 点「记词」输入单词，自动查询雅思风格例句并保存到 Markdown 文件 |
| 🔁 **开机自启** | 注册 LaunchAgent，每次登录自动出现在菜单栏 |

---

## 📋 环境要求

- macOS 13 Ventura 及以上
- Python 3.10+
- Xcode Command Line Tools（用于编译 Swift 组件）

---

## 🚀 安装

```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/screenshot-translator.git
cd screenshot-translator

# 2. 运行安装向导（自动编译 + 引导配置 API Key）
bash setup.sh
```

安装向导会：
- 创建 Python 虚拟环境，安装依赖
- 编译 OCR 和菜单栏两个 Swift 二进制
- 引导你输入 DeepSeek API Key 并生成 `config.py`
- 提示开启屏幕录制权限

> **获取 DeepSeek API Key**：注册 [platform.deepseek.com](https://platform.deepseek.com/api_keys)，费用极低（约 ¥0.001/次翻译）

---

## ⚙️ 配置

安装后 `config.py` 自动生成，也可以手动编辑：

```python
# config.py
DEEPSEEK_API_KEY = "sk-your-key-here"

# 生词本保存路径（留空则默认 ~/Documents/生词本.md）
# Obsidian 用户可填入自己的 vault 路径：
# VOCAB_FILE = "/Users/yourname/Obsidian/Notes/生词本.md"
VOCAB_FILE = ""
```

---

## 🖥️ 使用

**启动（每次开机后在终端运行一次）：**
```bash
bash run_worker.sh
```

**使用流程：**
1. 点击菜单栏「译」
2. 拖拽选择要翻译的屏幕区域
3. 等待 1-2 秒，翻译卡片弹出
4. 点「继续翻译」进行下一次 / 点「复制」复制译文 / 点「记词」保存生词 / 点卡片外关闭

**首次使用需开启权限：**
> 系统设置 → 隐私与安全性 → **屏幕录制** → 开启「终端」✅

---

## 📖 生词本格式

每次「记词」后自动追加到 Markdown 文件，格式如下：

```markdown
### serendipity
词性：n.
释义：意外发现美好事物的能力；机缘巧合
例句：The discovery of penicillin, widely regarded as one of the most
significant breakthroughs in medical history, was itself a product of
serendipity rather than systematic investigation.
例句翻译：青霉素的发现被普遍视为医学史上最重要的突破之一，其本身是机缘
巧合的产物，而非系统研究的结果。
📅 2026-05-23
```

---

## 🏗️ 技术架构

```
Swift 菜单栏 App
    ↓ 写入 /tmp/translate_trigger
Python Worker（PyQt6 事件循环，常驻后台）
    ↓
RegionSelector（全屏透明选区 UI）
    ↓
mss 截图 → Swift OCR（macOS Vision 框架）
    ↓
DeepSeek API 翻译 / 查词
    ↓
TranslationOverlay（粉色悬浮卡片 UI）
    ↓（可选）
本地 Markdown 生词本
```

---

## 🤝 贡献 / Contributing

欢迎 PR 和 Issue！特别欢迎：
- Windows / Linux 支持（需替换 OCR 方案）
- 快捷键触发（替代菜单栏点击）
- 更多翻译引擎支持

---

## 📄 License

MIT
