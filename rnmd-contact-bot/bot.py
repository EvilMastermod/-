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
    CallbackQueryHandler,
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
DND_BUTTON = "🔕 Не беспокоить"
DND_OFF_BUTTON = "🔔 Отключить не беспокоить"
ADMIN_DND_OFF_BUTTON = "🛡 Снять DND у пользователя"
ADMIN_ANON_BAN_BUTTON = "🚫 Бан анона"
ADMIN_ANON_UNBAN_BUTTON = "🟢 Отключить бан анона"
ADMIN_REPORT_LIST_BUTTON = "📋 Лист жалоб"
MINECRAFT_BUTTON = "⛏ Minecraft"
SPOOKY_BUTTON = "👻 Spooky Time"
BACK_BUTTON = "⬅️ Назад"
CANCEL_BUTTON = "❌ Отменить"
CHOOSE_USER_BUTTON = "👤 Выбрать получателя"

user_main_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton(CONTACT_BUTTON), KeyboardButton(ANON_BUTTON)],
        [KeyboardButton(DND_BUTTON), KeyboardButton(DND_OFF_BUTTON)],
        [KeyboardButton(MINECRAFT_BUTTON), KeyboardButton(SPOOKY_BUTTON)],
    ],
    resize_keyboard=True,
)

admin_main_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton(CONTACT_BUTTON), KeyboardButton(ANON_BUTTON)],
        [KeyboardButton(DND_BUTTON), KeyboardButton(DND_OFF_BUTTON)],
        [KeyboardButton(MINECRAFT_BUTTON), KeyboardButton(SPOOKY_BUTTON)],
        [KeyboardButton(ADMIN_DND_OFF_BUTTON), KeyboardButton(ADMIN_ANON_BAN_BUTTON)],
        [KeyboardButton(ADMIN_ANON_UNBAN_BUTTON), KeyboardButton(ADMIN_REPORT_LIST_BUTTON)],
    ],
    resize_keyboard=True,
)

def get_main_keyboard(user_id: int):
    return admin_main_keyboard if user_id == ADMIN_ID else user_main_keyboard

section_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton(BACK_BUTTON)]],
    resize_keyboard=True,
)

