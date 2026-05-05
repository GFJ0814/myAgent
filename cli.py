from agent_service import AgentService


def main() -> None:
    service = AgentService()
    session_id = service.create_session("cli-default")
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
            service.clear_session(session_id)
            print("(context cleared)\n")
            continue

        reply = service.chat(session_id, user_input)
        print(f"\nAgent> {reply}\n")


if __name__ == "__main__":
    main()
