import logging
import os
import re
import sqlite3
import time as time_module
from collections import defaultdict, deque
from datetime import time, datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import (
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import (
    Application,
    BusinessConnectionHandler,
    BusinessMessagesDeletedHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("chat-automator")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
DB_PATH = os.environ.get("DB_PATH", "/data/chat-automator.sqlite")
TZ_NAME = os.environ.get("TZ", "Europe/Kyiv")
TZ = ZoneInfo(TZ_NAME)

URL_RE = re.compile(r"(https?://|t\.me/|www\.|discord\.gg/)", re.I)
FLOOD = defaultdict(lambda: deque(maxlen=30))


def db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS chats(
                chat_id INTEGER PRIMARY KEY,
                welcome_enabled INTEGER NOT NULL DEFAULT 1,
                welcome_text TEXT NOT NULL DEFAULT '👋 Добро пожаловать, {name}!',
                anti_spam INTEGER NOT NULL DEFAULT 1,
                anti_links INTEGER NOT NULL DEFAULT 0,
                bad_words_enabled INTEGER NOT NULL DEFAULT 1,
                warn_limit INTEGER NOT NULL DEFAULT 3,
                clean_service INTEGER NOT NULL DEFAULT 0,
                rules TEXT NOT NULL DEFAULT 'Правила пока не настроены.',
                flood_count INTEGER NOT NULL DEFAULT 6,
                flood_window INTEGER NOT NULL DEFAULT 10,
                flood_mute INTEGER NOT NULL DEFAULT 60
            );

            CREATE TABLE IF NOT EXISTS bad_words(
                chat_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                PRIMARY KEY(chat_id, word)
            );

            CREATE TABLE IF NOT EXISTS auto_replies(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                trigger TEXT NOT NULL,
                reply TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS warnings(
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(chat_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS schedules(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                hh INTEGER NOT NULL,
                mm INTEGER NOT NULL,
                text TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS business_connections(
                connection_id TEXT PRIMARY KEY,
                owner_user_id INTEGER NOT NULL,
                user_chat_id INTEGER NOT NULL,
                is_enabled INTEGER NOT NULL DEFAULT 1,
                can_reply INTEGER NOT NULL DEFAULT 0,
                can_read INTEGER NOT NULL DEFAULT 0,
                can_delete_sent INTEGER NOT NULL DEFAULT 0,
                can_delete_all INTEGER NOT NULL DEFAULT 0,
                updated_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS business_settings(
                owner_user_id INTEGER PRIMARY KEY,
                automation_enabled INTEGER NOT NULL DEFAULT 1,
                fallback_enabled INTEGER NOT NULL DEFAULT 0,
                fallback_text TEXT NOT NULL DEFAULT '👋 Спасибо за сообщение! Я скоро отвечу.',
                welcome_enabled INTEGER NOT NULL DEFAULT 1,
                welcome_text TEXT NOT NULL DEFAULT '👋 Привет, {name}! Спасибо за сообщение.',
                mark_read INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS business_replies(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_user_id INTEGER NOT NULL,
                trigger TEXT NOT NULL,
                reply TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS business_seen_chats(
                owner_user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                first_seen_at INTEGER NOT NULL,
                PRIMARY KEY(owner_user_id, chat_id)
            );

            CREATE TABLE IF NOT EXISTS business_muted_chats(
                owner_user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                muted_at INTEGER NOT NULL,
                PRIMARY KEY(owner_user_id, chat_id)
            );

            CREATE TABLE IF NOT EXISTS business_message_archive(
                connection_id TEXT NOT NULL,
                owner_user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                sender_user_id INTEGER,
                sender_name TEXT,
                text_content TEXT,
                media_type TEXT,
                file_id TEXT,
                created_at INTEGER NOT NULL,
                PRIMARY KEY(connection_id, chat_id, message_id)
            );
            """
        )
        for statement in [
            "ALTER TABLE chats ADD COLUMN clean_service INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE chats ADD COLUMN rules TEXT NOT NULL DEFAULT 'Правила пока не настроены.'",
            "ALTER TABLE chats ADD COLUMN flood_count INTEGER NOT NULL DEFAULT 6",
            "ALTER TABLE chats ADD COLUMN flood_window INTEGER NOT NULL DEFAULT 10",
            "ALTER TABLE chats ADD COLUMN flood_mute INTEGER NOT NULL DEFAULT 60",
            "ALTER TABLE business_connections ADD COLUMN can_read INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE business_connections ADD COLUMN can_delete_sent INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE business_connections ADD COLUMN can_delete_all INTEGER NOT NULL DEFAULT 0",
        ]:
            try:
                c.execute(statement)
            except sqlite3.OperationalError:
                pass


def ensure_chat(chat_id: int):
    with db() as c:
        c.execute("INSERT OR IGNORE INTO chats(chat_id) VALUES(?)", (chat_id,))


def get_chat(chat_id: int):
    ensure_chat(chat_id)
    with db() as c:
        return c.execute("SELECT * FROM chats WHERE chat_id=?", (chat_id,)).fetchone()


def set_chat(chat_id: int, field: str, value):
    allowed = {
        "welcome_enabled",
        "welcome_text",
        "anti_spam",
        "anti_links",
        "bad_words_enabled",
        "warn_limit",
        "clean_service",
        "rules",
        "flood_count",
        "flood_window",
        "flood_mute",
    }
    if field not in allowed:
        raise ValueError("bad field")
    ensure_chat(chat_id)
    with db() as c:
        c.execute(f"UPDATE chats SET {field}=? WHERE chat_id=?", (value, chat_id))


def ensure_business_settings(owner_user_id: int):
    with db() as c:
        c.execute(
            "INSERT OR IGNORE INTO business_settings(owner_user_id) VALUES(?)",
            (owner_user_id,),
        )


def get_business_settings(owner_user_id: int):
    ensure_business_settings(owner_user_id)
    with db() as c:
        return c.execute(
            "SELECT * FROM business_settings WHERE owner_user_id=?",
            (owner_user_id,),
        ).fetchone()


def set_business_setting(owner_user_id: int, field: str, value):
    allowed = {
        "automation_enabled",
        "fallback_enabled",
        "fallback_text",
        "welcome_enabled",
        "welcome_text",
        "mark_read",
    }
    if field not in allowed:
        raise ValueError("bad business field")
    ensure_business_settings(owner_user_id)
    with db() as c:
        c.execute(
            f"UPDATE business_settings SET {field}=? WHERE owner_user_id=?",
            (value, owner_user_id),
        )


def get_business_connection(connection_id: str):
    with db() as c:
        return c.execute(
            "SELECT * FROM business_connections WHERE connection_id=?",
            (connection_id,),
        ).fetchone()


def owner_business_connection(owner_user_id: int):
    with db() as c:
        return c.execute(
            """
            SELECT * FROM business_connections
            WHERE owner_user_id=?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (owner_user_id,),
        ).fetchone()


def business_panel(owner_user_id: int):
    s = get_business_settings(owner_user_id)
    connection = owner_business_connection(owner_user_id)
    connected = bool(connection and connection["is_enabled"])
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{'✅' if connected else '❌'} Подключение Telegram Business",
                    callback_data="biz:status",
                )
            ],
            [
                InlineKeyboardButton(
                    f"{'✅' if s['automation_enabled'] else '❌'} Автоматизация",
                    callback_data="biz:automation",
                ),
                InlineKeyboardButton(
                    f"{'✅' if s['fallback_enabled'] else '❌'} Общий автоответ",
                    callback_data="biz:fallback",
                ),
            ],
            [
                InlineKeyboardButton(
                    f"{'✅' if s['welcome_enabled'] else '❌'} Первое сообщение",
                    callback_data="biz:welcome",
                ),
                InlineKeyboardButton(
                    f"{'✅' if s['mark_read'] else '❌'} Читать сообщения",
                    callback_data="biz:read",
                ),
            ],
            [
                InlineKeyboardButton("🗯 Ответы по словам", callback_data="biz:replies"),
                InlineKeyboardButton("📝 Тексты автоответов", callback_data="biz:texts"),
            ],
        ]
    )


def business_chat_is_muted(owner_user_id: int, chat_id: int) -> bool:
    with db() as c:
        return c.execute(
            "SELECT 1 FROM business_muted_chats WHERE owner_user_id=? AND chat_id=?",
            (owner_user_id, chat_id),
        ).fetchone() is not None


def set_business_chat_muted(owner_user_id: int, chat_id: int, muted: bool):
    with db() as c:
        if muted:
            c.execute(
                """
                INSERT INTO business_muted_chats(owner_user_id,chat_id,muted_at)
                VALUES(?,?,?)
                ON CONFLICT(owner_user_id,chat_id) DO UPDATE SET muted_at=excluded.muted_at
                """,
                (owner_user_id, chat_id, int(time_module.time())),
            )
        else:
            c.execute(
                "DELETE FROM business_muted_chats WHERE owner_user_id=? AND chat_id=?",
                (owner_user_id, chat_id),
            )


def business_message_payload(msg):
    text_content = (msg.text or msg.caption or "").strip()
    media_type = None
    file_id = None

    if msg.photo:
        media_type = "photo"
        file_id = msg.photo[-1].file_id
    elif msg.video:
        media_type = "video"
        file_id = msg.video.file_id
    elif msg.document:
        media_type = "document"
        file_id = msg.document.file_id
        if not text_content and msg.document.file_name:
            text_content = msg.document.file_name
    elif msg.voice:
        media_type = "voice"
        file_id = msg.voice.file_id
    elif msg.audio:
        media_type = "audio"
        file_id = msg.audio.file_id
    elif msg.animation:
        media_type = "animation"
        file_id = msg.animation.file_id
    elif msg.sticker:
        media_type = "sticker"
        file_id = msg.sticker.file_id
        if not text_content:
            text_content = msg.sticker.emoji or "стикер"
    elif msg.video_note:
        media_type = "video_note"
        file_id = msg.video_note.file_id

    return text_content, media_type, file_id


def archive_business_message(connection_id: str, owner_user_id: int, msg):
    text_content, media_type, file_id = business_message_payload(msg)
    sender = msg.from_user
    with db() as c:
        c.execute(
            """
            INSERT OR REPLACE INTO business_message_archive(
                connection_id,owner_user_id,chat_id,message_id,
                sender_user_id,sender_name,text_content,media_type,file_id,created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                connection_id,
                owner_user_id,
                msg.chat_id,
                msg.message_id,
                sender.id if sender else None,
                sender.full_name if sender else None,
                text_content,
                media_type,
                file_id,
                int(time_module.time()),
            ),
        )


async def send_deleted_archive(context: ContextTypes.DEFAULT_TYPE, owner_chat_id: int, row):
    sender = row["sender_name"] or (
        f"ID {row['sender_user_id']}" if row["sender_user_id"] else "Неизвестный"
    )
    body = row["text_content"] or ""
    header = (
        "🗑 Удалено сообщение\n"
        f"👤 {sender}\n"
        f"💬 Chat ID: {row['chat_id']}\n"
        f"🆔 Message ID: {row['message_id']}\n"
    )

    media_type = row["media_type"]
    file_id = row["file_id"]
    caption = (header + (f"\n📝 {body}" if body else ""))[:1024]

    try:
        if media_type == "photo" and file_id:
            await context.bot.send_photo(owner_chat_id, file_id, caption=caption)
        elif media_type == "video" and file_id:
            await context.bot.send_video(owner_chat_id, file_id, caption=caption)
        elif media_type == "document" and file_id:
            await context.bot.send_document(owner_chat_id, file_id, caption=caption)
        elif media_type == "voice" and file_id:
            await context.bot.send_voice(owner_chat_id, file_id, caption=caption)
        elif media_type == "audio" and file_id:
            await context.bot.send_audio(owner_chat_id, file_id, caption=caption)
        elif media_type == "animation" and file_id:
            await context.bot.send_animation(owner_chat_id, file_id, caption=caption)
        elif media_type == "sticker" and file_id:
            await context.bot.send_message(owner_chat_id, header + (f"\n📝 {body}" if body else ""))
            await context.bot.send_sticker(owner_chat_id, file_id)
        elif media_type == "video_note" and file_id:
            await context.bot.send_message(owner_chat_id, header + (f"\n📝 {body}" if body else ""))
            await context.bot.send_video_note(owner_chat_id, file_id)
        else:
            await context.bot.send_message(
                owner_chat_id,
                (header + (f"\n📝 {body}" if body else "\n📝 [без текста]"))[:4000],
            )
    except Exception:
        log.exception("Failed to send deleted message archive")


async def is_admin(update: Update, user_id: int | None = None) -> bool:
    chat = update.effective_chat
    if not chat or chat.type == "private":
        return False
    uid = user_id or update.effective_user.id
    try:
        member = await chat.get_member(uid)
        return member.status in {
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        }
    except Exception:
        return False


async def require_admin(update: Update) -> bool:
    if not await is_admin(update):
        if update.callback_query:
            await update.callback_query.answer("⛔ Только для админов.", show_alert=True)
        elif update.effective_message:
            await update.effective_message.reply_text("⛔ Эта команда только для админов чата.")
        return False
    return True


def panel(chat_id: int):
    s = get_chat(chat_id)
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{'✅' if s['welcome_enabled'] else '❌'} Приветствие",
                    callback_data="cfg:welcome",
                ),
                InlineKeyboardButton(
                    f"{'✅' if s['anti_spam'] else '❌'} Антиспам",
                    callback_data="cfg:spam",
                ),
            ],
            [
                InlineKeyboardButton(
                    f"{'✅' if s['anti_links'] else '❌'} Антиссылки",
                    callback_data="cfg:links",
                ),
                InlineKeyboardButton(
                    f"{'✅' if s['bad_words_enabled'] else '❌'} Фильтр слов",
                    callback_data="cfg:words",
                ),
            ],
            [
                InlineKeyboardButton("🗯 Автоответы", callback_data="cfg:replies"),
                InlineKeyboardButton("⏰ Расписание", callback_data="cfg:schedules"),
            ],
            [
                InlineKeyboardButton(
                    f"{'✅' if s['clean_service'] else '❌'} Чистить сервис",
                    callback_data="cfg:clean",
                ),
                InlineKeyboardButton("📋 Правила", callback_data="cfg:rules"),
            ],
            [
                InlineKeyboardButton("⚠️ Лимит предупреждений", callback_data="cfg:warnlimit"),
            ],
        ]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "🤖 Я RNMD Chat Automator.\n\n"
            "Я могу работать как Telegram Business-бот: получать сообщения "
            "из выбранных личных чатов и отвечать от твоего имени.\n\n"
            "Настройки Business: /business\n"
            "Настройки групп: /setup"
        )
    else:
        await update.message.reply_text("🤖 Готов. Админ-панель: /setup")


async def business_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        await update.effective_message.reply_text("⚠️ Открой эту команду в личном чате с ботом.")
        return
    owner_id = update.effective_user.id
    ensure_business_settings(owner_id)
    connection = owner_business_connection(owner_id)
    status = "✅ подключён" if connection and connection["is_enabled"] else "❌ ещё не подключён"
    await update.effective_message.reply_text(
        "💼 Автоматизация личных чатов\n\n"
        f"Telegram Business: {status}\n\n"
        "Чаты, к которым бот получает доступ, выбираются прямо в Telegram "
        "на экране «Автоматизация чатов».\n\n"
        "Команды прямо в личном чате:\n"
        "• .mute — удалять новые сообщения собеседника\n"
        "• .unmute — снять мут\n\n"
        "Удалённые собеседником сообщения бот автоматически сохраняет "
        "и присылает тебе в личный чат с ботом.",
        reply_markup=business_panel(owner_id),
    )


async def business_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return
    owner_id = q.from_user.id
    action = q.data.split(":", 1)[1]
    s = get_business_settings(owner_id)

    toggles = {
        "automation": ("automation_enabled", "Автоматизация"),
        "fallback": ("fallback_enabled", "Общий автоответ"),
        "welcome": ("welcome_enabled", "Первое сообщение"),
        "read": ("mark_read", "Пометка прочитанным"),
    }
    if action in toggles:
        field, label = toggles[action]
        value = 0 if s[field] else 1
        set_business_setting(owner_id, field, value)
        await q.answer(f"{label}: {'включено' if value else 'выключено'}")
        await q.edit_message_reply_markup(reply_markup=business_panel(owner_id))
        return

    if action == "status":
        connection = owner_business_connection(owner_id)
        if connection and connection["is_enabled"]:
            text = (
                "✅ Telegram Business подключён.\n"
                f"Право отвечать: {'да' if connection['can_reply'] else 'нет'}.\n\n"
                "Доступные чаты и исключения настраиваются в самом Telegram."
            )
        else:
            text = (
                "❌ Бот пока не получил Business-подключение.\n\n"
                "Если Secretary Mode уже включён и бот уже выбран: "
                "в Telegram открой Настройки → Telegram Business → Автоматизация чатов, "
                "временно отключи этого бота, сохрани, затем подключи его снова и сохрани. "
                "После этого попроси кого-нибудь написать тебе в разрешённый личный чат "
                "и снова открой /business."
            )
        await q.answer()
        await q.message.reply_text(text)
        return

    if action == "replies":
        with db() as c:
            rows = c.execute(
                """
                SELECT id,trigger,reply FROM business_replies
                WHERE owner_user_id=? ORDER BY id DESC LIMIT 30
                """,
                (owner_id,),
            ).fetchall()
        text = "🗯 Ответы по словам\n\n"
        text += "\n".join(
            f"#{r['id']} «{r['trigger']}» → {r['reply']}" for r in rows
        ) or "Пока нет."
        text += (
            "\n\nДобавить: /bizreplyadd привет | Привет! Чем помочь?"
            "\nУдалить: /bizreplydel ID"
        )
        await q.answer()
        await q.message.reply_text(text)
        return

    if action == "texts":
        await q.answer()
        await q.message.reply_text(
            "📝 Тексты Business-автоответов\n\n"
            f"Первое сообщение:\n{s['welcome_text']}\n\n"
            f"Общий автоответ:\n{s['fallback_text']}\n\n"
            "Изменить первое сообщение:\n"
            "/bizwelcome Привет, {name}! Чем помочь?\n\n"
            "Изменить общий автоответ:\n"
            "/bizfallback Спасибо! Я скоро отвечу."
        )


async def business_connection_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bc = update.business_connection
    if not bc:
        return
    can_reply = int(bool(getattr(bc.rights, "can_reply", False))) if bc.rights else 0
    can_read = int(bool(getattr(bc.rights, "can_read_messages", False))) if bc.rights else 0
    can_delete_sent = int(bool(getattr(bc.rights, "can_delete_sent_messages", False))) if bc.rights else 0
    can_delete_all = int(bool(getattr(bc.rights, "can_delete_all_messages", False))) if bc.rights else 0
    with db() as c:
        c.execute(
            """
            INSERT INTO business_connections(
                connection_id,owner_user_id,user_chat_id,is_enabled,
                can_reply,can_read,can_delete_sent,can_delete_all,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?)
            ON CONFLICT(connection_id) DO UPDATE SET
                owner_user_id=excluded.owner_user_id,
                user_chat_id=excluded.user_chat_id,
                is_enabled=excluded.is_enabled,
                can_reply=excluded.can_reply,
                can_read=excluded.can_read,
                can_delete_sent=excluded.can_delete_sent,
                can_delete_all=excluded.can_delete_all,
                updated_at=excluded.updated_at
            """,
            (
                bc.id,
                bc.user.id,
                bc.user_chat_id,
                int(bool(bc.is_enabled)),
                can_reply,
                can_read,
                can_delete_sent,
                can_delete_all,
                int(time_module.time()),
            ),
        )
    ensure_business_settings(bc.user.id)
    try:
        await context.bot.send_message(
            chat_id=bc.user_chat_id,
            text=(
                "✅ Telegram Business подключён к RNMD Chat Automator."
                if bc.is_enabled
                else "⚠️ Telegram Business отключён от RNMD Chat Automator."
            ),
        )
    except Exception:
        log.exception("Could not notify business owner")


async def business_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.business_message
    if not msg or not msg.business_connection_id:
        return

    connection = get_business_connection(msg.business_connection_id)
    if not connection:
        try:
            bc = await context.bot.get_business_connection(msg.business_connection_id)
            can_reply = int(bool(getattr(bc.rights, "can_reply", False))) if bc.rights else 0
            can_read = int(bool(getattr(bc.rights, "can_read_messages", False))) if bc.rights else 0
            can_delete_sent = int(bool(getattr(bc.rights, "can_delete_sent_messages", False))) if bc.rights else 0
            can_delete_all = int(bool(getattr(bc.rights, "can_delete_all_messages", False))) if bc.rights else 0
            with db() as db_conn:
                db_conn.execute(
                    """
                    INSERT INTO business_connections(
                        connection_id,owner_user_id,user_chat_id,is_enabled,
                        can_reply,can_read,can_delete_sent,can_delete_all,updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(connection_id) DO UPDATE SET
                        owner_user_id=excluded.owner_user_id,
                        user_chat_id=excluded.user_chat_id,
                        is_enabled=excluded.is_enabled,
                        can_reply=excluded.can_reply,
                        can_read=excluded.can_read,
                        can_delete_sent=excluded.can_delete_sent,
                        can_delete_all=excluded.can_delete_all,
                        updated_at=excluded.updated_at
                    """,
                    (
                        bc.id,
                        bc.user.id,
                        bc.user_chat_id,
                        int(bool(bc.is_enabled)),
                        can_reply,
                        can_read,
                        can_delete_sent,
                        can_delete_all,
                        int(time_module.time()),
                    ),
                )
            ensure_business_settings(bc.user.id)
            connection = get_business_connection(msg.business_connection_id)
        except Exception:
            log.exception("Could not recover Business connection from incoming message")
            return

    if not connection or not connection["is_enabled"]:
        return

    owner_id = int(connection["owner_user_id"])
    text = (msg.text or msg.caption or "").strip()

    # Commands written by the owner directly inside a managed personal chat.
    if msg.from_user and msg.from_user.id == owner_id:
        low = text.lower()

        if low == ".mute":
            if not connection["can_delete_all"]:
                await msg.reply_text(
                    "❌ Для .мут включи боту право удалять все сообщения в Telegram Business.",
                    do_quote=False,
                )
                return
            set_business_chat_muted(owner_id, msg.chat_id, True)
            try:
                await context.bot.delete_business_messages(
                    business_connection_id=msg.business_connection_id,
                    message_ids=[msg.message_id],
                )
            except Exception:
                pass
            await context.bot.send_message(
                chat_id=msg.chat_id,
                text="🔇 Чат замьючен. Новые сообщения собеседника будут удаляться.",
                business_connection_id=msg.business_connection_id,
            )
            return

        if low == ".unmute":
            set_business_chat_muted(owner_id, msg.chat_id, False)
            try:
                if connection["can_delete_sent"]:
                    await context.bot.delete_business_messages(
                        business_connection_id=msg.business_connection_id,
                        message_ids=[msg.message_id],
                    )
            except Exception:
                pass
            await context.bot.send_message(
                chat_id=msg.chat_id,
                text="🔊 Мут снят.",
                business_connection_id=msg.business_connection_id,
            )
            return

        return

    if getattr(msg, "sender_business_bot", None):
        return

    # Save every incoming Business message before any automation/deletion.
    archive_business_message(msg.business_connection_id, owner_id, msg)

    # .мут works like a local mute: every new incoming message is deleted.
    if business_chat_is_muted(owner_id, msg.chat_id):
        if connection["can_delete_all"]:
            try:
                await context.bot.delete_business_messages(
                    business_connection_id=msg.business_connection_id,
                    message_ids=[msg.message_id],
                )
            except Exception:
                log.exception("Failed to delete muted business message")
        return

    s = get_business_settings(owner_id)
    if not s["automation_enabled"]:
        return

    if s["mark_read"]:
        try:
            await msg.read_business_message()
        except Exception:
            log.debug("Cannot mark business message as read", exc_info=True)

    low = text.lower()
    sender_name = msg.from_user.full_name if msg.from_user else "друг"

    chosen_reply = None
    if text:
        with db() as c:
            rows = c.execute(
                """
                SELECT trigger,reply FROM business_replies
                WHERE owner_user_id=? ORDER BY LENGTH(trigger) DESC,id ASC
                """,
                (owner_id,),
            ).fetchall()
        for row in rows:
            if row["trigger"].lower() in low:
                chosen_reply = row["reply"]
                break

    first_seen = False
    with db() as c:
        existing = c.execute(
            """
            SELECT 1 FROM business_seen_chats
            WHERE owner_user_id=? AND chat_id=?
            """,
            (owner_id, msg.chat_id),
        ).fetchone()
        if not existing:
            first_seen = True
            c.execute(
                """
                INSERT OR IGNORE INTO business_seen_chats(owner_user_id,chat_id,first_seen_at)
                VALUES(?,?,?)
                """,
                (owner_id, msg.chat_id, int(time_module.time())),
            )

    if chosen_reply is None and first_seen and s["welcome_enabled"]:
        chosen_reply = s["welcome_text"]
    elif chosen_reply is None and s["fallback_enabled"]:
        chosen_reply = s["fallback_text"]

    if not chosen_reply:
        return

    chosen_reply = (
        chosen_reply
        .replace("{name}", sender_name)
        .replace("{username}", f"@{msg.from_user.username}" if msg.from_user and msg.from_user.username else "")
    )

    try:
        await msg.reply_text(chosen_reply, do_quote=False)
    except Exception:
        log.exception("Failed to send business reply")


async def deleted_business_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deleted = update.deleted_business_messages
    if not deleted:
        return

    connection = get_business_connection(deleted.business_connection_id)
    if not connection:
        return

    owner_id = int(connection["owner_user_id"])
    owner_chat_id = int(connection["user_chat_id"])

    with db() as c:
        for message_id in deleted.message_ids:
            row = c.execute(
                """
                SELECT * FROM business_message_archive
                WHERE connection_id=? AND chat_id=? AND message_id=?
                """,
                (deleted.business_connection_id, deleted.chat.id, message_id),
            ).fetchone()
            if not row:
                continue

            # Only report messages that came from the other person.
            if row["sender_user_id"] == owner_id:
                continue

            await send_deleted_archive(context, owner_chat_id, row)
            c.execute(
                """
                DELETE FROM business_message_archive
                WHERE connection_id=? AND chat_id=? AND message_id=?
                """,
                (deleted.business_connection_id, deleted.chat.id, message_id),
            )


async def biz_reply_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    raw = update.message.text.partition(" ")[2].strip()
    if "|" not in raw:
        await update.message.reply_text("Пример: /bizreplyadd привет | Привет! Чем помочь?")
        return
    trigger, reply = [x.strip() for x in raw.split("|", 1)]
    if not trigger or not reply:
        await update.message.reply_text("❌ Нужны триггер и ответ.")
        return
    owner_id = update.effective_user.id
    ensure_business_settings(owner_id)
    with db() as c:
        c.execute(
            "INSERT INTO business_replies(owner_user_id,trigger,reply) VALUES(?,?,?)",
            (owner_id, trigger.lower()[:150], reply[:2000]),
        )
    await update.message.reply_text("✅ Business-автоответ добавлен.")


async def biz_reply_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    raw = update.message.text.partition(" ")[2].strip()
    if not raw.isdigit():
        await update.message.reply_text("Пример: /bizreplydel 3")
        return
    with db() as c:
        c.execute(
            "DELETE FROM business_replies WHERE owner_user_id=? AND id=?",
            (update.effective_user.id, int(raw)),
        )
    await update.message.reply_text("✅ Business-автоответ удалён.")


async def biz_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    text = update.message.text.partition(" ")[2].strip()
    if not text:
        await update.message.reply_text("Пример: /bizfallback Спасибо! Я скоро отвечу.")
        return
    set_business_setting(update.effective_user.id, "fallback_text", text[:2000])
    await update.message.reply_text("✅ Общий Business-автоответ сохранён.")


async def biz_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    text = update.message.text.partition(" ")[2].strip()
    if not text:
        await update.message.reply_text("Пример: /bizwelcome Привет, {name}! Чем помочь?")
        return
    set_business_setting(update.effective_user.id, "welcome_text", text[:2000])
    await update.message.reply_text("✅ Приветствие для нового чата сохранено.")


async def setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update):
        return
    ensure_chat(update.effective_chat.id)
    await update.message.reply_text(
        "🛠 Автоматизация чата\n\nВыберите настройку:",
        reply_markup=panel(update.effective_chat.id),
    )


async def config_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return
    if not await require_admin(update):
        return

    chat_id = q.message.chat.id
    action = q.data.split(":", 1)[1]
    s = get_chat(chat_id)

    toggles = {
        "welcome": ("welcome_enabled", "Приветствие"),
        "spam": ("anti_spam", "Антиспам"),
        "links": ("anti_links", "Антиссылки"),
        "words": ("bad_words_enabled", "Фильтр слов"),
        "clean": ("clean_service", "Очистка сервисных сообщений"),
    }
    if action in toggles:
        field, label = toggles[action]
        new_value = 0 if s[field] else 1
        set_chat(chat_id, field, new_value)
        await q.answer(f"{label}: {'включено' if new_value else 'выключено'}")
        await q.edit_message_reply_markup(reply_markup=panel(chat_id))
        return

    if action == "replies":
        with db() as c:
            rows = c.execute(
                "SELECT id, trigger, reply FROM auto_replies WHERE chat_id=? ORDER BY id DESC LIMIT 20",
                (chat_id,),
            ).fetchall()
        text = "🗯 Автоответы\n\n"
        text += "\n".join(f"#{r['id']} «{r['trigger']}» → {r['reply']}" for r in rows) or "Пока нет."
        text += (
            "\n\nДобавить: /replyadd слово | ответ"
            "\nУдалить: /replydel ID"
        )
        await q.answer()
        await q.message.reply_text(text)
        return

    if action == "schedules":
        with db() as c:
            rows = c.execute(
                "SELECT id, hh, mm, text FROM schedules WHERE chat_id=? AND enabled=1 ORDER BY hh,mm",
                (chat_id,),
            ).fetchall()
        text = "⏰ Ежедневные сообщения\n\n"
        text += "\n".join(
            f"#{r['id']} {r['hh']:02d}:{r['mm']:02d} — {r['text']}" for r in rows
        ) or "Пока нет."
        text += (
            f"\n\nЧасовой пояс: {TZ_NAME}"
            "\nДобавить: /schedule 18:30 | Текст сообщения"
            "\nУдалить: /scheduledel ID"
        )
        await q.answer()
        await q.message.reply_text(text)
        return

    if action == "rules":
        await q.answer()
        await q.message.reply_text(
            f"📋 Правила чата:\n\n{s['rules']}\n\nИзменить: /setrules текст правил"
        )
        return

    if action == "warnlimit":
        await q.answer()
        await q.message.reply_text(
            f"⚠️ Сейчас лимит: {s['warn_limit']}\n"
            "Изменить: /warnlimit 3"
        )


async def set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update):
        return
    text = update.message.text.partition(" ")[2].strip()
    if not text:
        await update.message.reply_text(
            "Пример:\n/setwelcome 👋 Привет, {name}! Добро пожаловать в {chat}"
        )
        return
    set_chat(update.effective_chat.id, "welcome_text", text[:1000])
    await update.message.reply_text("✅ Текст приветствия сохранён.")


async def set_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update):
        return
    text = update.message.text.partition(" ")[2].strip()
    if not text:
        await update.message.reply_text("Пример: /setrules Не спамить и уважать участников.")
        return
    set_chat(update.effective_chat.id, "rules", text[:3000])
    await update.message.reply_text("✅ Правила сохранены.")


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return
    s = get_chat(update.effective_chat.id)
    await update.message.reply_text("📋 Правила чата:\n\n" + s["rules"])


async def add_bad_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update):
        return
    word = update.message.text.partition(" ")[2].strip().lower()
    if not word:
        await update.message.reply_text("Пример: /badadd слово")
        return
    with db() as c:
        c.execute(
            "INSERT OR IGNORE INTO bad_words(chat_id,word) VALUES(?,?)",
            (update.effective_chat.id, word[:100]),
        )
    await update.message.reply_text(f"✅ Добавлено в фильтр: {word}")


async def del_bad_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update):
        return
    word = update.message.text.partition(" ")[2].strip().lower()
    if not word:
        await update.message.reply_text("Пример: /baddel слово")
        return
    with db() as c:
        c.execute(
            "DELETE FROM bad_words WHERE chat_id=? AND word=?",
            (update.effective_chat.id, word),
        )
    await update.message.reply_text(f"✅ Удалено из фильтра: {word}")


async def list_bad_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update):
        return
    with db() as c:
        rows = c.execute(
            "SELECT word FROM bad_words WHERE chat_id=? ORDER BY word",
            (update.effective_chat.id,),
        ).fetchall()
    await update.message.reply_text(
        "🚫 Запрещённые слова:\n" + (", ".join(r["word"] for r in rows) or "список пуст")
    )


async def reply_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update):
        return
    raw = update.message.text.partition(" ")[2].strip()
    if "|" not in raw:
        await update.message.reply_text("Пример: /replyadd привет | Привет 👋")
        return
    trigger, reply = [x.strip() for x in raw.split("|", 1)]
    if not trigger or not reply:
        await update.message.reply_text("❌ Нужны триггер и ответ.")
        return
    with db() as c:
        c.execute(
            "INSERT INTO auto_replies(chat_id,trigger,reply) VALUES(?,?,?)",
            (update.effective_chat.id, trigger.lower()[:150], reply[:1000]),
        )
    await update.message.reply_text("✅ Автоответ добавлен.")


async def reply_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update):
        return
    raw = update.message.text.partition(" ")[2].strip()
    if not raw.isdigit():
        await update.message.reply_text("Пример: /replydel 4")
        return
    with db() as c:
        c.execute(
            "DELETE FROM auto_replies WHERE chat_id=? AND id=?",
            (update.effective_chat.id, int(raw)),
        )
    await update.message.reply_text("✅ Автоответ удалён.")


def schedule_job_name(schedule_id: int):
    return f"schedule:{schedule_id}"


async def scheduled_send(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    try:
        await context.bot.send_message(chat_id=data["chat_id"], text=data["text"])
    except Exception:
        log.exception("scheduled send failed")


def add_schedule_job(app: Application, row):
    if not app.job_queue:
        return
    app.job_queue.run_daily(
        scheduled_send,
        time=time(hour=int(row["hh"]), minute=int(row["mm"]), tzinfo=TZ),
        data={"chat_id": int(row["chat_id"]), "text": row["text"]},
        name=schedule_job_name(int(row["id"])),
    )


async def schedule_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update):
        return
    raw = update.message.text.partition(" ")[2].strip()
    if "|" not in raw:
        await update.message.reply_text("Пример: /schedule 18:30 | Добрый вечер!")
        return
    clock, text = [x.strip() for x in raw.split("|", 1)]
    try:
        hh, mm = map(int, clock.split(":"))
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            raise ValueError
    except Exception:
        await update.message.reply_text("❌ Время должно быть HH:MM, например 18:30.")
        return
    if not text:
        await update.message.reply_text("❌ Нужен текст сообщения.")
        return

    with db() as c:
        cur = c.execute(
            "INSERT INTO schedules(chat_id,hh,mm,text,enabled) VALUES(?,?,?,?,1)",
            (update.effective_chat.id, hh, mm, text[:2000]),
        )
        sid = cur.lastrowid
        row = c.execute("SELECT * FROM schedules WHERE id=?", (sid,)).fetchone()

    add_schedule_job(context.application, row)
    await update.message.reply_text(
        f"✅ Добавлено: каждый день в {hh:02d}:{mm:02d} ({TZ_NAME}). ID #{sid}"
    )


async def schedule_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update):
        return
    raw = update.message.text.partition(" ")[2].strip()
    if not raw.isdigit():
        await update.message.reply_text("Пример: /scheduledel 2")
        return
    sid = int(raw)
    with db() as c:
        c.execute(
            "DELETE FROM schedules WHERE chat_id=? AND id=?",
            (update.effective_chat.id, sid),
        )
    if context.job_queue:
        for job in context.job_queue.get_jobs_by_name(schedule_job_name(sid)):
            job.schedule_removal()
    await update.message.reply_text("✅ Расписание удалено.")


async def warn_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update):
        return
    raw = update.message.text.partition(" ")[2].strip()
    if not raw.isdigit() or not (1 <= int(raw) <= 20):
        await update.message.reply_text("Пример: /warnlimit 3")
        return
    set_chat(update.effective_chat.id, "warn_limit", int(raw))
    await update.message.reply_text(f"✅ Лимит предупреждений: {raw}")


async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответь командой /warn на сообщение пользователя.")
        return

    user = update.message.reply_to_message.from_user
    if not user or user.is_bot:
        return
    if await is_admin(update, user.id):
        await update.message.reply_text("❌ Нельзя выдать предупреждение админу.")
        return

    chat_id = update.effective_chat.id
    s = get_chat(chat_id)
    with db() as c:
        c.execute(
            """
            INSERT INTO warnings(chat_id,user_id,count) VALUES(?,?,1)
            ON CONFLICT(chat_id,user_id) DO UPDATE SET count=count+1
            """,
            (chat_id, user.id),
        )
        count = c.execute(
            "SELECT count FROM warnings WHERE chat_id=? AND user_id=?",
            (chat_id, user.id),
        ).fetchone()["count"]

    if count >= s["warn_limit"]:
        try:
            await update.effective_chat.restrict_member(
                user.id,
                permissions=ChatPermissions(can_send_messages=False),
            )
            with db() as c:
                c.execute(
                    "UPDATE warnings SET count=0 WHERE chat_id=? AND user_id=?",
                    (chat_id, user.id),
                )
            await update.message.reply_text(
                f"🔇 {user.mention_html()} получил {count} предупреждений и был замьючен.",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await update.message.reply_text(
                f"⚠️ Предупреждение {count}/{s['warn_limit']}. "
                "Не смог замьютить — проверь права бота."
            )
    else:
        await update.message.reply_text(
            f"⚠️ {user.mention_html()}: {count}/{s['warn_limit']}",
            parse_mode=ParseMode.HTML,
        )


async def unwarn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответь /unwarn на сообщение пользователя.")
        return
    user = update.message.reply_to_message.from_user
    with db() as c:
        c.execute(
            "UPDATE warnings SET count=MAX(0,count-1) WHERE chat_id=? AND user_id=?",
            (update.effective_chat.id, user.id),
        )
    await update.message.reply_text("✅ Одно предупреждение снято.")


def parse_duration(raw: str):
    m = re.fullmatch(r"(\d+)([smhd]?)", (raw or "10m").lower())
    if not m:
        return 600
    n = int(m.group(1))
    return n * {"": 60, "s": 1, "m": 60, "h": 3600, "d": 86400}[m.group(2)]


async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответь /mute 10m на сообщение пользователя.")
        return
    user = update.message.reply_to_message.from_user
    if await is_admin(update, user.id):
        await update.message.reply_text("❌ Нельзя мутить администратора.")
        return
    seconds = parse_duration(context.args[0] if context.args else "10m")
    try:
        until = datetime.now(TZ) + timedelta(seconds=seconds)
        await update.effective_chat.restrict_member(
            user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until,
        )
        await update.message.reply_text(f"🔇 Мут на {seconds} сек.")
    except Exception:
        await update.message.reply_text("❌ Не получилось. Проверь права бота.")


async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответь /unmute на сообщение пользователя.")
        return
    user = update.message.reply_to_message.from_user
    perms = ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
    )
    try:
        await update.effective_chat.restrict_member(user.id, permissions=perms)
        await update.message.reply_text("🔊 Мут снят.")
    except Exception:
        await update.message.reply_text("❌ Не получилось снять мут.")


async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответь /ban на сообщение пользователя.")
        return
    user = update.message.reply_to_message.from_user
    if await is_admin(update, user.id):
        await update.message.reply_text("❌ Нельзя банить администратора.")
        return
    try:
        await update.effective_chat.ban_member(user.id)
        await update.message.reply_text("🚫 Пользователь заблокирован.")
    except Exception:
        await update.message.reply_text("❌ Не получилось заблокировать.")


async def on_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members:
        return
    s = get_chat(update.effective_chat.id)
    if not s["welcome_enabled"]:
        return
    for user in update.message.new_chat_members:
        if user.is_bot and user.id == context.bot.id:
            continue
        text = (
            s["welcome_text"]
            .replace("{name}", user.full_name)
            .replace("{chat}", update.effective_chat.title or "чат")
        )
        await update.message.reply_text(text)

    if s["clean_service"]:
        try:
            await update.message.delete()
        except Exception:
            pass


async def moderate_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not msg or not user or user.is_bot or chat.type == "private":
        return
    if await is_admin(update, user.id):
        return

    s = get_chat(chat.id)
    text = (msg.text or msg.caption or "").strip()
    if not text:
        return

    reason = None

    if s["anti_spam"]:
        key = (chat.id, user.id)
        now = time_module.time()
        bucket = FLOOD[key]
        bucket.append(now)
        while bucket and now - bucket[0] > int(s["flood_window"]):
            bucket.popleft()
        if len(bucket) >= int(s["flood_count"]):
            reason = "слишком много сообщений подряд"
            bucket.clear()
            try:
                until = datetime.now(TZ) + timedelta(seconds=int(s["flood_mute"]))
                await chat.restrict_member(
                    user.id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until,
                )
            except Exception:
                pass

    if not reason and s["anti_links"] and URL_RE.search(text):
        reason = "ссылки запрещены"

    if not reason and s["bad_words_enabled"]:
        low = text.lower()
        with db() as c:
            words = [r["word"] for r in c.execute(
                "SELECT word FROM bad_words WHERE chat_id=?",
                (chat.id,),
            )]
        if any(w in low for w in words):
            reason = "запрещённое слово"

    if reason:
        try:
            await msg.delete()
        except Exception:
            pass
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"🚫 {user.mention_html()}: {reason}.",
            parse_mode=ParseMode.HTML,
        )
        return

    with db() as c:
        replies = c.execute(
            "SELECT trigger,reply FROM auto_replies WHERE chat_id=?",
            (chat.id,),
        ).fetchall()
    low = text.lower()
    for row in replies:
        if row["trigger"] in low:
            await msg.reply_text(row["reply"])
            break


async def restore_jobs(app: Application):
    with db() as c:
        rows = c.execute(
            "SELECT * FROM schedules WHERE enabled=1"
        ).fetchall()
    for row in rows:
        add_schedule_job(app, row)


async def post_init(app: Application):
    await restore_jobs(app)
    log.info("Chat Automator started. timezone=%s", TZ_NAME)


def main():
    if not BOT_TOKEN:
        log.warning("BOT_TOKEN is not set. Service is waiting for the secret.")
        while True:
            time_module.sleep(3600)

    init_db()
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(BusinessConnectionHandler(business_connection_update))
    app.add_handler(BusinessMessagesDeletedHandler(deleted_business_messages))
    app.add_handler(MessageHandler(filters.UpdateType.BUSINESS_MESSAGE, business_message))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("business", business_menu))
    app.add_handler(CommandHandler("bizreplyadd", biz_reply_add))
    app.add_handler(CommandHandler("bizreplydel", biz_reply_del))
    app.add_handler(CommandHandler("bizfallback", biz_fallback))
    app.add_handler(CommandHandler("bizwelcome", biz_welcome))
    app.add_handler(CallbackQueryHandler(business_callback, pattern=r"^biz:"))
    app.add_handler(CommandHandler("setup", setup))
    app.add_handler(CommandHandler("setwelcome", set_welcome))
    app.add_handler(CommandHandler("setrules", set_rules))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("badadd", add_bad_word))
    app.add_handler(CommandHandler("baddel", del_bad_word))
    app.add_handler(CommandHandler("badlist", list_bad_words))
    app.add_handler(CommandHandler("replyadd", reply_add))
    app.add_handler(CommandHandler("replydel", reply_del))
    app.add_handler(CommandHandler("schedule", schedule_add))
    app.add_handler(CommandHandler("scheduledel", schedule_del))
    app.add_handler(CommandHandler("warnlimit", warn_limit))
    app.add_handler(CommandHandler("warn", warn_user))
    app.add_handler(CommandHandler("unwarn", unwarn_user))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CallbackQueryHandler(config_callback, pattern=r"^cfg:"))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_members))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, moderate_message))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