admin_anon_unban_keyboard = ReplyKeyboardMarkup(
    [
        [
            KeyboardButton(
                "👤 Выбрать пользователя для разбана",
                request_users=KeyboardButtonRequestUsers(
                    request_id=780,
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

admin_anon_ban_keyboard = ReplyKeyboardMarkup(
    [
        [
            KeyboardButton(
                "👤 Выбрать пользователя для бана",
                request_users=KeyboardButtonRequestUsers(
                    request_id=779,
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

admin_dnd_keyboard = ReplyKeyboardMarkup(
    [
        [
            KeyboardButton(
                "👤 Выбрать пользователя",
                request_users=KeyboardButtonRequestUsers(
                    request_id=778,
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

def get_anon_reply_map(application: Application):
    return application.bot_data.setdefault("anon_reply_routes", {})

def get_anon_reports(application: Application):
    return application.bot_data.setdefault("anon_reports", set())

def get_report_history(application: Application):
    return application.bot_data.setdefault("anon_report_history", [])

def get_dnd_map(application: Application):
    return application.bot_data.setdefault("dnd_states", {})

def get_anon_ban_map(application: Application):
    return application.bot_data.setdefault("anon_bans", {})

def get_anon_ban_remaining(application: Application, user_id: int):
    banned_until = get_anon_ban_map(application).get(user_id, 0)
    now = time.time()
    if banned_until > now:
        return int(banned_until - now)

    get_anon_ban_map(application).pop(user_id, None)
    return 0

def get_dnd_status(application: Application, user_id: int):
    state = get_dnd_map(application).get(user_id)
    if not state:
        return "available", 0

    now = time.time()
    active_until = state.get("active_until", 0)
    cooldown_until = state.get("cooldown_until", 0)

    if now < active_until:
        return "active", int(active_until - now)

    if now < cooldown_until:
        return "cooldown", int(cooldown_until - now)

    get_dnd_map(application).pop(user_id, None)
    return "available", 0

def minutes_left(seconds: int):
    return max(1, (seconds + 59) // 60)

def anon_message_keyboard():
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("💬 Ответить анонимно", callback_data="anon_reply"),
            InlineKeyboardButton("⚠️ Жалоба", callback_data="anon_report"),
        ]]
    )

def clear_modes(context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_for_message"] = False
    context.user_data.pop("anon_stage", None)
    context.user_data.pop("anon_recipient_id", None)
    context.user_data.pop("anon_recipient_name", None)
    context.user_data.pop("anon_reply_target_id", None)
    context.user_data.pop("admin_dnd_stage", None)
    context.user_data.pop("admin_anon_ban_stage", None)
    context.user_data.pop("admin_anon_ban_target_id", None)
    context.user_data.pop("admin_anon_unban_stage", None)

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
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    await update.message.reply_text(
        "Привет! 👋\n\nВыберите действие.",
        reply_markup=get_main_keyboard(update.effective_user.id),
    )

async def minecraft_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    await update.message.reply_text(
        "⛏ Minecraft\n\nРаздел Minecraft.",
        reply_markup=section_keyboard,
    )

async def spooky_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    await update.message.reply_text(
        "👻 Spooky Time\n\nРаздел Spooky Time.",
        reply_markup=section_keyboard,
    )

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    await update.message.reply_text(
        "Главное меню:",
        reply_markup=get_main_keyboard(update.effective_user.id),
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
    remaining = get_anon_ban_remaining(context.application, update.effective_user.id)
    if remaining:
        await update.message.reply_text(
            f"🚫 Вам временно запрещено отправлять анонимные сообщения. Осталось примерно {minutes_left(remaining)} мин.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

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
        reply_markup=get_main_keyboard(update.effective_user.id),
    )

async def dnd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    status, remaining = get_dnd_status(context.application, user_id)

    if status == "active":
        await update.message.reply_text(
            f"🔕 Режим уже включён. Осталось примерно {minutes_left(remaining)} мин.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    if status == "cooldown":
        await update.message.reply_text(
            f"⏳ Перезарядка режима. Осталось примерно {minutes_left(remaining)} мин.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("15 мин", callback_data="dnd_15"),
                InlineKeyboardButton("30 мин", callback_data="dnd_30"),
                InlineKeyboardButton("1 час", callback_data="dnd_60"),
            ]
        ]
    )

    await update.message.reply_text(
        "🔕 На сколько включить «Не беспокоить»?\n\nМаксимум — 1 час. После окончания перезарядка 30 минут.",
        reply_markup=keyboard,
    )

async def dnd_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    status, remaining = get_dnd_status(context.application, user_id)

    if status == "active":
        now = time.time()
        get_dnd_map(context.application)[user_id] = {
            "active_until": 0,
            "cooldown_until": now + 30 * 60,
        }
        await update.message.reply_text(
            "🔔 «Не беспокоить» отключён. Перезарядка — 30 минут.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    if status == "cooldown":
        await update.message.reply_text(
            f"🔔 Режим уже выключен. Перезарядка ещё примерно {minutes_left(remaining)} мин.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    await update.message.reply_text(
        "🔔 «Не беспокоить» уже выключен.",
        reply_markup=get_main_keyboard(update.effective_user.id),
    )

async def admin_dnd_off_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(
            "⛔ Эта кнопка доступна только администратору.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    clear_modes(context)
    context.user_data["admin_dnd_stage"] = True

    await update.message.reply_text(
        "🛡 Выберите пользователя, у которого нужно снять «Не беспокоить».",
        reply_markup=admin_dnd_keyboard,
    )

async def admin_remove_dnd_for_user(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    if update.effective_user.id != ADMIN_ID:
        return

    get_dnd_map(context.application).pop(target_id, None)
    clear_modes(context)

    await update.message.reply_text(
        f"✅ «Не беспокоить» у пользователя {target_id} отключён без перезарядки.",
        reply_markup=get_main_keyboard(update.effective_user.id),
    )

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text="🔔 Администратор отключил у вас режим «Не беспокоить»."
        )
    except Exception:
        logging.exception("Не удалось уведомить пользователя об отключении DND")

async def admin_anon_unban_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(
            "⛔ Эта кнопка доступна только администратору.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    clear_modes(context)
    context.user_data["admin_anon_unban_stage"] = True

    await update.message.reply_text(
        "🟢 Выберите пользователя, у которого нужно отключить бан анона.",
        reply_markup=admin_anon_unban_keyboard,
    )

async def admin_remove_anon_ban(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    if update.effective_user.id != ADMIN_ID:
        return

    was_banned = target_id in get_anon_ban_map(context.application)
    get_anon_ban_map(context.application).pop(target_id, None)
    clear_modes(context)

    if was_banned:
        text = f"✅ Бан анона у пользователя {target_id} отключён."
    else:
        text = f"ℹ️ У пользователя {target_id} активного бана анона нет."

    await update.message.reply_text(
        text,
        reply_markup=get_main_keyboard(update.effective_user.id),
    )

    if was_banned:
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text="🟢 Администратор отключил ваш бан на анонимные сообщения."
            )
        except Exception:
            logging.exception("Не удалось уведомить пользователя о снятии анонимного бана")

async def admin_report_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(
            "⛔ Эта кнопка доступна только администратору.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    history = get_report_history(context.application)
    if not history:
        await update.message.reply_text(
            "📋 Жалоб пока нет.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    lines = ["📋 Последние жалобы:"]
    for i, item in enumerate(reversed(history[-10:]), 1):
        msg = item["text"].replace("\n", " ")
        if len(msg) > 180:
            msg = msg[:177] + "..."
        lines.append(
            f"\n{i}. Отправитель ID: {item['sender_id']}\n"
            f"Получатель ID: {item['recipient_id']}\n"
            f"Сообщение: {msg}"
        )

    await update.message.reply_text(
        "".join(lines),
        reply_markup=get_main_keyboard(update.effective_user.id),
    )

async def admin_anon_ban_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(
            "⛔ Эта кнопка доступна только администратору.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    clear_modes(context)
    context.user_data["admin_anon_ban_stage"] = True

    await update.message.reply_text(
        "🚫 Выберите пользователя, которому нужно запретить анонимные сообщения.",
        reply_markup=admin_anon_ban_keyboard,
    )

async def admin_choose_anon_ban_duration(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    if update.effective_user.id != ADMIN_ID:
        return

    context.user_data["admin_anon_ban_stage"] = False
    context.user_data["admin_anon_ban_target_id"] = target_id

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("15 мин", callback_data="admin_anon_ban_15"),
                InlineKeyboardButton("20 мин", callback_data="admin_anon_ban_20"),
                InlineKeyboardButton("25 мин", callback_data="admin_anon_ban_25"),
            ],
            [
                InlineKeyboardButton("30 мин", callback_data="admin_anon_ban_30"),
                InlineKeyboardButton("1 час", callback_data="admin_anon_ban_60"),
            ],
        ]
    )

    await update.message.reply_text(
        f"🚫 На сколько забанить анонимки пользователю {target_id}?",
        reply_markup=keyboard,
    )

async def apply_anon_ban(application: Application, target_id: int, minutes: int):
    minutes = min(max(minutes, 1), 60)
    get_anon_ban_map(application)[target_id] = time.time() + minutes * 60
    return minutes

async def handle_admin_anon_ban_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or query.from_user.id != ADMIN_ID:
        if query:
            await query.answer("⛔ Только для администратора.", show_alert=True)
        return

    target_id = context.user_data.get("admin_anon_ban_target_id")
    if not target_id:
        await query.answer("Сначала выберите пользователя.", show_alert=True)
        return

    try:
        minutes = int(query.data.rsplit("_", 1)[1])
    except Exception:
        await query.answer("Ошибка.", show_alert=True)
        return

    minutes = await apply_anon_ban(context.application, target_id, minutes)
    clear_modes(context)

    await query.answer("Пользователь забанен.")
    await query.edit_message_text(
        f"🚫 Пользователю {target_id} запрещены анонимные сообщения на {minutes} мин."
    )

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"🚫 Администратор временно запретил вам анонимные сообщения на {minutes} мин."
        )
    except Exception:
        logging.exception("Не удалось уведомить пользователя об анонимном бане")

async def handle_report_ban_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or query.from_user.id != ADMIN_ID:
        if query:
            await query.answer("⛔ Только для администратора.", show_alert=True)
        return

    try:
        _, _, target_id_raw, minutes_raw = query.data.split(":")
        target_id = int(target_id_raw)
        minutes = int(minutes_raw)
    except Exception:
        await query.answer("Ошибка данных.", show_alert=True)
        return

    minutes = await apply_anon_ban(context.application, target_id, minutes)
    await query.answer(f"Бан на {minutes} мин. применён.", show_alert=True)

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"🚫 Администратор временно запретил вам анонимные сообщения на {minutes} мин."
        )
    except Exception:
        logging.exception("Не удалось уведомить пользователя об анонимном бане")

async def handle_dnd_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    try:
        minutes = int(query.data.split("_", 1)[1])
    except Exception:
        await query.answer("Ошибка", show_alert=True)
        return

    minutes = min(max(minutes, 1), 60)
    user_id = query.from_user.id

    status, remaining = get_dnd_status(context.application, user_id)
    if status == "active":
        await query.answer(
            f"Уже включено. Осталось примерно {minutes_left(remaining)} мин.",
            show_alert=True,
        )
        return

    if status == "cooldown":
        await query.answer(
            f"Перезарядка. Осталось примерно {minutes_left(remaining)} мин.",
            show_alert=True,
        )
        return

    now = time.time()
    active_until = now + minutes * 60
    get_dnd_map(context.application)[user_id] = {
        "active_until": active_until,
        "cooldown_until": active_until + 30 * 60,
    }

    await query.answer("Включено")
    await query.edit_message_text(
        f"🔕 «Не беспокоить» включён на {minutes} мин.\nПосле окончания будет перезарядка 30 минут."
    )

async def handle_users_shared(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.users_shared:
        return

    shared = update.message.users_shared.users

    if context.user_data.get("admin_dnd_stage"):
        if update.effective_user.id != ADMIN_ID:
            clear_modes(context)
            return
        if not shared:
            await update.message.reply_text(
                "❌ Пользователь не выбран.",
                reply_markup=admin_dnd_keyboard,
            )
            return
        await admin_remove_dnd_for_user(update, context, shared[0].user_id)
        return

    if context.user_data.get("admin_anon_ban_stage"):
        if update.effective_user.id != ADMIN_ID:
            clear_modes(context)
            return
        if not shared:
            await update.message.reply_text(
                "❌ Пользователь не выбран.",
                reply_markup=admin_anon_ban_keyboard,
            )
            return
        await admin_choose_anon_ban_duration(update, context, shared[0].user_id)
        return

    if context.user_data.get("admin_anon_unban_stage"):
        if update.effective_user.id != ADMIN_ID:
            clear_modes(context)
            return
        if not shared:
            await update.message.reply_text(
                "❌ Пользователь не выбран.",
                reply_markup=admin_anon_unban_keyboard,
            )
            return
        await admin_remove_anon_ban(update, context, shared[0].user_id)
        return

    if context.user_data.get("anon_stage") != "choose":
        await update.message.reply_text(
            "Сначала нажмите «🕵️ Анон».",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return
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
    ban_remaining = get_anon_ban_remaining(context.application, update.effective_user.id)
    if ban_remaining:
        clear_modes(context)
        await update.message.reply_text(
            f"🚫 Вам временно запрещено отправлять анонимные сообщения. Осталось примерно {minutes_left(ban_remaining)} мин.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    target_id = context.user_data.get("anon_recipient_id")
    if not target_id:
        clear_modes(context)
        await update.message.reply_text(
            "❌ Получатель не выбран. Нажмите «🕵️ Анон» ещё раз.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    dnd_status, dnd_remaining = get_dnd_status(context.application, target_id)
    if dnd_status == "active":
        clear_modes(context)
        await update.message.reply_text(
            f"🔕 Получатель сейчас не принимает анонимные сообщения. Осталось примерно {minutes_left(dnd_remaining)} мин.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    now = time.monotonic()
    last_sent = context.user_data.get("anon_last_sent", 0.0)
    if now - last_sent < 5:
        await update.message.reply_text(
            "⏳ Подождите несколько секунд перед следующим анонимным сообщением.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    try:
        reply_keyboard = anon_message_keyboard()
        sent = await context.bot.send_message(
            chat_id=target_id,
            text=f"📨 Анонимное сообщение\n\n{text}",
            reply_markup=reply_keyboard,
        )

        reply_routes = get_anon_reply_map(context.application)
        reply_routes[f"{target_id}:{sent.message_id}"] = update.effective_user.id

        context.user_data["anon_last_sent"] = now
        clear_modes(context)

        await update.message.reply_text(
            "✅ Анонимное сообщение отправлено",
            reply_markup=get_main_keyboard(update.effective_user.id),
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
                reply_markup=get_main_keyboard(update.effective_user.id),
            )
        except Exception:
            logging.exception("Не удалось создать ссылку-приглашение")
            clear_modes(context)
            await update.message.reply_text(
                "❌ Не удалось отправить сообщение",
                reply_markup=get_main_keyboard(update.effective_user.id),
            )

async def handle_anon_reply_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.message:
        return

    ban_remaining = get_anon_ban_remaining(context.application, query.from_user.id)
    if ban_remaining:
        await query.answer(
            f"🚫 Анонимные ответы заблокированы ещё примерно на {minutes_left(ban_remaining)} мин.",
            show_alert=True,
        )
        return

    await query.answer()

    route_key = f"{query.message.chat_id}:{query.message.message_id}"
    target_id = get_anon_reply_map(context.application).get(route_key)

    if not target_id:
        await query.message.reply_text(
            "❌ На это сообщение уже нельзя ответить.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    clear_modes(context)
    context.user_data["anon_reply_target_id"] = target_id

    await query.message.reply_text(
        "✍️ Напишите анонимный ответ",
        reply_markup=cancel_keyboard,
    )

async def handle_anon_report_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.message:
        return

    route_key = f"{query.message.chat_id}:{query.message.message_id}"
    sender_id = get_anon_reply_map(context.application).get(route_key)

    if not sender_id:
        await query.answer("На это сообщение уже нельзя пожаловаться.", show_alert=True)
        return

    reports = get_anon_reports(context.application)
    if route_key in reports:
        await query.answer("Жалоба уже отправлена.", show_alert=True)
        return

    reports.add(route_key)

    try:
        ban_keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🚫 15м", callback_data=f"report:ban:{sender_id}:15"),
                    InlineKeyboardButton("20м", callback_data=f"report:ban:{sender_id}:20"),
                    InlineKeyboardButton("25м", callback_data=f"report:ban:{sender_id}:25"),
                ],
                [
                    InlineKeyboardButton("30м", callback_data=f"report:ban:{sender_id}:30"),
                    InlineKeyboardButton("1ч", callback_data=f"report:ban:{sender_id}:60"),
                ],
            ]
        )

        report_text = query.message.text or "(без текста)"
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "⚠️ Жалоба на анонимное сообщение\n\n"
                f"ID отправителя: {sender_id}\n"
                f"ID получателя: {query.from_user.id}\n\n"
                f"Сообщение:\n{report_text}"
            ),
            reply_markup=ban_keyboard,
        )

        history = get_report_history(context.application)
        history.append({
            "sender_id": sender_id,
            "recipient_id": query.from_user.id,
            "text": report_text,
            "created_at": time.time(),
        })
        if len(history) > 100:
            del history[:-100]

        await query.answer("✅ Жалоба отправлена.", show_alert=True)
    except Exception:
        reports.discard(route_key)
        logging.exception("Не удалось отправить жалобу")
        await query.answer("❌ Не удалось отправить жалобу.", show_alert=True)

async def send_anonymous_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    ban_remaining = get_anon_ban_remaining(context.application, update.effective_user.id)
    if ban_remaining:
        clear_modes(context)
        await update.message.reply_text(
            f"🚫 Вам временно запрещены анонимные ответы. Осталось примерно {minutes_left(ban_remaining)} мин.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    target_id = context.user_data.get("anon_reply_target_id")
    if not target_id:
        clear_modes(context)
        await update.message.reply_text(
            "❌ Не удалось найти получателя ответа.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    dnd_status, dnd_remaining = get_dnd_status(context.application, target_id)
    if dnd_status == "active":
        clear_modes(context)
        await update.message.reply_text(
            f"🔕 Получатель сейчас не принимает анонимные сообщения. Осталось примерно {minutes_left(dnd_remaining)} мин.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    now = time.monotonic()
    last_sent = context.user_data.get("anon_last_sent", 0.0)
    if now - last_sent < 5:
        await update.message.reply_text(
            "⏳ Подождите несколько секунд перед следующим анонимным сообщением.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    try:
        reply_keyboard = anon_message_keyboard()
        sent = await context.bot.send_message(
            chat_id=target_id,
            text=f"💬 Анонимный ответ\n\n{text}",
            reply_markup=reply_keyboard,
        )

        reply_routes = get_anon_reply_map(context.application)
        reply_routes[f"{target_id}:{sent.message_id}"] = update.effective_user.id

        context.user_data["anon_last_sent"] = now
        clear_modes(context)

        await update.message.reply_text(
            "✅ Анонимный ответ отправлен",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )

    except Exception:
        logging.exception("Не удалось отправить анонимный ответ")
        clear_modes(context)
        await update.message.reply_text(
            "❌ Не удалось отправить анонимный ответ",
            reply_markup=get_main_keyboard(update.effective_user.id),
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

    if text == DND_BUTTON:
        await dnd_menu(update, context)
        return

    if text == DND_OFF_BUTTON:
        await dnd_off(update, context)
        return

    if text == MINECRAFT_BUTTON:
        await minecraft_section(update, context)
        return

    if text == SPOOKY_BUTTON:
        await spooky_section(update, context)
        return

    if text == BACK_BUTTON:
        await back_to_main(update, context)
        return

    if text == ADMIN_DND_OFF_BUTTON:
        await admin_dnd_off_start(update, context)
        return

    if text == ADMIN_ANON_BAN_BUTTON:
        await admin_anon_ban_start(update, context)
        return

    if text == ADMIN_ANON_UNBAN_BUTTON:
        await admin_anon_unban_start(update, context)
        return

    if text == ADMIN_REPORT_LIST_BUTTON:
        await admin_report_list(update, context)
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

    if context.user_data.get("anon_reply_target_id"):
        await send_anonymous_reply(update, context, text)
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
            reply_markup=get_main_keyboard(update.effective_user.id),
        )

    except Exception:
        logging.exception("Не удалось отправить сообщение владельцу")
        await update.message.reply_text(
            "❌ Не получилось отправить сообщение. Попробуй позже.",
            reply_markup=get_main_keyboard(update.effective_user.id),
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
    app.add_handler(CallbackQueryHandler(handle_anon_reply_button, pattern="^anon_reply$"))
    app.add_handler(CallbackQueryHandler(handle_anon_report_button, pattern="^anon_report$"))
    app.add_handler(CallbackQueryHandler(handle_dnd_callback, pattern="^dnd_(15|30|60)$"))
    app.add_handler(CallbackQueryHandler(handle_admin_anon_ban_callback, pattern="^admin_anon_ban_(15|20|25|30|60)$"))
    app.add_handler(CallbackQueryHandler(handle_report_ban_callback, pattern=r"^report:ban:-?\d+:(15|20|25|30|60)$"))

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
