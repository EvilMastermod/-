import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
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
CANCEL_BUTTON = "❌ Отменить"
main_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton(CONTACT_BUTTON)]],
    resize_keyboard=True,
)

cancel_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton(CANCEL_BUTTON)]],
    resize_keyboard=True,
)

def get_waiting_map(application: Application):
    return application.bot_data.setdefault("waiting_replies", {})

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

    context.user_data["waiting_for_message"] = False

    await update.message.reply_text(
        "Привет! 👋\n\nНажми «📩 Связь», чтобы написать владельцу бота.",
        reply_markup=main_keyboard,
    )

async def show_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            f"Твой Telegram ID: {update.effective_user.id}"
        )

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_for_message"] = True

    await update.message.reply_text(
        "✍️ Отправьте сообщение",
        reply_markup=cancel_keyboard,
    )

async def cancel_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_for_message"] = False

    await update.message.reply_text(
        "❌ Отправка отменена.",
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

    if text == CANCEL_BUTTON:
        await cancel_contact(update, context)
        return

    if not context.user_data.get("waiting_for_message"):
        await update.message.reply_text(
            "Нажми кнопку «📩 Связь», чтобы написать владельцу.",
            reply_markup=main_keyboard,
        )
        return

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
            "\u2063",
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
