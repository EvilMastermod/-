import os
import logging
import time
from urllib.parse import quote
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestUsers,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

CONTACT_BUTTON = "📩 Связь"
ANON_BUTTON = "🕵️ Анон"
CANCEL_BUTTON = "❌ Отменить"
CHOOSE_USER_BUTTON = "👤 Выбрать получателя"

main_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton(CONTACT_BUTTON), KeyboardButton(ANON_BUTTON)]],
    resize_keyboard=True,
)

cancel_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton(CANCEL_BUTTON)]],
    resize_keyboard=True,
)

anon_recipient_keyboard = ReplyKeyboardMarkup(
    [
        [
            KeyboardButton(
                CHOOSE_USER_BUTTON,
                request_users=KeyboardButtonRequestUsers(
                    request_id=777,
                    user_is_bot=False,
                    max_quantity=1,
                    request_name=True,
                    request_username=True,
                ),
            )
        ],
        [KeyboardButton(CANCEL_BUTTON)],
    ],
    resize_keyboard=True,
)

def get_waiting_map(application: Application):
    return application.bot_data.setdefault("waiting_replies", {})

def clear_modes(context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_for_message"] = False
    context.user_data.pop("anon_stage", None)
    context.user_data.pop("anon_recipient_id", None)
    context.user_data.pop("anon_recipient_name", None)

async def post_init(application: Application):
    try:
        await application.bot.send_message(
            chat_id=ADMIN_ID,
            text="🤖 Бот подключен и готов принимать сообщения."
        )
    except Exception:
        logging.exception("Не удалось отправить уведомление о запуске")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    clear_modes(context)

    if context.args and context.args[0] == "anon":
        await update.message.reply_text(
            "✅ Готово. Теперь вам можно отправлять анонимные сообщения через этого бота.",
            reply_markup=main_keyboard,
        )
        return

    await update.message.reply_text(
        "Привет! 👋\n\nВыберите действие.",
        reply_markup=main_keyboard,
    )

async def show_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            f"Твой Telegram ID: {update.effective_user.id}"
        )

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    context.user_data["waiting_for_message"] = True

    await update.message.reply_text(
        "✍️ Отправьте сообщение",
        reply_markup=cancel_keyboard,
    )

async def anon_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    context.user_data["anon_stage"] = "choose"

    await update.message.reply_text(
        "🕵️ Выберите получателя анонимного сообщения.",
        reply_markup=anon_recipient_keyboard,
    )

async def cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)

    await update.message.reply_text(
        "❌ Отправка отменена.",
        reply_markup=main_keyboard,
    )

async def handle_users_shared(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.users_shared:
        return

    if context.user_data.get("anon_stage") != "choose":
        await update.message.reply_text(
            "Сначала нажмите «🕵️ Анон».",
            reply_markup=main_keyboard,
        )
        return

    shared = update.message.users_shared.users
    if not shared:
        await update.message.reply_text(
            "❌ Получатель не выбран.",
            reply_markup=anon_recipient_keyboard,
        )
        return

    target = shared[0]
    context.user_data["anon_recipient_id"] = target.user_id
    context.user_data["anon_stage"] = "message"

    target_name = target.first_name or "пользователя"
    if target.username:
        target_name = f"@{target.username}"
    context.user_data["anon_recipient_name"] = target_name

    await update.message.reply_text(
        f"✍️ Напишите анонимное сообщение для {target_name}",
        reply_markup=cancel_keyboard,
    )

async def send_anonymous(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    target_id = context.user_data.get("anon_recipient_id")
    if not target_id:
        clear_modes(context)
        await update.message.reply_text(
            "❌ Получатель не выбран. Нажмите «🕵️ Анон» ещё раз.",
            reply_markup=main_keyboard,
        )
        return

    now = time.monotonic()
    last_sent = context.user_data.get("anon_last_sent", 0.0)
    if now - last_sent < 5:
        await update.message.reply_text(
            "⏳ Подождите несколько секунд перед следующим анонимным сообщением.",
            reply_markup=main_keyboard,
        )
        return

    sender = update.effective_user
    sender_username = f"@{sender.username}" if sender.username else "нет username"

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"📨 Анонимное сообщение\n\n{text}",
        )

        # Получатель не видит отправителя. Этот лог видит только владелец бота.
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "🛡 Анонимное сообщение отправлено\n\n"
                    f"Отправитель: {sender.full_name}\n"
                    f"Username: {sender_username}\n"
                    f"ID: {sender.id}\n"
                    f"Получатель ID: {target_id}\n\n"
                    f"Текст:\n{text}"
                ),
            )
        except Exception:
            logging.exception("Не удалось отправить админ-лог анонимного сообщения")

        context.user_data["anon_last_sent"] = now
        clear_modes(context)

        await update.message.reply_text(
            "✅ Анонимное сообщение отправлено",
            reply_markup=main_keyboard,
        )

    except Exception:
        logging.exception("Не удалось отправить анонимное сообщение")

        try:
            me = await context.bot.get_me()
            bot_link = f"https://t.me/{me.username}?start=anon"
            share_url = (
                "https://t.me/share/url?url="
                + quote(bot_link, safe="")
                + "&text="
                + quote("Открой RNMD Bot и нажми Start, чтобы получать сообщения.", safe="")
            )

            invite_keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("📨 Отправить ссылку получателю", url=share_url)]]
            )

            clear_modes(context)

            await update.message.reply_text(
                "Получатель ещё не подключил бота. Отправь ему ссылку:",
                reply_markup=invite_keyboard,
            )
            await update.message.reply_text(
                "Главное меню:",
                reply_markup=main_keyboard,
            )
        except Exception:
            logging.exception("Не удалось создать ссылку-приглашение")
            clear_modes(context)
            await update.message.reply_text(
                "❌ Не удалось отправить сообщение",
                reply_markup=main_keyboard,
            )

