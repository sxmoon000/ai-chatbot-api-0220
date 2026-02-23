"""
对话记忆系统 — 长期记忆 + 角色扮演 + Token 管理

v1.1 新增:
  • 短时记忆 (当前会话) + 长期记忆 (JSON持久化)
  • 角色预设: 编程助手/文案写手/心理咨询/面试官
  • Token 计数器 + 预算管理 (截断策略)
  • 对话摘要: 长对话自动压缩为摘要
  • 记忆检索: 根据当前问题召回相关历史
"""
import json
import re
import tiktoken
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from collections import OrderedDict


# ── 角色预设 ──
ROLES = {
    "编程助手": {
        "prompt": "你是一位经验丰富的软件工程师。用简洁的代码示例回答问题，解释关键设计决策。",
        "style": "技术、高效、代码优先",
        "temperature": 0.3,
    },
    "文案写手": {
        "prompt": "你是一位创意文案专家。语言生动有力，擅长用故事打动读者，熟悉社交媒体写作风格。",
        "style": "创意、感性、精炼",
        "temperature": 0.9,
    },
    "心理咨询": {
        "prompt": "你是一位温暖的心理咨询师。用共情的方式倾听和回应，不评判，引导积极思考。",
        "style": "温暖、共情、非评判",
        "temperature": 0.7,
    },
    "面试官": {
        "prompt": "你是一位严格的面试官。根据岗位要求提出有深度的问题，评估候选人的真实能力。",
        "style": "专业、尖锐、结构化",
        "temperature": 0.5,
    },
    "英文老师": {
        "prompt": "你是一位耐心的英语老师。纠正语法错误，解释地道表达，鼓励多说多练。",
        "style": "教育、鼓励、细致",
        "temperature": 0.6,
    },
}


@dataclass
class MemoryEntry:
    role: str       # user / assistant / system
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    importance: int = 1  # 1-5, 用于长期记忆排序
    tags: List[str] = field(default_factory=list)


class MemoryManager:
    """对话记忆管理"""

    def __init__(self, max_short_term: int = 20, max_long_term: int = 500):
        self.short_term: List[MemoryEntry] = []
        self.long_term: OrderedDict = OrderedDict()  # key: 摘要
        self.max_short = max_short_term
        self.max_long = max_long_term
        self.summary = ""  # 对话摘要

    def add(self, role: str, content: str, importance: int = 1):
        entry = MemoryEntry(role, content, importance=importance)
        self.short_term.append(entry)

        # 超过上限 → 最旧的转入长期记忆
        if len(self.short_term) > self.max_short:
            old = self.short_term.pop(0)
            self._archive(old)

    def _archive(self, entry: MemoryEntry):
        """归档到长期记忆"""
        key = entry.content[:60]
        self.long_term[key] = entry
        if len(self.long_term) > self.max_long:
            self.long_term.popitem(last=False)

    def get_context(self, max_tokens: int = 4000) -> List[dict]:
        """获取当前上下文 (含摘要压缩)"""
        messages = []

        # 如果有摘要，先加入
        if self.summary:
            messages.append({"role": "system", "content": f"[对话历史摘要] {self.summary}"})

        # 加入短期记忆
        token_count = 0
        # 用简单方式估算: ~4 chars = 1 token for English, ~1.5 chars for Chinese
        for entry in self.short_term:
            est_tokens = self._estimate_tokens(entry.content)
            if token_count + est_tokens > max_tokens:
                # 触发压缩
                self._compress()
                break
            messages.append({"role": entry.role, "content": entry.content})
            token_count += est_tokens

        return messages

    def _estimate_tokens(self, text: str) -> int:
        """估算 token 数"""
        try:
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except:
            return len(text) // 2

    def _compress(self):
        """压缩: 将早期对话转为摘要"""
        if len(self.short_term) < 6:
            return

        # 取前1/3做摘要
        split = len(self.short_term) // 3
        to_summarize = self.short_term[:split]
        topics = " → ".join(set(e.content[:20] for e in to_summarize if e.role == "user"))

        self.summary = f"之前讨论了: {topics}"
        self.short_term = self.short_term[split:]

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """从长期记忆检索相关内容 (简单关键词匹配)"""
        query_words = set(query.lower().split())
        scored = []
        for key, entry in self.long_term.items():
            content_words = set(entry.content.lower().split())
            overlap = len(query_words & content_words)
            if overlap > 0:
                scored.append((overlap * entry.importance, entry.content))
        scored.sort(reverse=True)
        return [c for _, c in scored[:top_k]]

    def stats(self) -> dict:
        return {
            "short_term_count": len(self.short_term),
            "long_term_count": len(self.long_term),
            "has_summary": bool(self.summary),
            "total_est_tokens": sum(self._estimate_tokens(e.content) for e in self.short_term),
        }

    def clear(self):
        self.short_term.clear()
        self.summary = ""


def main():
    print("=" * 55)
    print("🧠 对话记忆系统 v1.1")
    print("=" * 55)

    mm = MemoryManager(max_short_term=8)

    # 模拟对话
    dialogue = [
        ("user", "Hi, I need help with a Python data pipeline", 1),
        ("assistant", "Sure! What kind of data are you working with?", 1),
        ("user", "It's CSV files from IoT sensors, about 10GB per day", 2),
        ("assistant", "For 10GB/day, I'd recommend using Dask or Polars for out-of-core processing", 3),
        ("user", "Great, can you show me a Dask example?", 1),
        ("assistant", "Here's how you'd set it up:\n```python\nimport dask.dataframe as dd\ndf = dd.read_csv('sensor_*.csv')\n```", 3),
        ("user", "What about error handling when files are corrupted?", 2),
        ("assistant", "Good question! You can wrap reads in try/except or use Dask's built-in error handling", 2),
    ]

    for role, content, importance in dialogue:
        mm.add(role, content, importance)

    print(f"\n📊 记忆统计: {mm.stats()}")

    # 检索
    results = mm.retrieve("error handling corrupted files")
    print(f"\n🔍 检索 'error handling':")
    for i, r in enumerate(results, 1):
        print(f"   {i}. {r[:80]}...")

    # Token 预算
    print(f"\n💾 当前上下文 (最多4000 tokens):")
    ctx = mm.get_context(100)
    for msg in ctx:
        print(f"   [{msg['role']}] {msg['content'][:60]}...")

    # 角色展示
    print(f"\n🎭 可用角色:")
    for name, cfg in ROLES.items():
        print(f"   {name}: {cfg['style']} (temperature={cfg['temperature']})")

    print(f"\n✅ 记忆系统演示完成")


if __name__ == "__main__":
    main()
