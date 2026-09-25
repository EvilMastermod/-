# RNMD Chat Automator for Cloudflare (Business prototype)

This is a separate webhook implementation of the Telegram Business features of
`chat-automator-bot/bot.py`. The existing Railway bot remains the production
version until the D1 data and all other features have been migrated.

Implemented: Telegram Business connection updates, permission status, settings,
first-message and keyword replies, muted-chat deletion and inline controls,
deleted-message archive forwarding, and `.spam N text` (1–10 messages).

Not implemented yet: group moderation, group configuration, warnings, scheduled
messages, and transfer of the Railway SQLite database. Do not switch this bot's
Telegram webhook until those features and the existing data have been reviewed.

## Prepare a Cloudflare account

1. Create a D1 database named `rnmd-chat-automator` in Cloudflare.
2. Copy its database ID to `database_id` in `wrangler.toml`.
3. From this folder, use `npx wrangler d1 execute rnmd-chat-automator --remote --file=schema.sql`
   to create the tables (this is a fresh empty database).
4. Set `BOT_TOKEN` and `WEBHOOK_SECRET` as **Worker secrets**, never commit them.
   Use a new, random `WEBHOOK_SECRET` consisting of letters, numbers, `_`, `-`.
5. Deploy with `npx wrangler deploy`. Only after a tested cutover, stop Railway's
   bot and set the Telegram webhook to `https://<worker>.workers.dev/webhook`
   with the same `secret_token`. `getUpdates` and webhooks cannot run together.

The Worker rejects webhook requests without the matching
`X-Telegram-Bot-Api-Secret-Token`. It keeps update IDs in D1 to avoid repeats
when Telegram retries delivery. The public root URL is a health response.

Review the existing SQLite data and export/import it to D1 before switching.
`BOT_TOKEN` was previously included in old HTTP request logs on Railway, so
rotate it in BotFather before cutover, then update the secret in the chosen host.
