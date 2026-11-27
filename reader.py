"""Read posts from a public Telegram channel's web preview (https://t.me/s/<channel>).

No Telegram login is needed. Only public channels with a @username have a preview.
All HTML parsing lives in parse_page(), so a change to Telegram's markup is fixed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import time

import requests
from bs4 import BeautifulSoup

PREVIEW_URL = "https://t.me/s/{channel}"
USER_AGENT = "Mozilla/5.0 (compatible; tuition-digest/1.0)"
MAX_PAGES = 50  # safety cap per channel per run (about 20 posts a page, so ~1,000 posts)
PAGE_DELAY = 0.5  # seconds between page loads, to be polite to t.me


@dataclass
class Post:
    channel: str
    id: int
    date: Optional[datetime]
    text: str
    link: str


def clean_text(div) -> str:
    """The post's text with its real line breaks. Inline tags (bold, emoji) don't add breaks."""
    for br in div.find_all("br"):
        br.replace_with("\n")
    lines = [line.strip() for line in div.get_text().splitlines()]
    text = "\n".join(lines)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.strip()


def parse_page(html: str, channel: str) -> list[Post]:
    """Return the posts on one preview page, in page order (oldest first)."""
    soup = BeautifulSoup(html, "html.parser")
    posts: list[Post] = []
    for msg in soup.select("div.tgme_widget_message[data-post]"):
        data_post = msg["data-post"]  # e.g. "sgTuitions/175643"
        try:
            msg_id = int(data_post.rsplit("/", 1)[1])
        except (IndexError, ValueError):
            continue

        # The post's own text, not the text of a message it replies to.
        text_div = None
        for div in msg.select("div.tgme_widget_message_text"):
            if not div.find_parent(class_="tgme_widget_message_reply"):
                text_div = div
                break
        text = clean_text(text_div) if text_div else ""

        date = None
        time_tag = msg.select_one("a.tgme_widget_message_date time[datetime]")
        if time_tag:
            try:
                date = datetime.fromisoformat(time_tag["datetime"])
            except ValueError:
                date = None

        posts.append(
            Post(
                channel=channel,
                id=msg_id,
                date=date,
                text=text,
                link=f"https://t.me/{data_post}",
            )
        )
    posts.sort(key=lambda p: p.id)
    return posts


def fetch_page(channel: str, before: Optional[int] = None, session=None) -> str:
    http = session or requests
    params = {"before": before} if before else None
    resp = http.get(
        PREVIEW_URL.format(channel=channel),
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.text


def fetch_new_posts(
    channel: str,
    after_id: int = 0,
    since: Optional[datetime] = None,
    fetch=fetch_page,
    delay: float = PAGE_DELAY,
) -> tuple[list[Post], bool]:
    """Posts with id > after_id (and, if given, dated at or after `since`), oldest first.

    Pages back with ?before= until it passes after_id or `since`. Returns (posts, capped),
    where capped is True if MAX_PAGES ran out first, meaning older posts were left unread.
    """
    found: dict[int, Post] = {}
    before = None
    for page_no in range(MAX_PAGES):
        if page_no and delay:
            time.sleep(delay)
        page = parse_page(fetch(channel, before), channel)
        if not page:
            return [found[i] for i in sorted(found)], False
        for post in page:
            if post.id > after_id and (since is None or post.date is None or post.date >= since):
                found[post.id] = post
        oldest = page[0]
        if oldest.id <= after_id + 1:
            return [found[i] for i in sorted(found)], False
        if since is not None and oldest.date is not None and oldest.date < since:
            return [found[i] for i in sorted(found)], False
        before = oldest.id
    return [found[i] for i in sorted(found)], True

