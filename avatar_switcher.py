#!/usr/bin/env python3
"""
Slack Avatar & Status Switcher
Automatically changes your Slack profile photo AND status based on schedule.

Requires:
  pip install slack-sdk python-dotenv

Environment variables (set as GitHub Secrets):
  SLACK_USER_TOKEN  — xoxp-... token (see README for how to get it)
"""

import os
import sys
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

TIMEZONE = ZoneInfo("Europe/Warsaw")  # Change to your timezone

# Each slot: avatar image + Slack status emoji + status text
SLOTS = {
    "work": {
        "avatar": "avatars/work.jpg",
        "emoji":  ":computer:",
        "status": "Working",
    },
    "lunch": {
        "avatar": "avatars/lunch.jpg",
        "emoji":  ":fork_and_knife:",
        "status": "Lunch break",
    },
    "evening": {
        "avatar": "avatars/evening.jpg",
        "emoji":  ":house:",
        "status": "Out of office",
    },
    "weekend": {
        "avatar": "avatars/weekend.jpg",
        "emoji":  ":beach_with_umbrella:",
        "status": "Be back Monday",
    },
}


def get_current_slot(now: datetime) -> tuple[str, str]:
    """Return (slot_key, label) for the given datetime."""
    weekday = now.weekday()  # 0=Mon … 6=Sun
    t = now.time()

    if weekday >= 5:
        return "weekend", "🏖 Weekend"

    if time(9, 0) <= t < time(13, 0):
        return "work", "💼 Morning work"

    if time(13, 0) <= t < time(14, 0):
        return "lunch", "🍽 Lunch break"

    if time(14, 0) <= t < time(18, 0):
        return "work", "💼 Afternoon work"

    return "evening", "🌙 Out of office"


# ── Slack helpers ─────────────────────────────────────────────────────────────

def set_avatar(client: WebClient, image_path: str) -> None:
    path = Path(image_path)
    if not path.exists():
        print(f"  ✗ File not found: {image_path}")
        sys.exit(1)

    with open(path, "rb") as f:
        image_data = f.read()

    client.users_setPhoto(image=image_data)
    print(f"  ✓ Avatar set: {image_path}")


def set_status(client: WebClient, emoji: str, text: str) -> None:
    client.users_profile_set(
        profile={
            "status_emoji": emoji,
            "status_text": text,
            "status_expiration": 0,  # 0 = never expires
        }
    )
    print(f"  ✓ Status set: {emoji} {text}")


def main() -> None:
    token = os.environ["SLACK_USER_TOKEN"]
    client = WebClient(token=token)

    now = datetime.now(tz=TIMEZONE)
    slot_key, label = get_current_slot(now)
    slot = SLOTS[slot_key]

    print(f"[{now.strftime('%Y-%m-%d %H:%M %Z')}] Rule matched: {label}")
    print(f"  → Slot: {slot_key}")

    try:
        set_avatar(client, slot["avatar"])
        set_status(client, slot["emoji"], slot["status"])
    except SlackApiError as e:
        print(f"  ✗ Slack API error: {e.response['error']}")
        sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
