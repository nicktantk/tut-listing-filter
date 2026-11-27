"""Print your chat ID. First open your bot in Telegram and press Start (or send it any message).

Usage: BOT_TOKEN=123:abc python get_chat_id.py
"""
import os

import requests

token = os.environ["BOT_TOKEN"]
updates = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=30).json()
chats = {}
for u in updates.get("result", []):
    msg = u.get("message") or u.get("edited_message") or {}
    chat = msg.get("chat")
    if chat:
        chats[chat["id"]] = chat.get("username") or chat.get("first_name") or ""
if not chats:
    print("No messages yet. Send your bot a message in Telegram, then run this again.")
for chat_id, name in chats.items():
    print(f"{chat_id}\t{name}")
