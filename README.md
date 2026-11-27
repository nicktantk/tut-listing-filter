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
   - `CHAT_ID`: the number from step 3
5. **Test it.** Actions tab → *Daily tuition digest* → **Run workflow**. You should get a DM within a minute.

After that it runs every day at 8 AM Singapore time. Neither secret expires.

## Changing what you get

- **Criteria:** edit `criteria` in `config.yaml`. The next run uses it.
- **Channels:** edit `sources` in `config.yaml`. Only public channels with a username work.
- **Smarter matching:** rewrite `matches()` in `filters.py`. Nothing else needs to change.
- **Time:** edit the `cron` line in `.github/workflows/digest.yml` (it's in UTC, so 8 AM SGT is `0 0 * * *`).

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
