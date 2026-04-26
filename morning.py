import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import anthropic
import httpx

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def send_telegram(text: str):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    group_id = os.environ["TELEGRAM_GROUP_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    httpx.post(url, json={"chat_id": group_id, "text": text, "parse_mode": "Markdown"})


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
                "content": f"הרץ את שגרת הבוקר.\n\nתאריך והיום: {datetime.now().strftime('%A %d/%m/%Y')}\n\nשגרה:\n{routine}\n\nמשימות נוכחיות:\n{tasks}",
            }
        ],
    )
    text = message.content[0].text
    print(text)
    send_telegram(text)


if __name__ == "__main__":
    run_morning_routine()
