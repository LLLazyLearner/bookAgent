from init_llm import llm
from template import get_prompt
from tools import create_tts
from langchain.agents import create_agent
from SummaryMemory import SummaryMemory

book_prompt_ch = get_prompt("ch")
current_date = "2024-01-15"
user_preferences = "喜欢经典文学"

system_prompt = (
    book_prompt_ch.messages[0].prompt.format(
        current_date=current_date,
        user_preferences=user_preferences,
    )
    + "\n\n## 字数限制：回答请控制在 50 字以内。"
)

agent = create _agent(
    model=llm,
    tools=[create_tts],
    system_prompt=system_prompt,
)

memory = SummaryMemory(llm, max_size=3)

while True:
    print(f"当前摘要：{memory.summary or '无'}")
    print(f"当前最近对话：{memory.chat_history}")

    user_input = input("请输入你的问题：").strip()
    if user_input == "exit":
        break

    memory.append("user", user_input)

    result = agent.invoke({
        "messages": memory.messages()
    })

    reply = result["messages"][-1].content
    memory.append("assistant", reply)

    print(reply)

#todo:上图形化界面
#todo:上rag功能
