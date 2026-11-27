from datetime import datetime, timezone

from digest import build_messages
from reader import Post


def test_empty_digest_still_reports():
    msgs = build_messages([], 42, datetime(2026, 11, 27, 0, 5, tzinfo=timezone.utc))
    assert msgs == ["<b>0 matches today (27 Nov)</b>, from 42 new posts"]


def test_long_digest_is_split_under_limit():
    posts = [Post("c", i, None, "x" * 300 + "\n" + "y" * 300, f"https://t.me/c/{i}") for i in range(30)]
    msgs = build_messages(posts, 30, datetime(2026, 11, 27, tzinfo=timezone.utc))
    assert len(msgs) > 1
    assert all(len(m) <= 4096 for m in msgs)


def test_entry_escapes_html():
    posts = [Post("c", 1, None, "Rate <$60> & up", "https://t.me/c/1")]
    msg = build_messages(posts, 1, datetime(2026, 11, 27, tzinfo=timezone.utc))[0]
    assert "Rate &lt;$60&gt; &amp; up" in msg
