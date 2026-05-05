import json
import os
import sys

from openai import OpenAI
from tools import TOOLS


MAX_TURNS = 20
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "ep-20260212155102-7ccnk"

SYSTEM_PROMPT = """You are a helpful AI assistant with access to the following tools:
1. shell_exec — run shell commands
2. file_read — read file contents
3. file_write — write content to a file
4. python_exec — execute Python code
Think step by step. Use tools when you need to interact with the file system, \
run commands, or execute code. When the task is complete, respond directly \
without calling any tool."""


def agent_loop(user_message: str, messages: list, client: OpenAI) -> str:
    """
    Agent Loop: while 循环驱动 LLM 推理与工具调用。
    流程：
    1. 将用户消息追加到 messages
    2. 调用 LLM
    3. 若 LLM 返回 tool_calls -> 逐个执行 -> 结果追加到 messages -> 继续循环
    4. 若 LLM 直接返回文本（无 tool_calls）-> 退出循环，返回文本
    5. 安全上限 MAX_TURNS 轮
    """
    messages.append({"role": "user", "content": user_message})
    tool_schemas = [t["schema"] for t in TOOLS.values()]

    for _ in range(1, MAX_TURNS + 1):
        if messages and messages[0].get("role") == "system":
            request_messages = messages
        else:
            request_messages = [{"role": "system", "content": SYSTEM_PROMPT}, *messages]

        # --- LLM Call ---
        response = client.chat.completions.create(
            model=os.environ.get("ARK_MODEL", DEFAULT_MODEL),
            messages=request_messages,
            tools=tool_schemas,
        )
        choice = response.choices[0]
        assistant_msg = choice.message

        # 将 assistant 消息追加到上下文
        messages.append(assistant_msg.model_dump())

        # --- 终止条件：无 tool_calls ---
        if not assistant_msg.tool_calls:
            return assistant_msg.content or ""

        # --- 执行每个 tool_call ---
        for tool_call in assistant_msg.tool_calls:
            name = tool_call.function.name
            raw_args = tool_call.function.arguments
            print(f"  [tool] {name}({raw_args})")

            # 解析参数并调用工具
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                args = {}

            tool_entry = TOOLS.get(name)
            if tool_entry is None:
                result = f"[error] unknown tool: {name}"
            else:
                result = tool_entry["function"](**args)

            # 将工具结果追加到上下文
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

    return "[agent] reached maximum turns, stopping."


def main() -> None:
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        print("Error: please set ARK_API_KEY environment variable.")
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=ARK_BASE_URL)
    messages: list = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("Agent ready. Type your message (or 'exit' to quit, 'clear' to reset).\n")

    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("Bye.")
            break

        if user_input.lower() == "clear":
            messages.clear()
            messages.append({"role": "system", "content": SYSTEM_PROMPT})
            print("(context cleared)\n")
            continue

        reply = agent_loop(user_input, messages, client)
        print(f"\nAgent> {reply}\n")


if __name__ == "__main__":
    main()
