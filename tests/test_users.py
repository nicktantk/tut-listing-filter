from digest import load_chat_ids

USERS = [{"name": "nicholas"}, {"name": "friend"}]


def test_first_user_falls_back_to_chat_id(monkeypatch):
    monkeypatch.setenv("CHAT_ID", "111")
    monkeypatch.delenv("CHAT_IDS", raising=False)
    assert load_chat_ids(USERS) == {"nicholas": "111"}


def test_chat_ids_secret_adds_friends(monkeypatch):
    monkeypatch.setenv("CHAT_ID", "111")
    monkeypatch.setenv("CHAT_IDS", "Friend: 222\n")
    assert load_chat_ids(USERS) == {"friend": "222", "nicholas": "111"}


def test_chat_ids_secret_wins_over_chat_id(monkeypatch):
    monkeypatch.setenv("CHAT_ID", "111")
    monkeypatch.setenv("CHAT_IDS", "nicholas: 333")
    assert load_chat_ids(USERS)["nicholas"] == "333"


def test_name_lines_in_chat_id_secret(monkeypatch):
    monkeypatch.setenv("CHAT_ID", "nicholas: 111\nchloe: 1003228034")
    monkeypatch.delenv("CHAT_IDS", raising=False)
    assert load_chat_ids(USERS) == {"nicholas": "111", "chloe": "1003228034"}


def test_parse_keeps_leading_zeros():
    from digest import _parse_ids

    assert _parse_ids("nicholas: 018956\nChloe : 470629") == {"nicholas": "018956", "chloe": "470629"}
