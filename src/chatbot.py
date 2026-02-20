"""
AI 聊天机器人 — 支持 Claude API 和 OpenAI API
支持多轮对话、系统提示词、温度调节

知识点：
  1. LLM API 调用模式
  2. System Prompt 设计
  3. 多轮对话上下文管理
  4. 流式 vs 非流式输出
  5. Temperature 参数对创造性的影响
"""
import os
import json
import sys

# ── 配置 ──
# 设置你的 API Key: export ANTHROPIC_API_KEY=sk-xxx  或  export OPENAI_API_KEY=sk-xxx
PROVIDER = "claude"  # 可选: "claude" 或 "openai"
MODEL = "claude-sonnet-5" if PROVIDER == "claude" else "gpt-4o"


class Chatbot:
    def __init__(self, system_prompt: str = "你是一个有帮助的AI助手。", temperature: float = 0.7):
        self.system = system_prompt
        self.temperature = temperature
        self.history = []

    def chat(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})

        messages = [{"role": "system", "content": self.system}] + self.history

        try:
            # 调用 Claude API (兼容 OpenAI SDK 格式)
            import requests
            api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                return "⚠️ 请设置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY 环境变量"

            headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
            body = {
                "model": "claude-sonnet-5-20251001",
                "max_tokens": 1024,
                "temperature": self.temperature,
                "system": self.system,
                "messages": self.history,
            }
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers, json=body, timeout=30,
            )
            data = resp.json()
            reply = data["content"][0]["text"]
        except Exception as e:
            reply = f"API 调用失败: {e}"

        self.history.append({"role": "assistant", "content": reply})
        return reply

    def clear(self):
        self.history = []


# ── CLI 演示模式（无需 API Key 即可运行）──
def demo():
    print("=" * 55)
    print("🤖 AI Chatbot — 调用 Claude/OpenAI API")
    print("=" * 55)
    print("\n📋 架构说明:")
    print("  User Input → System Prompt → LLM API → Response")
    print("\n💡 核心参数:")
    print("  • System Prompt: 控制AI的角色和行为边界")
    print("  • Temperature: 0=确定, 1=创造 (越高越随机)")
    print("  • Max Tokens: 限制输出长度")
    print("  • Context Window: 多轮对话历史管理")
    print("\n🔑 使用真实 API:")
    print("  export ANTHROPIC_API_KEY=sk-ant-xxx")
    print("  python src/chatbot.py")
    print("\n📝 示例对话:")
    demos = [
        ("用户", "用Python写一个快速排序"),
        ("AI", "(此处需 API Key)  def quicksort(arr): ..."),
        ("用户", "能加注释吗？"),
        ("AI", "(多轮对话：AI记得上一轮在说快排)"),
    ]
    for role, msg in demos:
        print(f"  [{role}] {msg}")

    if "ANTHROPIC_API_KEY" in os.environ or "OPENAI_API_KEY" in os.environ:
        bot = Chatbot("你是一个Python编程专家。")
        print("\n🟢 API Key 已配置，进入对话模式...")
        while True:
            u = input("\n你 > ")
            if u.lower() in ("q", "quit", "exit"):
                break
            print(f"AI > {bot.chat(u)}")


if __name__ == "__main__":
    demo()
