"""
HR Reminders Bot — birthdays & work anniversaries -> Slack

Як це працює:
1. Скрипт читає employees.json
2. Порівнює місяць+день кожного співробітника з сьогоднішньою датою
3. Якщо збіг — формує повідомлення і надсилає в Slack через Incoming Webhook

Запуск вручну (для тесту):
    SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..." python3 reminders.py

У продакшені запускається автоматично щодня через GitHub Actions
(див. .github/workflows/reminders.yml)
"""

import json
import os
import sys
from datetime import date, datetime


def load_employees(path: str = "employees.json") -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def years_between(past_date: date, today: date) -> int:
    years = today.year - past_date.year
    return years


def build_messages(employees: list[dict], today: date) -> list[str]:
    messages = []

    for emp in employees:
        name = emp.get("name", "Хтось")
        mention = emp.get("slack_mention", "")
        who = f"{mention} ({name})" if mention else name

        birthday = emp.get("birthday")
        if birthday:
            bday = datetime.strptime(birthday, "%Y-%m-%d").date()
            if (bday.month, bday.day) == (today.month, today.day):
                age = years_between(bday, today)
                messages.append(
                    f":birthday: Сьогодні день народження святкує {who}! "
                    f"Виповнюється {age} :tada: Не забудьте привітати!"
                )

        start_date = emp.get("start_date")
        if start_date:
            sdate = datetime.strptime(start_date, "%Y-%m-%d").date()
            if (sdate.month, sdate.day) == (today.month, today.day) and sdate.year != today.year:
                years = years_between(sdate, today)
                messages.append(
                    f":tada: Сьогодні {who} відзначає {years}-річчя роботи в компанії! "
                    f"Дякуємо за внесок! :clap:"
                )

    return messages


def post_to_slack(webhook_url: str, text: str) -> None:
    import urllib.request

    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Slack webhook returned status {resp.status}")


def main() -> None:
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("ПОМИЛКА: змінна оточення SLACK_WEBHOOK_URL не задана.", file=sys.stderr)
        sys.exit(1)

    employees = load_employees()
    today = date.today()
    messages = build_messages(employees, today)

    if not messages:
        print(f"{today}: сьогодні нема кого вітати.")
        return

    for msg in messages:
        post_to_slack(webhook_url, msg)
        print(f"Надіслано в Slack: {msg}")


if __name__ == "__main__":
    main()
