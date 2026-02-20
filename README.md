# 🤖 AI Chatbot — LLM API 调用

> 调用 Claude/OpenAI API 的智能聊天机器人，支持多轮对话

## 🧠 知识点
- **LLM API 调用**: RESTful API + HTTP Headers + JSON Body 标准模式
- **System Prompt**: 控制 AI 的角色、语气、知识范围
- **多轮对话**: 每次请求携带完整对话历史，模型才能"记住"上下文
- **Temperature**: 0→确定性输出，1→高创造性
- **Token**: LLM 计费单位，≈0.75 英文词 ≈0.5 中文字

## 🚀 运行
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key-here
python src/chatbot.py
```

---

Day 4 | 2026-02-20 | [sxmoon000](https://github.com/sxmoon000)
