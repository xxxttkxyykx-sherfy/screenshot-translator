<h1 align="center">🌸 截屏翻译 · 词汇知识库</h1>

<p align="center">
  框选屏幕任意区域 → 即时翻译 → 一键将生词存入个人知识库<br/>
  例句全部达到雅思写作水准，让每一个词都值得被记住
</p>

<p align="center">
  <img src="https://img.shields.io/badge/macOS-13%2B-pink?style=flat-square"/>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square"/>
  <img src="https://img.shields.io/badge/powered_by-DeepSeek-purple?style=flat-square"/>
</p>

---

## 为什么做这个工具？

读论文、刷英文资料时，遇到不认识的词，查完就忘——这是很多人的痛点。

这个工具的核心逻辑是：**翻译是入口，积累才是目的。** 截屏翻译之后，你可以一键把这个词连同雅思级别的例句一起存进本地 Markdown 文件。如果你用 Obsidian，直接写入你的 vault，久而久之形成一个真正属于你的词汇知识库。

---

## ✨ 核心功能

| | |
|---|---|
| 🖱️ **拖拽截屏翻译** | 点菜单栏「译」，框选任意屏幕区域，自动 OCR + AI 翻译，1-2 秒出结果 |
| 🃏 **悬浮卡片显示** | 半透明粉色卡片，原文 + 译文并排，点外部即关闭，不打断阅读节奏 |
| 📚 **一键存入知识库** | 点「记词」输入单词，AI 自动生成词性、释义与雅思级例句，追加到本地 Markdown |
| 🧠 **雅思水准例句** | 例句语法复杂、逻辑严密，贴近真实学术写作表达，背了真的能用 |
| 🗂️ **Obsidian 原生兼容** | 生词本直接写入你的 Obsidian vault，与你现有笔记系统无缝融合 |
| 📋 **一键复制译文** | 点「复制」直接写入剪贴板，无需手动选中 |
| 🔁 **开机自启** | 注册 LaunchAgent，登录后自动出现在菜单栏，零感知常驻 |

---

## 生词本长什么样？

每次「记词」后自动追加，格式整洁，可直接在 Obsidian 中浏览：

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

例句在句式结构和词汇密度上对标雅思 7+ 写作水准，积累到一定数量后可以直接作为写作素材库使用。

---

## 📋 环境要求

- macOS 13 Ventura 及以上
- Python 3.10+
- Xcode Command Line Tools（用于编译 Swift 组件）

---

## 🚀 安装

```bash
# 1. 克隆项目
git clone https://github.com/xxxttkxyykx-sherfy/screenshot-translator.git
cd screenshot-translator

# 2. 运行安装向导（自动编译 + 引导配置 API Key）
bash setup.sh
```

安装向导会自动完成：
- 创建 Python 虚拟环境，安装依赖
- 编译 OCR 和菜单栏两个 Swift 二进制
- 引导输入 DeepSeek API Key 并生成 `config.py`
- 提示开启屏幕录制权限

> **获取 DeepSeek API Key**：注册 [platform.deepseek.com](https://platform.deepseek.com/api_keys)，费用极低（约 ¥0.001 / 次）

---

## ⚙️ 配置生词本路径

安装后编辑 `config.py`，把生词本指向你的 Obsidian vault：

```python
DEEPSEEK_API_KEY = "sk-your-key-here"

# 默认保存到 ~/Documents/生词本.md
# Obsidian 用户建议改成 vault 内路径，例如：
# VOCAB_FILE = "/Users/yourname/Obsidian/Notes/生词本.md"
VOCAB_FILE = ""
```

---

## 🖥️ 使用方式

**启动（每次开机后在终端运行一次）：**
```bash
bash run_worker.sh
```

**日常使用流程：**
1. 点击菜单栏「译」
2. 拖拽框选要翻译的屏幕区域
3. 等待 1-2 秒，翻译卡片弹出
4. 点「记词」→ 输入单词 → AI 生成例句并存入知识库

**首次使用需开启权限：**
> 系统设置 → 隐私与安全性 → **屏幕录制** → 开启「终端」✅

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
DeepSeek API 翻译 / 查词 + 例句生成
    ↓
TranslationOverlay（粉色悬浮卡片 UI）
    ↓（可选）
本地 Markdown 生词本 / Obsidian Vault
```

---

## 🤝 Contributing

欢迎 PR 和 Issue！特别欢迎：
- Windows / Linux 支持（需替换 OCR 方案）
- 快捷键触发（替代菜单栏点击）
- 更多翻译引擎支持（OpenAI / Claude）

---

## 📄 License

MIT
