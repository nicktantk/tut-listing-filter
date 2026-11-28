"""Daily run: read new posts from each source channel, keep matches, DM one digest, save state.

State is saved only after the digest is sent, so a failed run repeats posts next time
but never skips them.
"""

from __future__ import annotations

import html
from dataclasses import replace
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import yaml

from filters import matches
from jobs import split_jobs, summary_lines
from reader import Post, fetch_new_posts

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.yaml"
STATE_PATH = ROOT / "state.json"
SGT = timezone(timedelta(hours=8))
TELEGRAM_LIMIT = 4000  # Telegram allows 4096 characters per message
PREVIEW_LINES = 6
LAST_SENT = "_last_sent"  # date of the last digest, kept in state.json


def load_state() -> dict[str, int]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {}


def save_state(state: dict[str, int]) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def collect(channel: str, last_id: int | None, now: datetime) -> tuple[list[Post], int | None, bool]:
    """New posts since last_id, the ID to store next, and whether the page cap was hit."""
    if last_id is not None:
        posts, capped = fetch_new_posts(channel, after_id=last_id)
        return posts, max([p.id for p in posts], default=last_id), capped
    # First time we see this channel: take the last 24 hours so the first digest isn't empty.
    posts, capped = fetch_new_posts(channel, since=now - timedelta(hours=24))
    return posts, max([p.id for p in posts], default=None), capped


def format_entry(n: int, post: Post) -> str:
    body = "\n".join(html.escape(l) for l in summary_lines(post.text, PREVIEW_LINES))
    return f"<b>{n}.</b> {body}\n<a href=\"{post.link}\">Open post</a> · @{html.escape(post.channel)}"


def build_messages(matched: list[Post], checked: int, now: datetime) -> list[str]:
    day = now.astimezone(SGT).strftime("%d %b")
    header = f"<b>{len(matched)} match{'es' if len(matched) != 1 else ''} today ({day})</b>, from {checked} new posts"
    if not matched:
        return [header]
    messages, current = [], header
    for i, post in enumerate(matched, 1):
        entry = format_entry(i, post)
        if len(current) + len(entry) + 2 > TELEGRAM_LIMIT:
            messages.append(current)
            current = entry
        else:
            current += "\n\n" + entry
    messages.append(current)
    return messages


def send(messages: list[str], token: str, chat_id: str) -> None:
    for text in messages:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=30,
        )
        if not resp.ok:
            raise RuntimeError(f"Telegram sendMessage failed: {resp.status_code} {resp.text}")


def load_chat_ids(users: list[dict]) -> dict[str, str]:
    """Chat IDs come from secrets, so they never appear in this (public) repo.

    CHAT_IDS holds one "name: id" line per person. The first person in config.yaml
    also falls back to the older single CHAT_ID secret.
    """
    ids = {}
    raw = os.environ.get("CHAT_IDS", "").strip()
    if raw:
        parsed = yaml.safe_load(raw) or {}
        ids = {str(k).strip().lower(): str(v).strip() for k, v in parsed.items() if v}
    first = str(users[0]["name"]).lower() if users else None
    if first and first not in ids and os.environ.get("CHAT_ID"):
        ids[first] = os.environ["CHAT_ID"].strip()
    return ids


def main() -> int:
    token = os.environ["BOT_TOKEN"]
    config = yaml.safe_load(CONFIG_PATH.read_text())
    users = config.get("users", [])
    chat_ids = load_chat_ids(users)
    state = load_state()
    now = datetime.now(timezone.utc)
    today = now.astimezone(SGT).date().isoformat()

    # The schedule fires twice as a backup, since GitHub sometimes drops scheduled runs.
    # A scheduled run does nothing if today's digest already went out.
    if os.environ.get("GITHUB_EVENT_NAME") == "schedule" and state.get(LAST_SENT) == today:
        print(f"Today's digest ({today}) was already sent; nothing to do.")
        return 0

    new_state = dict(state)
    matched: dict[str, list[Post]] = {u["name"]: [] for u in users}
    checked = 0
    failed: list[str] = []
    capped_channels: list[str] = []

    for channel in config["sources"]:
        key = channel.lstrip("@").lower()
        try:
            posts, next_id, capped = collect(channel.lstrip("@"), state.get(key), now)
        except Exception as exc:  # one broken channel shouldn't stop the digest
            print(f"[warn] {channel}: {exc}", file=sys.stderr)
            failed.append(channel)
            continue
        checked += len(posts)
        for post in posts:
            # A post can hold several jobs; match and show each one on its own.
            jobs = [replace(post, text=t) for t in split_jobs(post.text)]
            for user in users:
                matched[user["name"]] += [j for j in jobs if matches(j, user.get("criteria", {}))]
        if next_id is not None:
            new_state[key] = next_id
        if capped:
            capped_channels.append(channel)
        print(f"{channel}: {len(posts)} new{' (page cap reached, older posts skipped)' if capped else ''}")

    sent_any = False
    for i, user in enumerate(users):
        name = user["name"]
        chat_id = chat_ids.get(str(name).lower())
        if not chat_id:
            print(f"Skipping {name}: no chat ID yet (add '{name}: <id>' to the CHAT_IDS secret)")
            continue
        messages = build_messages(matched[name], checked, now)
        if i == 0:  # problems are only reported to the first person (the admin)
            if failed:
                messages[-1] += "\n\nCouldn't read: " + ", ".join(html.escape(c) for c in failed)
            if capped_channels:
                messages[-1] += (
                    "\n\nToo many posts to read them all in: "
                    + ", ".join(html.escape(c) for c in capped_channels)
                    + ". Consider running more often."
                )
        send(messages, token, chat_id)
        sent_any = True
        print(f"Sent {name} {len(matched[name])} matches from {checked} posts.")

    if not sent_any:
        print("No one has a chat ID, so nothing was sent and state was not saved.", file=sys.stderr)
        return 1
    new_state[LAST_SENT] = today
    save_state(new_state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
