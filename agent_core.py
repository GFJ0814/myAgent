import json
import os
from typing import Any

from openai import OpenAI
from skill_loader import load_skills
from tools import TOOLS


MAX_TURNS = 20
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "ep-20260212155102-7ccnk"
BASE_SYSTEM_PROMPT = """You are a helpful AI assistant.
Think step by step. Use tools for single atomic actions such as reading files,
writing files, running shell commands, or executing Python code. Use skills for
multi-step tasks or reusable workflows. When the task is complete, respond
directly without calling any tool or skill."""


def load_capabilities() -> dict[str, dict[str, Any]]:
    capabilities = dict(TOOLS)
    for name, skill in load_skills().items():
        if name not in capabilities:
            capabilities[name] = skill
    return capabilities


def build_client() -> OpenAI:
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        raise RuntimeError("please set ARK_API_KEY environment variable")
    return OpenAI(api_key=api_key, base_url=ARK_BASE_URL)


def build_system_prompt(capabilities: dict[str, dict[str, Any]]) -> str:
    lines = [BASE_SYSTEM_PROMPT, "", "Available capabilities:"]
    for name, entry in capabilities.items():
        kind = entry.get("kind", "tool")
        description = entry["schema"]["function"]["description"]
        lines.append(f"- {name} ({kind}): {description}")
    return "\n".join(lines)


def execute_capability(
    name: str,
    args: dict[str, Any],
    client: OpenAI,
    capabilities: dict[str, dict[str, Any]],
) -> str:
    entry = capabilities.get(name)
    if entry is None:
        return f"[error] unknown capability: {name}"

    if entry.get("kind") == "skill":
        return execute_skill(entry, args, client)

    return entry["function"](**args)


def execute_skill(skill_entry: dict[str, Any], args: dict[str, Any], client: OpenAI) -> str:
    task = str(args.get("task", "")).strip()
    if not task:
        return "[error] skill requires a non-empty 'task' argument"

    skill_name = skill_entry["name"]
    description = skill_entry["description"]
    instructions = skill_entry["instructions"]
    skill_prompt = f"""You are executing the skill "{skill_name}".
Skill description: {description}

Follow these skill instructions:
{instructions}

Use the available tools when necessary. Do not call any skill from within a
skill. Return the final result directly when the task is complete."""
    skill_messages = [{"role": "user", "content": task}]
    return run_agent_loop(skill_messages, client, TOOLS, skill_prompt)


def run_agent_loop(
    messages: list,
    client: OpenAI,
    capabilities: dict[str, dict[str, Any]],
    system_prompt: str,
) -> str:
    capability_schemas = [entry["schema"] for entry in capabilities.values()]

    for _ in range(1, MAX_TURNS + 1):
        request_messages = [{"role": "system", "content": system_prompt}, *messages]

        response = client.chat.completions.create(
            model=os.environ.get("ARK_MODEL", DEFAULT_MODEL),
            messages=request_messages,
            tools=capability_schemas,
        )
        choice = response.choices[0]
        assistant_msg = choice.message
        print(f"  [assistant] {assistant_msg.content}")
        print(f"  [tool_calls] {assistant_msg.tool_calls}")

        messages.append(assistant_msg.model_dump())

        if not assistant_msg.tool_calls:
            return assistant_msg.content or ""

        for tool_call in assistant_msg.tool_calls:
            name = tool_call.function.name
            raw_args = tool_call.function.arguments
            print(f"  [capability] {name}({raw_args})")

            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                args = {}

            result = execute_capability(name, args, client, capabilities)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

    return "[agent] reached maximum turns, stopping."


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
    capabilities = load_capabilities()
    system_prompt = build_system_prompt(capabilities)
    return run_agent_loop(messages, client, capabilities, system_prompt)


def main() -> None:
    from cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
