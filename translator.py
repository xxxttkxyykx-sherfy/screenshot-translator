import requests

_URL = "https://api.deepseek.com/chat/completions"
_SYSTEM = (
    "你是专业翻译。将用户提供的英文文本翻译成简体中文，"
    "保持原文的段落结构，只输出翻译结果，不加任何解释。"
)
_VOCAB_SYSTEM = (
    "你是英语词典助手。用户给你一个英语单词或短语，"
    "你用中文给出简洁的词典释义，严格按照指定格式输出，不加其他内容。"
)


def translate(text: str, api_key: str) -> str:
    resp = requests.post(
        _URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": text},
            ],
            "temperature": 0.2,
            "max_tokens": 2000,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def lookup_word(word: str, api_key: str) -> str:
    """Return a formatted dictionary entry for *word* (in Chinese)."""
    prompt = (
        f"请为「{word}」提供释义，严格按照以下格式：\n"
        "词性：（n./v./adj./adv. 等）\n"
        "释义：（1-3个核心中文意思）\n"
        "例句：（一个雅思阅读/写作风格的复杂长句，体现学术语境，禁止使用简单句）\n"
        "例句翻译：（例句的中文翻译）"
    )
    resp = requests.post(
        _URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": _VOCAB_SYSTEM},
                {"role": "user",   "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 300,
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()
