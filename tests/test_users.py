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
