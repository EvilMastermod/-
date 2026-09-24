# RNMD Chat Automator

Telegram bot for group chat automation.

## Environment variables
- `BOT_TOKEN` — Telegram bot token from BotFather.
- `DB_PATH` — optional SQLite path. Recommended on Railway: `/data/chat-automator.sqlite`.
- `TZ` — optional timezone, default `Europe/Kyiv`.

## Start
```bash
python bot.py
```

## Main commands
- `/setup` — admin panel
- `/setwelcome TEXT`
- `/badadd WORD`, `/baddel WORD`, `/badlist`
- `/replyadd TRIGGER | REPLY`, `/replydel ID`
- `/schedule HH:MM | TEXT`, `/scheduledel ID`
- `/warn`, `/unwarn`, `/warnlimit N`

The bot needs admin rights in the group for deleting messages and muting users.
