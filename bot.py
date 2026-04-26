import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv
import httpx

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GROUP_ID = os.environ["TELEGRAM_GROUP_ID"]
TASKS_FILE = Path("tasks.md")
OFFSET_FILE = Path(".bot_offset")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


def get_updates(offset=None):
    params = {"timeout": 30}
    if offset is not None:
        params["offset"] = offset
    r = httpx.get(
        f"{BASE_URL}/getUpdates",
        params=params,
        timeout=httpx.Timeout(connect=10, read=40, write=10, pool=10),
    )
    return r.json().get("result", [])


def send(text: str):
    r = httpx.post(f"{BASE_URL}/sendMessage", json={
        "chat_id": GROUP_ID,
        "text": text,
        "parse_mode": "Markdown",
    })
    print(f"sendMessage status={r.status_code} body={r.text[:200]}")


def load_tasks():
    content = TASKS_FILE.read_text(encoding="utf-8")
    pending, done = [], []
    section = None
    for line in content.splitlines():
        if "## ממתין" in line:
            section = "pending"
        elif "## הושלם" in line:
            section = "done"
        elif line.startswith("- [ ]") and section == "pending":
            pending.append(line[6:].strip())
        elif line.startswith("- [x]") and section == "done":
            done.append(line[6:].strip())
    return pending, done


def save_tasks(pending, done):
    lines = ["# משימות\n", "## ממתין\n"]
    for t in pending:
        lines.append(f"- [ ] {t}\n")
    lines.append("\n## הושלם\n")
    for t in done:
        lines.append(f"- [x] {t}\n")
    TASKS_FILE.write_text("".join(lines), encoding="utf-8")


def handle(text: str):
    text = text.strip()

    if text.startswith("/add ") or text.startswith("/הוסף "):
        task = re.sub(r"^/\S+\s+", "", text)
        pending, done = load_tasks()
        pending.append(task)
        save_tasks(pending, done)
        send(f"✅ נוספה משימה: *{task}*")

    elif text.startswith("/done ") or text.startswith("/בוצע "):
        num = re.sub(r"^/\S+\s+", "", text)
        try:
            idx = int(num) - 1
            pending, done = load_tasks()
            task = pending.pop(idx)
            done.append(task)
            save_tasks(pending, done)
            send(f"✔️ סומן כהושלם: *{task}*")
        except (ValueError, IndexError):
            send("❌ מספר משימה לא תקין. השתמש ב-/list לראות את המספרים.")

    elif text in ("/list", "/רשימה"):
        pending, _ = load_tasks()
        if not pending:
            send("אין משימות פתוחות 🎉")
        else:
            lines = ["📋 *משימות פתוחות:*\n"]
            for i, t in enumerate(pending, 1):
                lines.append(f"{i}. {t}")
            send("\n".join(lines))

    elif text in ("/help", "/עזרה"):
        send(
            "🤖 *פקודות זמינות:*\n\n"
            "/add <משימה> — הוסף משימה חדשה\n"
            "/done <מספר> — סמן משימה כהושלמה\n"
            "/list — הצג משימות פתוחות\n"
            "/help — הצג עזרה"
        )


def load_offset():
    if OFFSET_FILE.exists():
        return int(OFFSET_FILE.read_text().strip())
    return None


def save_offset(offset):
    OFFSET_FILE.write_text(str(offset))


def main():
    import time
    print(f"🤖 Bot is running... GROUP_ID={GROUP_ID!r}")
    offset = load_offset()
    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                save_offset(offset)
                msg = update.get("message", {})
                text = msg.get("text", "")
                chat_id = str(msg.get("chat", {}).get("id", ""))
                if text and chat_id == GROUP_ID:
                    handle(text)
        except Exception as e:
            print(f"Connection error: {e} — retrying in 10s")
            time.sleep(10)


if __name__ == "__main__":
    main()
