from reader import fetch_new_posts, parse_page


def msg(channel, i, text, reply=None):
    reply_html = (
        f'<a class="tgme_widget_message_reply"><div class="tgme_widget_message_text">{reply}</div></a>'
        if reply
        else ""
    )
    return f"""
<div class="tgme_widget_message_wrap js-widget_message_wrap">
  <div class="tgme_widget_message text_not_supported_wrap js-widget_message" data-post="{channel}/{i}">
    <div class="tgme_widget_message_bubble">
      {reply_html}
      <div class="tgme_widget_message_text js-message_text" dir="auto">{text}</div>
      <div class="tgme_widget_message_footer">
        <a class="tgme_widget_message_date" href="https://t.me/{channel}/{i}">
          <time datetime="2026-11-27T03:59:12+00:00" class="time">11:59</time></a>
      </div>
    </div>
  </div>
</div>"""


def page(channel, ids):
    return "<html><body>" + "".join(msg(channel, i, f"Post {i}<br/>line two") for i in ids) + "</body></html>"


def test_parse_page_reads_id_text_link_date():
    posts = parse_page(page("sgTuitions", [101, 100]), "sgtuitions")
    assert [p.id for p in posts] == [100, 101]
    assert posts[0].text == "Post 100\nline two"
    assert posts[0].link == "https://t.me/sgTuitions/100"
    assert posts[0].date.isoformat() == "2026-11-27T03:59:12+00:00"


def test_parse_page_ignores_quoted_reply_text():
    html = msg("c", 5, "Own text", reply="Quoted text")
    assert parse_page(html, "c")[0].text == "Own text"


def test_fetch_new_posts_pages_back_until_last_id():
    pages = {None: list(range(41, 61)), 41: list(range(21, 41)), 21: list(range(1, 21))}
    calls = []

    def fake_fetch(channel, before):
        calls.append(before)
        return page(channel, pages[before])

    posts = fetch_new_posts("c", 30, fetch=fake_fetch)
    assert [p.id for p in posts] == list(range(31, 61))
    assert calls == [None, 41]  # stopped once it reached ID 30


def test_fetch_new_posts_nothing_new():
    posts = fetch_new_posts("c", 60, fetch=lambda c, b: page(c, list(range(41, 61))))
    assert posts == []
