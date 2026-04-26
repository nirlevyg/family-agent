import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def run_morning_routine():
    with open("SOUL.md", encoding="utf-8") as f:
        soul = f.read()
    with open("morning-routine.md", encoding="utf-8") as f:
        routine = f.read()
    with open("tasks.md", encoding="utf-8") as f:
        tasks = f.read()

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=soul,
        messages=[
            {
                "role": "user",
                "content": f"הרץ את שגרת הבוקר.\n\nשגרה:\n{routine}\n\nמשימות נוכחיות:\n{tasks}",
            }
        ],
    )
    print(message.content[0].text)


if __name__ == "__main__":
    run_morning_routine()
