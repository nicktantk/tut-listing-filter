# Tuition listing filter

Once a day, reads new posts from public Singapore tuition channels on Telegram, keeps the ones that
match `config.yaml`, and has a bot DM you one digest with a link to each post.

No server, no database and no Telegram login: posts are read from each channel's public web preview
(`https://t.me/s/<channel>`), and the last message ID read per channel is kept in `state.json`.

## Setup (about 10 minutes)

1. **Create the bot.** In Telegram, message @BotFather, send `/newbot` and follow the steps. Copy the token.
2. **Let it message you.** Open your new bot and press **Start**.
3. **Find your chat ID.** On your computer:
   ```
   pip install requests
   BOT_TOKEN=<your token> python get_chat_id.py
   ```
   It prints a number, which is your chat ID.
4. **Add two repo secrets** in GitHub: Settings → Secrets and variables → Actions → New repository secret.
   - `BOT_TOKEN`: the token from step 1
   - `CHAT_ID`: the number from step 3 (used for the first person in `config.yaml`)
   - `CHAT_IDS` (optional): one `name: id` line per extra person
5. **Test it.** Actions tab → *Daily tuition digest* → **Run workflow**. You should get a DM within a minute.

After that it runs every day at about 8 AM Singapore time, with a 9:37 AM backup run that only sends if the first one didn't. Neither secret expires.

## Changing what you get

- **Criteria:** each person under `users` in `config.yaml` has their own `criteria`. The next run uses it.
- **Adding a friend:** (1) they open the bot in Telegram and press **Start**; (2) open
  `https://api.telegram.org/bot<TOKEN>/getUpdates` and find their `"chat":{"id":...}`; (3) add a
  `name: id` line for them to the `CHAT_IDS` repo secret (re-enter every line, since secrets can't be
  viewed); (4) add a `- name:` block for them under `users` in `config.yaml`. People without a chat
  ID are skipped.
- **Channels:** edit `sources` in `config.yaml`. Only public channels with a username work.
- **Smarter matching:** rewrite `matches()` in `filters.py`. Nothing else needs to change.
- **Time:** edit the `cron` line in `.github/workflows/digest.yml` (it's in UTC, so 8:07 AM SGT is `7 0 * * *`).

## How it works

| File | Does |
| --- | --- |
| `reader.py` | Downloads `t.me/s/<channel>` pages and parses posts, paging back with `?before=` |
| `filters.py` | `matches(post, criteria)`: levels, subjects, postal prefix or town, exclusions |
| `digest.py` | For each channel, takes posts above the stored ID, filters, sends the digest, then saves `state.json` |
| `state.json` | Highest message ID handled per channel, committed back by the workflow |

The first time a channel is seen, the last 24 hours of its posts are included. State is saved only
after the digest is sent, so a failed run repeats posts next time but never skips them.

Run the tests with `pip install pytest -r requirements.txt && pytest`.
