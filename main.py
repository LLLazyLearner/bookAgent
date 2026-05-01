from agent_service import ask, memory


while True:
    print(f"当前摘要：{memory.summary or '无'}")
    print(f"当前最近对话：{memory.chat_history}")

    user_input = input("请输入你的问题：").strip()
    if user_input == "exit":
        break

    result = ask(user_input)
    print(result["reply"])
