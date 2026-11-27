# Tuition listing filter

Once a day, reads new posts from public Singapore tuition channels on Telegram, keeps the ones that
match `config.yaml`, and has a bot DM you one digest with a link to each post.

No server, no database and no Telegram login: posts are read from each channel's public web preview
(`https://t.me/s/<channel>`), and the last message ID read per channel is kept in `state.json`.