async def no_answer_job(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    admin_message_id = data["admin_message_id"]
    user_id = data["user_id"]

    waiting = get_waiting_map(context.application)
    ticket = waiting.get(admin_message_id)

    if not ticket or ticket.get("answered"):
        return

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="⏳ Собеседник оповещён. Ожидайте ответа."
        )
        ticket["reminder_sent"] = True
    except Exception:
        logging.exception("Не удалось отправить автооповещение пользователю")

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text or ""

    if text == CONTACT_BUTTON:
        await contact(update, context)
        return

    if text == ANON_BUTTON:
        await anon_start(update, context)
        return

    if text == CANCEL_BUTTON:
        await cancel_action(update, context)
        return

    if context.user_data.get("anon_stage") == "choose":
        await update.message.reply_text(
            "👤 Нажмите «Выбрать получателя» или «❌ Отменить».",
            reply_markup=anon_recipient_keyboard,
        )
        return

    if context.user_data.get("anon_stage") == "message":
        await send_anonymous(update, context, text)
        return

    # Обычная связь. Если Railway перезапустился между нажатием «Связь»
    # и сообщением, текст всё равно будет доставлен владельцу.
    user = update.effective_user
    username = f"@{user.username}" if user.username else "нет username"

    admin_text = (
        "📨 Новое сообщение\n\n"
        f"👤 Имя: {user.full_name}\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: {user.id}\n\n"
        f"💬 Сообщение:\n{text}\n\n"
        "↩️ Ответь на ЭТО сообщение, чтобы ответ ушёл пользователю."
    )

    try:
        sent = await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
        )

        waiting = get_waiting_map(context.application)
        waiting[sent.message_id] = {
            "user_id": user.id,
            "answered": False,
            "reminder_sent": False,
        }

        context.job_queue.run_once(
            no_answer_job,
            when=300,
            data={
                "admin_message_id": sent.message_id,
                "user_id": user.id,
            },
            name=f"no_answer_{sent.message_id}",
        )

        context.user_data["waiting_for_message"] = False

        await update.message.reply_text(
            "✅ Сообщение отправлено",
            reply_markup=main_keyboard,
        )

    except Exception:
        logging.exception("Не удалось отправить сообщение владельцу")
        await update.message.reply_text(
            "❌ Не получилось отправить сообщение. Попробуй позже.",
            reply_markup=main_keyboard,
        )

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or update.effective_user.id != ADMIN_ID:
        return

    reply = update.message.reply_to_message
    if not reply:
        return

    waiting = get_waiting_map(context.application)
    ticket = waiting.get(reply.message_id)

    if not ticket:
        return

    answer_text = update.message.text
    if not answer_text:
        await update.message.reply_text(
            "⚠️ Пока можно отправлять пользователю только текстовый ответ."
        )
        return

    try:
        await context.bot.send_message(
            chat_id=ticket["user_id"],
            text=f"💬 Ответ:\n{answer_text}"
        )

        ticket["answered"] = True

        job_name = f"no_answer_{reply.message_id}"
        for job in context.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()

        await update.message.reply_text("✅ Ответ отправлен пользователю.")
        waiting.pop(reply.message_id, None)

    except Exception:
        logging.exception("Не удалось отправить ответ пользователю")
        await update.message.reply_text("❌ Не удалось отправить ответ.")

def main():
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", show_id))

    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.USERS_SHARED,
            handle_users_shared,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.User(user_id=ADMIN_ID) & filters.REPLY & filters.TEXT,
            handle_admin_reply,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_user_message,
        )
    )

    print("Бот запущен...")
    app.run_polling(drop_pending_updates=False)

if __name__ == "__main__":
    main()
