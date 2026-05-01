class SummaryMemory:
    def __init__(self, llm, max_size=10):
        self.llm = llm
        self.max_size = max_size
        self.chat_history = []
        self.summary = ""

    def _format_messages(self, messages):
        return "\n".join(f"{message['role']}: {message['content']}" for message in messages)

    def _summarize(self, messages):
        text = self._format_messages(messages)
        old_summary = self.summary or "无"

        prompt = f"""
你是一个对话记忆总结助手。请根据已有摘要和新增对话，生成新的对话摘要。

已有摘要：
{old_summary}

新增对话：
{text}

要求：
1. 保留用户偏好、重要事实、书名、人名、任务目标和未完成事项。
2. 删除寒暄、重复内容和无关细节。
3. 不要编造新增对话里没有的信息。
4. 用简洁中文输出一段摘要。
""".strip()

        summary_result = self.llm.invoke([
            {"role": "user", "content": prompt}
        ])
        return summary_result.content

    def append(self, role, content):
        self.chat_history.append({"role": role, "content": content})

        if len(self.chat_history) > self.max_size:
            messages_to_summarize = self.chat_history[:self.max_size]
            remaining_messages = self.chat_history[self.max_size:]

            self.summary = self._summarize(messages_to_summarize)
            self.chat_history = remaining_messages

    def messages(self):
        if not self.summary:
            return list(self.chat_history)

        return [
            {
                "role": "system",
                "content": f"以下是前面对话摘要，请作为上下文参考：{self.summary}",
            },
            *self.chat_history,
        ]

    def reset(self):
        self.chat_history = []
        self.summary = ""
