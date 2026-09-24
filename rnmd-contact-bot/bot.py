import os
import re
import logging
import time
import httpx
from types import SimpleNamespace
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
SPOOKY_PRICE_API = os.environ.get(
    "SPOOKY_PRICE_API",
    "https://spooky-auction-bot-production.up.railway.app",
).rstrip("/")
PRICE_API_KEY = os.environ.get("PRICE_API_KEY", "")
SHOP_API_KEY = os.environ.get("SHOP_API_KEY", "")

CONTACT_BUTTON = "📩 Связь"
ANON_BUTTON = "🕵️ Анон"
DND_BUTTON = "🔕 Не беспокоить"
DND_OFF_BUTTON = "🔔 Отключить не беспокоить"
ADMIN_DND_OFF_BUTTON = "🛡 Снять DND у пользователя"
ADMIN_ANON_BAN_BUTTON = "🚫 Бан анона"
ADMIN_ANON_UNBAN_BUTTON = "🟢 Отключить бан анона"
ADMIN_REPORT_LIST_BUTTON = "📋 Лист жалоб"
ADMIN_COINS_BUTTON = "🪙 Выдать коины"
ADMIN_REMOVE_COINS_BUTTON = "➖ Удалить коины"
ADMIN_PANEL_BUTTON = "🛠 Админ панель"
MINECRAFT_BUTTON = "⛏ Minecraft"
SPOOKY_BUTTON = "👻 Spooky Time"
SPOOKY_PRICE_BUTTON = "💰 Средняя цена"
WALLET_BUTTON = "👛 Кошелёк"
SHOP_BUTTON = "🛒 Магазин"
PROFILE_BUTTON = "👤 Профиль"
OTHER_PROFILE_BUTTON = "👥 Профиль другого"
ACTIVITIES_BUTTON = "🎮 Активности"
DAILY_BUTTON = "🎁 Ежедневная награда"
INVENTORY_BUTTON = "🧰 Инвентарь"
TRANSFER_BUTTON = "💸 Перевод"
GIFT_BUTTON = "🎁 Подарок"
PROMO_BUTTON = "🎟 Промокод"
TOP_BUTTON = "🏆 Топ"
LIKE_BUTTON = "❤️ Лайк профиля"
CASE_BUTTON = "🎁 Кейс"
FRIENDS_BUTTON = "🧑‍🤝‍🧑 Друзья"
DIRECT_BUTTON = "💌 Личное сообщение"
ACHIEVEMENTS_BUTTON = "🏅 Достижения"
QUESTS_BUTTON = "🎯 Задания на день"
BANK_BUTTON = "🏦 Банк"
SEASON_BUTTON = "🎫 Сезонный пропуск"
CALENDAR_BUTTON = "📅 Календарь ежедневок"
ROTATION_BUTTON = "🔄 Ротация магазина"
TRADE_BUTTON = "🔁 Обмен украшениями"
SELL_BUTTON = "🗑 Продать украшение"
HISTORY_BUTTON = "📈 История баланса"
NOTIFICATIONS_BUTTON = "🔔 Уведомления"
STATUS_BUTTON = "🪪 Статус профиля"
BUNDLES_BUTTON = "📦 Наборы"
EVENT_BUTTON = "🎉 Ивент"
ADMIN_PROMO_BUTTON = "🎟 Создать промокод"
ADMIN_DAILY_BUTTON = "🎁 Настроить ежедневку"
ADMIN_PROMO_DELETE_BUTTON = "🗑 Удалить промокод"
ADMIN_EXCLUSIVE_BUTTON = "✨ Создать эксклюзив"
ADMIN_TITLE_BUTTON = "🎖 Создать титул"
ADMIN_STATS_BUTTON = "📊 Статистика бота"
ADMIN_LOG_BUTTON = "🧾 История админа"
ADMIN_SHOP_EDIT_BUTTON = "🧰 Редактор магазина"
ADMIN_ECONOMY_BLOCK_BUTTON = "🚫 Блок экономики"
ADMIN_RANDOM_DAILY_BUTTON = "🎲 Случайная ежедневка"
ADMIN_BUNDLE_BUTTON = "📦 Создать набор"
ADMIN_EVENT_BUTTON = "🎉 Настроить ивент"
ADMIN_SEASON_BUTTON = "🎫 Настроить сезон"
ADMIN_QUESTS_BUTTON = "🎯 Редактор заданий"
BACK_BUTTON = "⬅️ Назад"
MINECRAFT_BACK_BUTTON = "⬅️ В Minecraft"
CANCEL_BUTTON = "❌ Отменить"
CHOOSE_USER_BUTTON = "👤 Выбрать получателя"

PROFILE_COLOR_OPTIONS = [
    ("green", "🟢", "Зелёный"),
    ("white", "⚪", "Белый"),
    ("gray", "🩶", "Серый"),
    ("black", "⚫", "Чёрный"),
    ("red", "🔴", "Красный"),
    ("purple", "🟣", "Фиолетовый"),
    ("pink", "🩷", "Розовый"),
    ("dark_green", "🟩", "Тёмно-зелёный"),
    ("light_blue", "🩵", "Голубой"),
    ("blue", "🔵", "Синий"),
]


user_main_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton(CONTACT_BUTTON), KeyboardButton(ANON_BUTTON)],
        [KeyboardButton(DND_BUTTON), KeyboardButton(DND_OFF_BUTTON)],
        [KeyboardButton(MINECRAFT_BUTTON), KeyboardButton(WALLET_BUTTON)],
        [KeyboardButton(SHOP_BUTTON), KeyboardButton(PROFILE_BUTTON)],
        [KeyboardButton(OTHER_PROFILE_BUTTON), KeyboardButton(ACTIVITIES_BUTTON)],
    ],
    resize_keyboard=True,
)

admin_main_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton(CONTACT_BUTTON), KeyboardButton(ANON_BUTTON)],
        [KeyboardButton(DND_BUTTON), KeyboardButton(DND_OFF_BUTTON)],
        [KeyboardButton(MINECRAFT_BUTTON), KeyboardButton(WALLET_BUTTON)],
        [KeyboardButton(SHOP_BUTTON), KeyboardButton(PROFILE_BUTTON)],
        [KeyboardButton(OTHER_PROFILE_BUTTON), KeyboardButton(ACTIVITIES_BUTTON)],
        [KeyboardButton(ADMIN_PANEL_BUTTON)],
    ],
    resize_keyboard=True,
)

def get_main_keyboard(user_id: int):
    return admin_main_keyboard if user_id == ADMIN_ID else user_main_keyboard

admin_panel_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton(ADMIN_DND_OFF_BUTTON), KeyboardButton(ADMIN_ANON_BAN_BUTTON)],
        [KeyboardButton(ADMIN_ANON_UNBAN_BUTTON), KeyboardButton(ADMIN_REPORT_LIST_BUTTON)],
        [KeyboardButton(ADMIN_COINS_BUTTON), KeyboardButton(ADMIN_REMOVE_COINS_BUTTON)],
        [KeyboardButton(ADMIN_PROMO_BUTTON), KeyboardButton(ADMIN_PROMO_DELETE_BUTTON)],
        [KeyboardButton(ADMIN_DAILY_BUTTON), KeyboardButton(ADMIN_EXCLUSIVE_BUTTON)],
        [KeyboardButton(ADMIN_TITLE_BUTTON)],
        [KeyboardButton(ADMIN_STATS_BUTTON), KeyboardButton(ADMIN_LOG_BUTTON)],
        [KeyboardButton(ADMIN_SHOP_EDIT_BUTTON), KeyboardButton(ADMIN_ECONOMY_BLOCK_BUTTON)],
        [KeyboardButton(ADMIN_RANDOM_DAILY_BUTTON), KeyboardButton(ADMIN_BUNDLE_BUTTON)],
        [KeyboardButton(ADMIN_SEASON_BUTTON), KeyboardButton(ADMIN_QUESTS_BUTTON)],
        [KeyboardButton(ADMIN_EVENT_BUTTON)],
        [KeyboardButton(BACK_BUTTON)],
    ],
    resize_keyboard=True,
)

activities_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton(DAILY_BUTTON), KeyboardButton(INVENTORY_BUTTON)],
        [KeyboardButton(FRIENDS_BUTTON), KeyboardButton(DIRECT_BUTTON)],
        [KeyboardButton(ACHIEVEMENTS_BUTTON), KeyboardButton(QUESTS_BUTTON)],
        [KeyboardButton(BANK_BUTTON), KeyboardButton(SEASON_BUTTON)],
        [KeyboardButton(CALENDAR_BUTTON), KeyboardButton(ROTATION_BUTTON)],
        [KeyboardButton(TRANSFER_BUTTON), KeyboardButton(GIFT_BUTTON)],
        [KeyboardButton(TRADE_BUTTON), KeyboardButton(SELL_BUTTON)],
        [KeyboardButton(PROMO_BUTTON), KeyboardButton(BUNDLES_BUTTON)],
        [KeyboardButton(TOP_BUTTON), KeyboardButton(LIKE_BUTTON)],
        [KeyboardButton(HISTORY_BUTTON), KeyboardButton(NOTIFICATIONS_BUTTON)],
        [KeyboardButton(STATUS_BUTTON), KeyboardButton(EVENT_BUTTON)],
        [KeyboardButton(CASE_BUTTON)],
        [KeyboardButton(BACK_BUTTON)],
    ],
    resize_keyboard=True,
)

other_profile_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton(
        "👤 Выбрать профиль пользователя",
        request_users=KeyboardButtonRequestUsers(
            request_id=786,
            user_is_bot=False,
            max_quantity=1,
            request_name=True,
            request_username=True,
        ),
    )], [KeyboardButton(CANCEL_BUTTON)]],
    resize_keyboard=True,
)

friends_user_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton(
        "👤 Добавить/удалить друга",
        request_users=KeyboardButtonRequestUsers(
            request_id=787, user_is_bot=False, max_quantity=1,
            request_name=True, request_username=True,
        ),
    )], [KeyboardButton(BACK_BUTTON)]],
    resize_keyboard=True,
)

direct_user_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton(
        "👤 Выбрать получателя сообщения",
        request_users=KeyboardButtonRequestUsers(
            request_id=788, user_is_bot=False, max_quantity=1,
            request_name=True, request_username=True,
        ),
    )], [KeyboardButton(CANCEL_BUTTON)]],
    resize_keyboard=True,
)

trade_user_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton(
        "👤 Выбрать пользователя для обмена",
        request_users=KeyboardButtonRequestUsers(
            request_id=789, user_is_bot=False, max_quantity=1,
            request_name=True, request_username=True,
        ),
    )], [KeyboardButton(CANCEL_BUTTON)]],
    resize_keyboard=True,
)

admin_economy_user_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton(
        "👤 Выбрать пользователя для блокировки экономики",
        request_users=KeyboardButtonRequestUsers(
            request_id=790, user_is_bot=False, max_quantity=1,
            request_name=True, request_username=True,
        ),
    )], [KeyboardButton(CANCEL_BUTTON)]],
    resize_keyboard=True,
)

transfer_user_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton(
        "👤 Выбрать получателя перевода",
        request_users=KeyboardButtonRequestUsers(
            request_id=782, user_is_bot=False, max_quantity=1,
            request_name=True, request_username=True,
        ),
    )], [KeyboardButton(CANCEL_BUTTON)]],
    resize_keyboard=True,
)

gift_user_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton(
        "👤 Выбрать получателя подарка",
        request_users=KeyboardButtonRequestUsers(
            request_id=783, user_is_bot=False, max_quantity=1,
            request_name=True, request_username=True,
        ),
    )], [KeyboardButton(CANCEL_BUTTON)]],
    resize_keyboard=True,
)

like_user_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton(
        "👤 Выбрать профиль для лайка",
        request_users=KeyboardButtonRequestUsers(
            request_id=784, user_is_bot=False, max_quantity=1,
            request_name=True, request_username=True,
        ),
    )], [KeyboardButton(CANCEL_BUTTON)]],
    resize_keyboard=True,
)

minecraft_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton(SPOOKY_BUTTON)],
        [KeyboardButton(BACK_BUTTON)],
    ],
    resize_keyboard=True,
)

spooky_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton(SPOOKY_PRICE_BUTTON)],
        [KeyboardButton(MINECRAFT_BACK_BUTTON)],
    ],
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

admin_coins_keyboard = ReplyKeyboardMarkup(
    [
        [
            KeyboardButton(
                "👤 Выбрать пользователя для коинов",
                request_users=KeyboardButtonRequestUsers(
                    request_id=781,
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

admin_remove_coins_keyboard = ReplyKeyboardMarkup(
    [
        [
            KeyboardButton(
                "👤 Выбрать пользователя для удаления коинов",
                request_users=KeyboardButtonRequestUsers(
                    request_id=785,
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
    context.user_data.pop("admin_coins_stage", None)
    context.user_data.pop("admin_coins_target_id", None)
    context.user_data.pop("admin_remove_coins_stage", None)
    context.user_data.pop("admin_remove_coins_target_id", None)
    context.user_data.pop("transfer_stage", None)
    context.user_data.pop("transfer_target_id", None)
    context.user_data.pop("gift_stage", None)
    context.user_data.pop("gift_target_id", None)
    context.user_data.pop("like_stage", None)
    context.user_data.pop("other_profile_stage", None)
    context.user_data.pop("friends_stage", None)
    context.user_data.pop("direct_stage", None)
    context.user_data.pop("direct_target_id", None)
    context.user_data.pop("trade_stage", None)
    context.user_data.pop("trade_target_id", None)
    context.user_data.pop("trade_give_item", None)
    context.user_data.pop("bank_stage", None)
    context.user_data.pop("status_waiting", None)
    context.user_data.pop("admin_shop_edit_waiting", None)
    context.user_data.pop("admin_economy_stage", None)
    context.user_data.pop("admin_random_daily_waiting", None)
    context.user_data.pop("admin_bundle_waiting", None)
    context.user_data.pop("admin_event_waiting", None)
    context.user_data.pop("admin_season_waiting", None)
    context.user_data.pop("admin_quests_waiting", None)
    context.user_data.pop("promo_waiting", None)
    context.user_data.pop("admin_promo_waiting", None)
    context.user_data.pop("admin_daily_waiting", None)
    context.user_data.pop("admin_exclusive_waiting", None)
    context.user_data.pop("admin_title_waiting", None)
    context.user_data.pop("spooky_price_waiting", None)

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

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(
            "⛔ Эта кнопка доступна только администратору.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    clear_modes(context)
    await update.message.reply_text(
        "🛠 Админ панель\n\nВыберите действие:",
        reply_markup=admin_panel_keyboard,
    )


async def minecraft_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    await update.message.reply_text(
        "⛏ Minecraft\n\nВыберите раздел:",
        reply_markup=minecraft_keyboard,
    )

async def spooky_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    await update.message.reply_text(
        "👻 Spooky Time\n\nРаздел Spooky Time.",
        reply_markup=spooky_keyboard,
    )

async def show_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)

    headers = {}
    if PRICE_API_KEY:
        headers["x-api-key"] = PRICE_API_KEY

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(
                f"{SPOOKY_PRICE_API}/wallet",
                json={"userId": update.effective_user.id},
                headers=headers,
            )

        data = response.json()
        if response.status_code != 200 or not data.get("ok"):
            error_text = data.get("error") or f"HTTP {response.status_code}"
            await update.message.reply_text(
                f"❌ Не удалось открыть кошелёк: {error_text}",
                reply_markup=get_main_keyboard(update.effective_user.id),
            )
            return

        balance = int(data.get("balance") or 0)
        purchases = data.get("purchases") or []
        purchase_labels = {
            "plus": "Plus",
            "premium": "Premium",
            "name_color": "🎨 Цвет ника",
            "crown": "👑 Корона",
            "star_badge": "⭐ Значок",
            "profile_frame": "🖼 Рамка профиля",
            "message_style": "💬 Стиль сообщений",
            "random_item": "🎁 Случайный предмет",
            "rnmd_badge": "🔥 RNMD",
            "diamond_badge": "💎 Алмазный значок",
            "sakura_badge": "🌸 Sakura-значок",
            "trophy": "🏆 Трофей",
            "premium_gold_frame": "👑 Premium-рамка",
            "premium_star": "🌟 Premium-звезда",
            "autumn_frame": "🍂 Осенняя рамка",
            "pumpkin_badge": "🎃 Тыквенный значок",
        }
        purchase_names = [
            purchase_labels[item_id]
            for item_id in purchases
            if item_id in purchase_labels
        ]

        purchases_text = ""
        if purchase_names:
            purchases_text = "\n🎁 Куплено: " + ", ".join(purchase_names)

        await update.message.reply_text(
            "👛 Кошелёк\n\n"
            f"🪙 Random Coins: {balance:,}".replace(",", " ")
            + purchases_text,
            reply_markup=get_main_keyboard(update.effective_user.id),
        )

    except Exception:
        logging.exception("Ошибка кошелька")
        await update.message.reply_text(
            "❌ Кошелёк сейчас недоступен. Попробуйте чуть позже.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )


def shop_headers():
    headers = {}
    if SHOP_API_KEY:
        headers["x-shop-key"] = SHOP_API_KEY
    return headers


def shop_item_button(item):
    item_id = item.get("id")
    name = item.get("name")
    price = int(item.get("price") or 0)
    owned = bool(item.get("owned"))

    rarity_labels = {
        "common": "⚪",
        "rare": "🔵",
        "epic": "🟣",
        "legendary": "🟡",
        "exclusive": "🔴",
    }
    rarity = rarity_labels.get(item.get("rarity"), "")
    rotation = " 🔄" if item.get("rotating") else ""

    if owned:
        text = f"✅ {rarity} {name} — куплено{rotation}".strip()
        callback = "shop_owned"
    else:
        lock = " 🔒Premium" if item.get("locked") else ""
        limited = " ⏳" if item.get("availableUntil") else ""
        text = f"Купить {rarity} {name} — {price:,} RC{lock}{limited}{rotation}".replace(",", " ").strip()
        callback = f"shop_buy:{item_id}"

    return InlineKeyboardButton(text, callback_data=callback)


def shop_keyboard(items):
    main_items = [item for item in items if item.get("category") == "main"]
    rows = [
        [InlineKeyboardButton("✨ Украшения", callback_data="shop_items")],
        [InlineKeyboardButton("🎖 Титулы", callback_data="shop_titles")],
        [InlineKeyboardButton("📦 Наборы", callback_data="shop_bundles")],
    ]

    for item in main_items:
        rows.append([shop_item_button(item)])

    return InlineKeyboardMarkup(rows)


def shop_items_keyboard(items):
    collectible_items = [item for item in items if item.get("category") == "items"]
    rows = [[shop_item_button(item)] for item in collectible_items]
    rows.append([InlineKeyboardButton("⬅️ Назад в магазин", callback_data="shop_back")])
    return InlineKeyboardMarkup(rows)

def shop_titles_keyboard(items):
    title_items = [item for item in items if item.get("category") == "titles"]
    rows = [[shop_item_button(item)] for item in title_items]
    rows.append([InlineKeyboardButton("⬅️ Назад в магазин", callback_data="shop_back")])
    return InlineKeyboardMarkup(rows)



async def fetch_shop(user_id: int):
    async with httpx.AsyncClient(timeout=12.0) as client:
        response = await client.post(
            f"{SPOOKY_PRICE_API}/shop",
            json={"userId": user_id},
            headers=shop_headers(),
        )
    data = response.json()
    return response, data


async def fetch_profile(user_id: int):
    async with httpx.AsyncClient(timeout=12.0) as client:
        response = await client.post(
            f"{SPOOKY_PRICE_API}/profile",
            json={"userId": user_id},
            headers=shop_headers(),
        )

    try:
        data = response.json()
    except Exception:
        data = {}

    if response.status_code == 200 and data.get("ok"):
        return response, data

    # Fallback: старый сервер ещё может не иметь /profile.
    # Тогда строим профиль прямо из уже работающего /shop.
    shop_response, shop_data = await fetch_shop(user_id)
    if shop_response.status_code != 200 or not shop_data.get("ok"):
        return response, data

    items = shop_data.get("items") or []
    cosmetics = []
    plus = False
    premium = False
    purchases = []

    for item in items:
        if item.get("owned"):
            item_id = item.get("id")
            purchases.append(item_id)
            if item_id == "plus":
                plus = True
            elif item_id == "premium":
                premium = True
            elif item.get("category") == "items":
                cosmetics.append({**item, "equipped": True})

    fallback = {
        "ok": True,
        "userId": str(user_id),
        "balance": int(shop_data.get("balance") or 0),
        "plus": plus,
        "premium": premium,
        "purchases": purchases,
        "cosmetics": cosmetics,
        "nameColor": "white",
        "availableColors": [
            {"id": color_id, "name": color_name}
            for color_id, _emoji, color_name in PROFILE_COLOR_OPTIONS
        ],
        "fallback": True,
    }
    return shop_response, fallback


def equipped_cosmetic_ids(data):
    return {
        item.get("id")
        for item in (data.get("cosmetics") or [])
        if item.get("equipped")
    }


def profile_color_meta(color_id):
    for option_id, emoji, name in PROFILE_COLOR_OPTIONS:
        if option_id == color_id:
            return emoji, name
    return "⚪", "Белый"


def profile_has_cosmetic(data, item_id):
    return any(
        item.get("id") == item_id
        for item in (data.get("cosmetics") or [])
    )


def profile_display_name(user, data):
    name = user.full_name or "Пользователь"
    equipped = equipped_cosmetic_ids(data)

    if "name_color" in equipped:
        color_emoji, _color_name = profile_color_meta(data.get("nameColor") or "white")
        name = f"{color_emoji} {name} {color_emoji}"
    if "crown" in equipped:
        name = f"👑 {name}"

    suffixes = []
    if "star_badge" in equipped:
        suffixes.append("⭐")
    if "rnmd_badge" in equipped:
        suffixes.append("🔥RNMD")
    if "diamond_badge" in equipped:
        suffixes.append("💎")
    if "sakura_badge" in equipped:
        suffixes.append("🌸")
    if "premium_star" in equipped:
        suffixes.append("🌟")
    if "pumpkin_badge" in equipped:
        suffixes.append("🎃")
    if "trophy" in equipped:
        suffixes.append("🏆")
    if "random_item" in equipped:
        suffixes.append("🎁")

    for item in data.get("cosmetics") or []:
        if item.get("customExclusive") and item.get("equipped"):
            suffixes.append(item.get("name") or "✨ Эксклюзив")

    if suffixes:
        name += " " + " ".join(suffixes)

    title = data.get("title")
    if title:
        name += f" · [{title}]"

    background_id = data.get("selectedBackground")
    if background_id == "bg_night":
        name = f"🌌 {name} 🌌"
    elif background_id == "bg_sakura":
        name = f"🌸 {name} 🌸"
    elif background_id == "bg_gold":
        name = f"👑 {name} 👑"
    elif background_id:
        bg = next((x for x in (data.get("cosmetics") or []) if x.get("id") == background_id), None)
        if bg:
            name = f"🖼 {name} · {bg.get('name')}"

    if "premium_gold_frame" in equipped:
        name = f"╔══ 👑 PREMIUM 👑 ══╗\n{name}\n╚══════════════════╝"
    elif "autumn_frame" in equipped:
        name = f"╔══ 🍂 ══╗\n{name}\n╚══ 🍂 ══╝"
    elif "profile_frame" in equipped:
        name = f"╔══ ✦ ══╗\n{name}\n╚══ ✦ ══╝"

    return name


def profile_text(user, data):
    balance = int(data.get("balance") or 0)
    status = "Premium" if data.get("premium") else ("Plus" if data.get("plus") else "Обычный")
    cosmetics = data.get("cosmetics") or []
    equipped_count = sum(1 for item in cosmetics if item.get("equipped"))
    username = f"@{user.username}" if user.username else "нет username"

    lines = [
        "👤 Профиль",
        "",
        profile_display_name(user, data),
        "",
        f"🔗 {username}",
        f"🆔 {user.id}",
        f"💎 Статус: {status}",
        f"🪙 Random Coins: {balance:,}".replace(",", " "),
    ]

    level = int(data.get("level") or 1)
    xp = int(data.get("xp") or 0)
    likes = int(data.get("likes") or 0)
    streak = int(data.get("streak") or 0)
    title = data.get("title") or "Новичок"
    favorite_id = data.get("favoriteDecoration")

    rank = data.get("rank") or "Новичок"
    custom_status = data.get("customStatus") or ""
    friends_count = int(data.get("friends") or 0)
    selected_background = data.get("selectedBackground")

    lines.append(f"⭐ Уровень: {level} · XP: {xp}")
    lines.append(f"👑 Ранг: {rank}")
    lines.append(f"🎖 Титул: {title}")
    if custom_status:
        lines.append(f"🪪 Статус: {custom_status}")
    lines.append(f"❤️ Лайков: {likes}")
    lines.append(f"🧑‍🤝‍🧑 Друзей: {friends_count}")
    lines.append(f"📅 Серия входов: {streak} дн.")
    if selected_background:
        bg = next((x for x in cosmetics if x.get("id") == selected_background), None)
        if bg:
            lines.append(f"🖼 Фон: {bg.get('name')}")

    if cosmetics:
        lines.append(f"✨ Украшений: {equipped_count}/{len(cosmetics)}")

    if favorite_id:
        favorite = next((x for x in cosmetics if x.get("id") == favorite_id), None)
        if favorite:
            lines.append(f"⭐ Избранное: {favorite.get('name')}")

    if profile_has_cosmetic(data, "name_color"):
        color_emoji, color_name = profile_color_meta(data.get("nameColor") or "white")
        lines.append(f"🎨 Цвет ника: {color_emoji} {color_name}")

    if "message_style" in equipped_cosmetic_ids(data):
        lines.append("💬 Особый стиль сообщений: включён")

    stats = data.get("stats") or {}
    if stats:
        lines.append("")
        lines.append(
            "📊 Статистика: "
            f"сообщений {int(stats.get('messages') or 0)}, "
            f"покупок {int(stats.get('purchases') or 0)}, "
            f"кейсов {int(stats.get('casesOpened') or 0)}"
        )

    return "\n".join(lines)


def profile_keyboard(data):
    rows = []
    if data.get("cosmetics"):
        rows.append([InlineKeyboardButton("✨ Украшения Профиля", callback_data="profile_decor")])
        rows.append([InlineKeyboardButton("⭐ Избранное украшение", callback_data="profile_favorite")])
    if data.get("unlockedTitles"):
        rows.append([InlineKeyboardButton("🎖 Выбрать титул", callback_data="profile_titles")])

    backgrounds = [
        item for item in (data.get("cosmetics") or [])
        if item.get("kind") == "background"
    ]
    if backgrounds:
        rows.append([InlineKeyboardButton("🖼 Фон профиля", callback_data="profile_background")])

    rows.append([InlineKeyboardButton("🪪 Изменить статус", callback_data="profile_status")])
    return InlineKeyboardMarkup(rows) if rows else None


def decorations_text(data):
    cosmetics = data.get("cosmetics") or []
    lines = ["✨ Украшения Профиля", ""]

    for item in cosmetics:
        mark = "✅" if item.get("equipped") else "⚪"
        lines.append(f"{mark} {item.get('name')}")

    if profile_has_cosmetic(data, "name_color"):
        color_emoji, color_name = profile_color_meta(data.get("nameColor") or "white")
        lines.append("")
        lines.append(f"🎨 Выбранный цвет: {color_emoji} {color_name}")

    lines.append("")
    lines.append("Нажми на украшение, чтобы включить или выключить его.")
    return "\n".join(lines)


def decorations_keyboard(data):
    rows = []
    for item in data.get("cosmetics") or []:
        mark = "✅" if item.get("equipped") else "⚪"
        rows.append([
            InlineKeyboardButton(
                f"{mark} {item.get('name')}",
                callback_data=f"profile_toggle:{item.get('id')}",
            )
        ])

    if profile_has_cosmetic(data, "name_color"):
        color_emoji, color_name = profile_color_meta(data.get("nameColor") or "white")
        rows.append([
            InlineKeyboardButton(
                f"🎨 Цвет: {color_emoji} {color_name}",
                callback_data="profile_colors",
            )
        ])

    rows.append([InlineKeyboardButton("⬅️ Назад в профиль", callback_data="profile_back")])
    return InlineKeyboardMarkup(rows)


def profile_colors_text(data):
    color_emoji, color_name = profile_color_meta(data.get("nameColor") or "white")
    return (
        "🎨 Цвет ника\n\n"
        f"Сейчас выбран: {color_emoji} {color_name}\n\n"
        "Выбери новый цвет:"
    )


def profile_colors_keyboard(data):
    selected = data.get("nameColor") or "white"
    buttons = []

    for color_id, emoji, name in PROFILE_COLOR_OPTIONS:
        prefix = "✅ " if color_id == selected else ""
        buttons.append(
            InlineKeyboardButton(
                f"{prefix}{emoji} {name}",
                callback_data=f"profile_color:{color_id}",
            )
        )

    rows = []
    for i in range(0, len(buttons), 2):
        rows.append(buttons[i:i + 2])

    rows.append([InlineKeyboardButton("⬅️ К украшениям", callback_data="profile_decor")])
    return InlineKeyboardMarkup(rows)


async def handle_profile_colors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    await query.answer()

    try:
        response, data = await fetch_profile(query.from_user.id)
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Профиль сейчас недоступен.", show_alert=True)
            return

        if not profile_has_cosmetic(data, "name_color"):
            await query.answer("Сначала купите «🎨 Цвет ника».", show_alert=True)
            return

        await query.edit_message_text(
            profile_colors_text(data),
            reply_markup=profile_colors_keyboard(data),
        )
    except Exception:
        logging.exception("Ошибка открытия выбора цвета")
        await query.answer("❌ Цвета сейчас недоступны.", show_alert=True)


async def handle_profile_color_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    color_id = query.data.split(":", 1)[1]
    valid_ids = {option_id for option_id, _emoji, _name in PROFILE_COLOR_OPTIONS}
    if color_id not in valid_ids:
        await query.answer("❌ Неизвестный цвет.", show_alert=True)
        return

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(
                f"{SPOOKY_PRICE_API}/profile/color",
                json={"userId": query.from_user.id, "colorId": color_id},
                headers=shop_headers(),
            )

        data = response.json()
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Не удалось изменить цвет.", show_alert=True)
            return

        emoji, name = profile_color_meta(color_id)
        await query.answer(f"✅ {name}")

        response2, profile_data = await fetch_profile(query.from_user.id)
        if response2.status_code == 200 and profile_data.get("ok"):
            await query.edit_message_text(
                profile_colors_text(profile_data),
                reply_markup=profile_colors_keyboard(profile_data),
            )
    except Exception:
        logging.exception("Ошибка изменения цвета ника")
        await query.answer("❌ Не удалось изменить цвет.", show_alert=True)


def titles_keyboard(data):
    selected = data.get("titleId")
    rows = []
    for title in data.get("unlockedTitles") or []:
        mark = "✅ " if title.get("id") == selected else ""
        rows.append([
            InlineKeyboardButton(
                f"{mark}🎖 {title.get('name')}",
                callback_data=f"profile_title:{title.get('id')}",
            )
        ])
    rows.append([InlineKeyboardButton("⬅️ Назад в профиль", callback_data="profile_back")])
    return InlineKeyboardMarkup(rows)


def favorite_keyboard(data):
    selected = data.get("favoriteDecoration")
    rows = []
    for item in data.get("cosmetics") or []:
        mark = "⭐ " if item.get("id") == selected else ""
        rows.append([
            InlineKeyboardButton(
                f"{mark}{item.get('name')}",
                callback_data=f"profile_fav:{item.get('id')}",
            )
        ])
    rows.append([InlineKeyboardButton("⬅️ Назад в профиль", callback_data="profile_back")])
    return InlineKeyboardMarkup(rows)


async def handle_profile_titles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    try:
        response, data = await fetch_profile(query.from_user.id)
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Профиль недоступен.", show_alert=True)
            return
        await query.edit_message_text(
            "🎖 Выберите титул профиля:",
            reply_markup=titles_keyboard(data),
        )
    except Exception:
        logging.exception("Ошибка меню титулов")
        await query.answer("❌ Титулы недоступны.", show_alert=True)


async def handle_profile_title_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    title_id = query.data.split(":", 1)[1]
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(
                f"{SPOOKY_PRICE_API}/profile/title",
                json={"userId": query.from_user.id, "titleId": title_id},
                headers=shop_headers(),
            )
        data = response.json()
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("🔒 Этот титул пока недоступен.", show_alert=True)
            return
        await query.answer("✅ Титул выбран")
        response2, profile_data = await fetch_profile(query.from_user.id)
        if response2.status_code == 200 and profile_data.get("ok"):
            await query.edit_message_text(
                "🎖 Выберите титул профиля:",
                reply_markup=titles_keyboard(profile_data),
            )
    except Exception:
        logging.exception("Ошибка смены титула")
        await query.answer("❌ Не удалось сменить титул.", show_alert=True)


async def handle_profile_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    try:
        response, data = await fetch_profile(query.from_user.id)
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Профиль недоступен.", show_alert=True)
            return
        if not data.get("cosmetics"):
            await query.answer("У вас нет украшений.", show_alert=True)
            return
        await query.edit_message_text(
            "⭐ Выберите главное украшение:",
            reply_markup=favorite_keyboard(data),
        )
    except Exception:
        logging.exception("Ошибка меню избранного украшения")
        await query.answer("❌ Избранное недоступно.", show_alert=True)


async def handle_profile_favorite_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    item_id = query.data.split(":", 1)[1]
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(
                f"{SPOOKY_PRICE_API}/profile/favorite",
                json={"userId": query.from_user.id, "itemId": item_id},
                headers=shop_headers(),
            )
        data = response.json()
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Это украшение недоступно.", show_alert=True)
            return
        await query.answer("⭐ Выбрано")
        response2, profile_data = await fetch_profile(query.from_user.id)
        if response2.status_code == 200 and profile_data.get("ok"):
            await query.edit_message_text(
                "⭐ Выберите главное украшение:",
                reply_markup=favorite_keyboard(profile_data),
            )
    except Exception:
        logging.exception("Ошибка выбора избранного")
        await query.answer("❌ Не удалось выбрать.", show_alert=True)


async def other_profile_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    context.user_data["other_profile_stage"] = "choose"
    await update.message.reply_text(
        "👥 Выберите пользователя, чей профиль хотите посмотреть.",
        reply_markup=other_profile_keyboard,
    )


async def show_other_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, shared_user):
    clear_modes(context)

    target_id = shared_user.user_id
    first_name = shared_user.first_name or "Пользователь"
    last_name = shared_user.last_name or ""
    full_name = (first_name + (" " + last_name if last_name else "")).strip()
    username = shared_user.username or None

    user_view = SimpleNamespace(
        id=target_id,
        full_name=full_name,
        username=username,
    )

    try:
        response, data = await fetch_profile(target_id)
        if response.status_code != 200 or not data.get("ok"):
            await update.message.reply_text(
                "❌ Не удалось открыть профиль пользователя.",
                reply_markup=get_main_keyboard(update.effective_user.id),
            )
            return

        await update.message.reply_text(
            "👥 Профиль другого пользователя\n\n" + profile_text(user_view, data),
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
    except Exception:
        logging.exception("Ошибка просмотра чужого профиля")
        await update.message.reply_text(
            "❌ Профиль пользователя сейчас недоступен.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)

    try:
        response, data = await fetch_profile(update.effective_user.id)
        if response.status_code != 200 or not data.get("ok"):
            error_text = data.get("error") or f"HTTP {response.status_code}"
            await update.message.reply_text(
                f"❌ Не удалось открыть профиль: {error_text}",
                reply_markup=get_main_keyboard(update.effective_user.id),
            )
            return

        await update.message.reply_text(
            profile_text(update.effective_user, data),
            reply_markup=profile_keyboard(data),
        )
    except Exception:
        logging.exception("Ошибка профиля")
        await update.message.reply_text(
            "❌ Профиль сейчас недоступен.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )


async def handle_profile_decor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()

    try:
        response, data = await fetch_profile(query.from_user.id)
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Профиль сейчас недоступен.", show_alert=True)
            return

        if not data.get("cosmetics"):
            await query.answer("У вас пока нет украшений.", show_alert=True)
            return

        await query.edit_message_text(
            decorations_text(data),
            reply_markup=decorations_keyboard(data),
        )
    except Exception:
        logging.exception("Ошибка открытия украшений")
        await query.answer("❌ Украшения сейчас недоступны.", show_alert=True)


async def handle_profile_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    item_id = query.data.split(":", 1)[1]

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(
                f"{SPOOKY_PRICE_API}/profile/decorate",
                json={"userId": query.from_user.id, "itemId": item_id},
                headers=shop_headers(),
            )

        data = response.json()
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Не удалось изменить украшение.", show_alert=True)
            return

        await query.answer("✅ Обновлено")

        response2, profile_data = await fetch_profile(query.from_user.id)
        if response2.status_code == 200 and profile_data.get("ok"):
            await query.edit_message_text(
                decorations_text(profile_data),
                reply_markup=decorations_keyboard(profile_data),
            )
    except Exception:
        logging.exception("Ошибка переключения украшения")
        await query.answer("❌ Не удалось изменить украшение.", show_alert=True)


async def handle_profile_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()

    try:
        response, data = await fetch_profile(query.from_user.id)
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Профиль сейчас недоступен.", show_alert=True)
            return

        await query.edit_message_text(
            profile_text(query.from_user, data),
            reply_markup=profile_keyboard(data),
        )
    except Exception:
        logging.exception("Ошибка возврата в профиль")
        await query.answer("❌ Профиль сейчас недоступен.", show_alert=True)


async def has_message_style(user_id: int):
    try:
        response, data = await fetch_profile(user_id)
        return (
            response.status_code == 200
            and data.get("ok")
            and "message_style" in equipped_cosmetic_ids(data)
        )
    except Exception:
        return False


async def user_has_premium(user_id: int):
    try:
        response, data = await fetch_shop(user_id)
        if response.status_code != 200 or not data.get("ok"):
            return False

        for item in data.get("items") or []:
            if item.get("id") == "premium" and item.get("owned"):
                return True
    except Exception:
        logging.exception("Не удалось проверить Premium")

    return False


def shop_text(data):
    balance = int(data.get("balance") or 0)
    items = [
        item for item in (data.get("items") or [])
        if item.get("category") == "main"
    ]

    lines = [
        "🛒 Магазин",
        "",
        f"🪙 Баланс: {balance:,} Random Coins".replace(",", " "),
        "",
    ]

    for item in items:
        name = item.get("name")
        price = int(item.get("price") or 0)
        status = " ✅" if item.get("owned") else ""
        lines.append(f"• {name} — {price:,} RC{status}".replace(",", " "))

    lines.append("")
    lines.append("✨ Нажми «Украшения», чтобы открыть украшения профиля.")

    return "\n".join(lines)


def shop_items_text(data):
    balance = int(data.get("balance") or 0)
    items = [
        item for item in (data.get("items") or [])
        if item.get("category") == "items"
    ]

    lines = [
        "✨ Украшения",
        "",
        f"🪙 Баланс: {balance:,} Random Coins".replace(",", " "),
        "",
    ]

    for item in items:
        name = item.get("name")
        price = int(item.get("price") or 0)
        status = " ✅" if item.get("owned") else ""
        lines.append(f"• {name} — {price:,} RC{status}".replace(",", " "))

    return "\n".join(lines)


async def show_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)

    try:
        response, data = await fetch_shop(update.effective_user.id)
        if response.status_code != 200 or not data.get("ok"):
            error_text = data.get("error") or f"HTTP {response.status_code}"
            await update.message.reply_text(
                f"❌ Не удалось открыть магазин: {error_text}",
                reply_markup=get_main_keyboard(update.effective_user.id),
            )
            return

        await update.message.reply_text(
            shop_text(data),
            reply_markup=shop_keyboard(data.get("items") or []),
        )

    except Exception:
        logging.exception("Ошибка магазина")
        await update.message.reply_text(
            "❌ Магазин сейчас недоступен. Попробуйте чуть позже.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )


async def handle_shop_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    await query.answer()

    try:
        response, data = await fetch_shop(query.from_user.id)
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Магазин сейчас недоступен.", show_alert=True)
            return

        await query.edit_message_text(
            shop_items_text(data),
            reply_markup=shop_items_keyboard(data.get("items") or []),
        )
    except Exception:
        logging.exception("Не удалось открыть украшения магазина")
        await query.answer("❌ Украшения сейчас недоступны.", show_alert=True)


async def handle_shop_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    await query.answer()

    try:
        response, data = await fetch_shop(query.from_user.id)
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Магазин сейчас недоступен.", show_alert=True)
            return

        await query.edit_message_text(
            shop_text(data),
            reply_markup=shop_keyboard(data.get("items") or []),
        )
    except Exception:
        logging.exception("Не удалось вернуться в магазин")
        await query.answer("❌ Магазин сейчас недоступен.", show_alert=True)


async def handle_shop_owned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer("✅ Этот товар уже куплен.", show_alert=True)


async def handle_shop_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    await query.answer()

    item_id = query.data.split(":", 1)[1]

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(
                f"{SPOOKY_PRICE_API}/buy",
                json={
                    "userId": query.from_user.id,
                    "itemId": item_id,
                },
                headers=shop_headers(),
            )

        data = response.json()

        if response.status_code != 200 or not data.get("ok"):
            code = data.get("code")
            if code == "insufficient_funds":
                missing = int(data.get("missing") or 0)
                await query.answer(
                    f"❌ Не хватает {missing:,} Random Coins".replace(",", " "),
                    show_alert=True,
                )
                return

            if code == "already_owned":
                await query.answer("✅ Этот товар уже куплен.", show_alert=True)
            elif code == "premium_required":
                await query.answer("🔒 Это украшение доступно только с Premium.", show_alert=True)
            elif code == "expired":
                await query.answer("⏳ Это ограниченное украшение уже недоступно.", show_alert=True)
            elif code == "daily_only":
                await query.answer("🎁 Этот эксклюзив можно получить только из ежедневной награды.", show_alert=True)
            else:
                await query.answer(
                    "❌ Не удалось выполнить покупку.",
                    show_alert=True,
                )
            return

        item = data.get("item") or {}
        balance = int(data.get("balance") or 0)
        item_name = item.get("name") or item_id

        await query.answer(f"✅ Куплено: {item_name}", show_alert=True)

        try:
            response2, shop_data = await fetch_shop(query.from_user.id)
            if response2.status_code == 200 and shop_data.get("ok"):
                if item.get("category") == "items":
                    await query.edit_message_text(
                        shop_items_text(shop_data),
                        reply_markup=shop_items_keyboard(shop_data.get("items") or []),
                    )
                elif item.get("category") == "titles":
                    await query.edit_message_text(
                        "🎖 Магазин титулов\n\nКупленный титул сразу становится выбранным.",
                        reply_markup=shop_titles_keyboard(shop_data.get("items") or []),
                    )
                else:
                    await query.edit_message_text(
                        shop_text(shop_data),
                        reply_markup=shop_keyboard(shop_data.get("items") or []),
                    )
        except Exception:
            logging.exception("Не удалось обновить магазин после покупки")

        try:
            username = f"@{query.from_user.username}" if query.from_user.username else "нет username"
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "🛒 Покупка в магазине\n\n"
                    f"👤 {query.from_user.full_name}\n"
                    f"🔗 {username}\n"
                    f"🆔 {query.from_user.id}\n"
                    f"🎁 Товар: {item_name}\n"
                    f"🪙 Остаток: {balance:,} RC".replace(",", " ")
                ),
            )
        except Exception:
            logging.exception("Не удалось уведомить администратора о покупке")

    except Exception:
        logging.exception("Ошибка покупки в магазине")
        await query.answer(
            "❌ Магазин сейчас недоступен.",
            show_alert=True,
        )


async def api_post(path: str, payload: dict):
    async with httpx.AsyncClient(timeout=12.0) as client:
        response = await client.post(
            f"{SPOOKY_PRICE_API}{path}",
            json=payload,
            headers=shop_headers(),
        )
    try:
        data = response.json()
    except Exception:
        data = {}
    return response, data


async def track_activity(user):
    try:
        await api_post(
            "/activity",
            {
                "userId": user.id,
                "kind": "message",
                "displayName": user.full_name,
                "username": user.username or "",
            },
        )
    except Exception:
        logging.debug("Не удалось записать активность", exc_info=True)


async def activities_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    await update.message.reply_text(
        "🎮 Активности\n\nВыберите действие:",
        reply_markup=activities_keyboard,
    )


async def notifications_enabled(user_id: int):
    try:
        response, data = await fetch_profile(user_id)
        return response.status_code == 200 and data.get("ok") and data.get("notifications", True)
    except Exception:
        return True


async def friends_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    context.user_data["friends_stage"] = "choose"
    try:
        response, data = await api_post("/friends/list", {"userId": update.effective_user.id})
        friends = data.get("friends") or [] if response.status_code == 200 else []
        lines = ["🧑‍🤝‍🧑 Друзья", ""]
        if friends:
            for friend in friends[:30]:
                who = f"@{friend.get('username')}" if friend.get("username") else (friend.get("displayName") or f"ID {friend.get('userId')}")
                lines.append(f"• {who} · ур. {int(friend.get('level') or 1)}")
        else:
            lines.append("Список друзей пока пуст.")
        lines.append("")
        lines.append("Нажми кнопку ниже, чтобы добавить или удалить друга.")
        await update.message.reply_text("\n".join(lines), reply_markup=friends_user_keyboard)
    except Exception:
        logging.exception("Ошибка списка друзей")
        await update.message.reply_text("❌ Друзья сейчас недоступны.", reply_markup=activities_keyboard)


async def toggle_friend(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    try:
        response, data = await api_post(
            "/friends/toggle",
            {"userId": update.effective_user.id, "targetId": target_id},
        )
        clear_modes(context)
        if response.status_code != 200 or not data.get("ok"):
            await update.message.reply_text("❌ Не удалось изменить список друзей.", reply_markup=activities_keyboard)
            return
        text = "✅ Пользователь добавлен в друзья." if data.get("enabled") else "➖ Пользователь удалён из друзей."
        await update.message.reply_text(text, reply_markup=activities_keyboard)
    except Exception:
        logging.exception("Ошибка изменения друзей")
        clear_modes(context)
        await update.message.reply_text("❌ Друзья сейчас недоступны.", reply_markup=activities_keyboard)


async def direct_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    context.user_data["direct_stage"] = "choose"
    await update.message.reply_text(
        "💌 Выберите пользователя, которому хотите написать через бота.",
        reply_markup=direct_user_keyboard,
    )


async def direct_choose_message(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    context.user_data["direct_stage"] = "message"
    context.user_data["direct_target_id"] = target_id
    await update.message.reply_text(
        "✍️ Напишите сообщение:",
        reply_markup=cancel_keyboard,
    )


async def direct_send(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    target_id = context.user_data.get("direct_target_id")
    if not target_id:
        clear_modes(context)
        await update.message.reply_text("❌ Получатель не найден.", reply_markup=activities_keyboard)
        return
    user = update.effective_user
    sender = f"@{user.username}" if user.username else user.full_name
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"💌 Личное сообщение от {sender}\n\n{text}",
        )
        clear_modes(context)
        await track_activity(user)
        await update.message.reply_text("✅ Сообщение отправлено.", reply_markup=activities_keyboard)
    except Exception:
        logging.exception("Ошибка личного сообщения")
        clear_modes(context)
        await update.message.reply_text("❌ Не удалось доставить сообщение.", reply_markup=activities_keyboard)


async def show_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    try:
        response, data = await api_post("/achievements", {"userId": update.effective_user.id})
        if response.status_code != 200 or not data.get("ok"):
            raise RuntimeError("achievements api")
        lines = ["🏅 Достижения", ""]
        for a in data.get("achievements") or []:
            lines.append(f"{'✅' if a.get('unlocked') else '🔒'} {a.get('name')}")
        await update.message.reply_text("\n".join(lines), reply_markup=activities_keyboard)
    except Exception:
        logging.exception("Ошибка достижений")
        await update.message.reply_text("❌ Достижения недоступны.", reply_markup=activities_keyboard)


async def show_quests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    try:
        response, data = await api_post("/quests", {"userId": update.effective_user.id})
        if response.status_code != 200 or not data.get("ok"):
            raise RuntimeError("quests api")
        rows = []
        lines = ["🎯 Задания на сегодня", ""]
        for q in data.get("quests") or []:
            progress = min(int(q.get("progress") or 0), int(q.get("target") or 0))
            target = int(q.get("target") or 0)
            mark = "✅" if q.get("claimed") else ("🟢" if q.get("done") else "⚪")
            lines.append(f"{mark} {q.get('name')} — {progress}/{target} · +{int(q.get('reward') or 0)} RC")
            if q.get("done") and not q.get("claimed"):
                rows.append([InlineKeyboardButton(
                    f"🎁 Забрать: {q.get('name')}",
                    callback_data=f"quest_claim:{q.get('id')}",
                )])
        await update.message.reply_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(rows) if rows else activities_keyboard,
        )
    except Exception:
        logging.exception("Ошибка заданий")
        await update.message.reply_text("❌ Задания недоступны.", reply_markup=activities_keyboard)


async def handle_quest_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    quest_id = query.data.split(":", 1)[1]
    try:
        response, data = await api_post("/quests/claim", {"userId": query.from_user.id, "questId": quest_id})
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Награду пока нельзя забрать.", show_alert=True)
            return
        await query.answer(f"🎁 +{int(data.get('reward') or 0)} RC", show_alert=True)
        await query.edit_message_text(
            f"✅ Задание выполнено!\n🪙 +{int(data.get('reward') or 0)} RC\n👛 Баланс: {int(data.get('balance') or 0)} RC"
        )
    except Exception:
        logging.exception("Ошибка получения награды задания")
        await query.answer("❌ Задания недоступны.", show_alert=True)


async def bank_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    try:
        response, data = await api_post("/bank", {"userId": update.effective_user.id})
        if response.status_code != 200 or not data.get("ok"):
            raise RuntimeError("bank api")
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Положить", callback_data="bank:deposit"),
                InlineKeyboardButton("➖ Снять", callback_data="bank:withdraw"),
            ]
        ])
        await update.message.reply_text(
            (
                "🏦 Банк\n\n"
                f"👛 Кошелёк: {int(data.get('balance') or 0):,} RC\n"
                f"🏦 На депозите: {int(data.get('bankBalance') or 0):,} RC\n"
                f"📈 Бонус: {data.get('rateDaily', 1)}% в сутки"
            ).replace(",", " "),
            reply_markup=keyboard,
        )
    except Exception:
        logging.exception("Ошибка банка")
        await update.message.reply_text("❌ Банк недоступен.", reply_markup=activities_keyboard)


async def handle_bank_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    action = query.data.split(":", 1)[1]
    context.user_data["bank_stage"] = action
    await query.answer()
    await query.message.reply_text(
        "Введите сумму Random Coins:",
        reply_markup=cancel_keyboard,
    )


async def bank_amount(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    action = context.user_data.get("bank_stage")
    raw = text.replace(" ", "").replace(",", "")
    if not raw.isdigit() or int(raw) < 1:
        await update.message.reply_text("❌ Введите целое число больше 0.", reply_markup=cancel_keyboard)
        return
    amount = int(raw)
    path = "/bank/deposit" if action == "deposit" else "/bank/withdraw"
    try:
        response, data = await api_post(path, {"userId": update.effective_user.id, "amount": amount})
        clear_modes(context)
        if response.status_code != 200 or not data.get("ok"):
            await update.message.reply_text("❌ Недостаточно средств или неверная сумма.", reply_markup=activities_keyboard)
            return
        await update.message.reply_text(
            (
                f"✅ Операция выполнена.\n"
                f"👛 Кошелёк: {int(data.get('balance') or 0):,} RC\n"
                f"🏦 Банк: {int(data.get('bankBalance') or 0):,} RC"
            ).replace(",", " "),
            reply_markup=activities_keyboard,
        )
    except Exception:
        logging.exception("Ошибка банка")
        clear_modes(context)
        await update.message.reply_text("❌ Банк недоступен.", reply_markup=activities_keyboard)


async def show_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    try:
        response, data = await api_post("/season", {"userId": update.effective_user.id})
        season = data.get("season") or {}
        if response.status_code != 200 or not data.get("ok"):
            raise RuntimeError("season api")

        lines = [
            f"🎫 {season.get('name') or 'Сезон'}",
            f"⭐ Ваш уровень: {int(season.get('level') or 1)}",
        ]
        ends_at = int(season.get("endsAt") or 0)
        if ends_at:
            remain_ms = max(0, ends_at - int(time.time() * 1000))
            days_left = (remain_ms + 86_399_999) // 86_400_000
            lines.append(f"⏳ Осталось примерно: {days_left} дн.")
        lines.append("")

        rows = []
        for tier in season.get("tiers") or []:
            mark = "✅" if tier.get("claimed") else ("🟢" if tier.get("unlocked") else "🔒")
            rewards = []
            coins = int(tier.get("reward") or 0)
            if coins:
                rewards.append(f"{coins:,} RC".replace(",", " "))
            item = tier.get("item")
            if item:
                rewards.append(item.get("name") or tier.get("itemId"))
            reward_text = " + ".join(rewards) if rewards else "без награды"
            lines.append(
                f"{mark} Этап {tier.get('tier')} · нужен ур. {tier.get('need')} · {reward_text}"
            )
            if tier.get("unlocked") and not tier.get("claimed"):
                rows.append([InlineKeyboardButton(
                    f"🎁 Забрать этап {tier.get('tier')}",
                    callback_data=f"season_claim:{tier.get('tier')}",
                )])

        await update.message.reply_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(rows) if rows else activities_keyboard,
        )
    except Exception:
        logging.exception("Ошибка сезона")
        await update.message.reply_text("❌ Сезон недоступен.", reply_markup=activities_keyboard)


async def handle_season_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    tier = int(query.data.split(":", 1)[1])
    try:
        response, data = await api_post("/season/claim", {"userId": query.from_user.id, "tier": tier})
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Награда недоступна.", show_alert=True)
            return

        rewards = []
        coins = int(data.get("reward") or 0)
        if coins:
            rewards.append(f"+{coins:,} RC".replace(",", " "))
        item = data.get("rewardItem")
        if item:
            rewards.append(item.get("name") or "предмет")
        elif data.get("itemAlreadyOwned"):
            rewards.append("предмет уже был в коллекции")

        reward_text = " + ".join(rewards) if rewards else "награда получена"
        await query.answer(f"🎁 {reward_text}", show_alert=True)
        await query.edit_message_text(
            f"✅ Награда сезона получена: {reward_text}\n"
            f"👛 Баланс: {int(data.get('balance') or 0):,} RC".replace(",", " ")
        )
    except Exception:
        await query.answer("❌ Сезон недоступен.", show_alert=True)


async def show_daily_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    try:
        response, data = await api_post("/calendar", {})
        if response.status_code != 200 or not data.get("ok"):
            raise RuntimeError("calendar")
        lines = ["📅 Календарь ежедневных наград", ""]
        days = data.get("days") or []
        if not days:
            lines.append("Администратор ещё не настроил календарь.")
        for day in days[:30]:
            if day.get("surprise"):
                lines.append(f"🎁 День {day.get('day')}: СЮРПРИЗ")
            else:
                parts = []
                if int(day.get("coins") or 0):
                    parts.append(f"{int(day.get('coins') or 0)} RC")
                if day.get("item"):
                    parts.append(day.get("item", {}).get("name"))
                lines.append(f"• День {day.get('day')}: " + (" + ".join(parts) if parts else "без награды"))
        await update.message.reply_text("\n".join(lines), reply_markup=activities_keyboard)
    except Exception:
        logging.exception("Ошибка календаря")
        await update.message.reply_text("❌ Календарь недоступен.", reply_markup=activities_keyboard)


async def show_rotation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    try:
        response, data = await fetch_shop(update.effective_user.id)
        items = [x for x in (data.get("items") or []) if x.get("rotating")]
        lines = ["🔄 Ротация магазина сегодня", ""]
        if not items:
            lines.append("Сегодня отдельной ротации нет.")
        for item in items:
            lines.append(f"• {item.get('name')} — {int(item.get('price') or 0):,} RC".replace(",", " "))
        await update.message.reply_text("\n".join(lines), reply_markup=activities_keyboard)
    except Exception:
        logging.exception("Ошибка ротации")
        await update.message.reply_text("❌ Ротация недоступна.", reply_markup=activities_keyboard)


async def show_balance_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    try:
        response, data = await api_post("/balance/history", {"userId": update.effective_user.id})
        rows = data.get("history") or []
        lines = ["📈 История баланса", ""]
        if not rows:
            lines.append("История пока пустая.")
        labels = {
            "purchase":"Покупка","daily":"Ежедневка","transfer_out":"Перевод",
            "transfer_in":"Получено","gift":"Подарок","quest":"Задание",
            "bank_deposit":"В банк","bank_withdraw":"Из банка","sell":"Продажа",
            "season":"Сезон","bundle":"Набор","promo":"Промокод","case":"Кейс","case_reward":"Награда кейса","admin_add":"Админ +","admin_remove":"Админ -",
        }
        for row in rows[:20]:
            amount = int(row.get("amount") or 0)
            sign = "+" if amount > 0 else ""
            lines.append(f"• {labels.get(row.get('type'), row.get('type'))}: {sign}{amount:,} RC".replace(",", " "))
        await update.message.reply_text("\n".join(lines), reply_markup=activities_keyboard)
    except Exception:
        logging.exception("Ошибка истории баланса")
        await update.message.reply_text("❌ История недоступна.", reply_markup=activities_keyboard)


async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    try:
        response, data = await api_post("/notifications", {"userId": update.effective_user.id})
        current = bool(data.get("enabled", True))
        response2, data2 = await api_post("/notifications", {"userId": update.effective_user.id, "enabled": not current})
        enabled = bool(data2.get("enabled", not current))
        await update.message.reply_text(
            f"🔔 Уведомления: {'включены' if enabled else 'выключены'}",
            reply_markup=activities_keyboard,
        )
    except Exception:
        logging.exception("Ошибка уведомлений")
        await update.message.reply_text("❌ Не удалось изменить уведомления.", reply_markup=activities_keyboard)


async def status_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    context.user_data["status_waiting"] = True
    await update.message.reply_text(
        "🪪 Напишите статус профиля до 80 символов.\nЧтобы очистить — отправьте «-».",
        reply_markup=cancel_keyboard,
    )


async def status_set(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    value = "" if text.strip() == "-" else text.strip()[:80]
    try:
        response, data = await api_post("/profile/status", {"userId": update.effective_user.id, "status": value})
        clear_modes(context)
        if response.status_code != 200 or not data.get("ok"):
            raise RuntimeError("status")
        await update.message.reply_text(
            f"✅ Статус профиля {'обновлён' if value else 'очищен'}.",
            reply_markup=activities_keyboard,
        )
    except Exception:
        logging.exception("Ошибка статуса")
        clear_modes(context)
        await update.message.reply_text("❌ Не удалось изменить статус.", reply_markup=activities_keyboard)


async def show_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    try:
        response, data = await fetch_shop(update.effective_user.id)
        event = data.get("event")
        if not event:
            text = "🎉 Сейчас активного ивента нет."
        else:
            text = (
                f"🎉 Ивент: {event.get('name') or 'Без названия'}\n"
                f"🎁 Бонус к ежедневке: +{int(event.get('dailyBonus') or 0)} RC"
            )
        await update.message.reply_text(text, reply_markup=activities_keyboard)
    except Exception:
        await update.message.reply_text("❌ Ивент сейчас недоступен.", reply_markup=activities_keyboard)


async def show_bundles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    try:
        response, data = await fetch_shop(update.effective_user.id)
        bundles = data.get("bundles") or []
        lines = ["📦 Наборы", ""]
        rows = []
        if not bundles:
            lines.append("Наборов пока нет.")
        for bundle in bundles:
            lines.append(f"• {bundle.get('name')} — {int(bundle.get('price') or 0):,} RC".replace(",", " "))
            rows.append([InlineKeyboardButton(
                f"Купить {bundle.get('name')}",
                callback_data=f"bundle_buy:{bundle.get('id')}",
            )])
        await update.message.reply_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(rows) if rows else activities_keyboard,
        )
    except Exception:
        logging.exception("Ошибка наборов")
        await update.message.reply_text("❌ Наборы недоступны.", reply_markup=activities_keyboard)


async def handle_bundle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    bundle_id = query.data.split(":", 1)[1]
    try:
        response, data = await api_post("/bundle/buy", {"userId": query.from_user.id, "bundleId": bundle_id})
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Не хватает коинов или набор недоступен.", show_alert=True)
            return
        await query.answer("📦 Набор куплен!", show_alert=True)
        granted = ", ".join(x.get("name") for x in (data.get("granted") or [])) or "все предметы уже были"
        await query.edit_message_text(
            f"✅ Набор куплен.\n🎁 Получено: {granted}\n👛 Баланс: {int(data.get('balance') or 0)} RC"
        )
    except Exception:
        await query.answer("❌ Наборы недоступны.", show_alert=True)


async def sell_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    try:
        response, data = await fetch_shop(update.effective_user.id)
        items = [
            x for x in (data.get("items") or [])
            if x.get("category") == "items" and x.get("owned") and not x.get("dailyOnly")
        ]
        rows = [[InlineKeyboardButton(
            f"🗑 {x.get('name')}",
            callback_data=f"sell_item:{x.get('id')}",
        )] for x in items]
        await update.message.reply_text(
            "🗑 Продажа украшений\n\nВозврат — 50% от цены покупки. Бесплатные/эксклюзивные награды продать нельзя.",
            reply_markup=InlineKeyboardMarkup(rows) if rows else activities_keyboard,
        )
    except Exception:
        await update.message.reply_text("❌ Продажа недоступна.", reply_markup=activities_keyboard)


async def handle_sell_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    item_id = query.data.split(":", 1)[1]
    try:
        response, data = await api_post("/sell", {"userId": query.from_user.id, "itemId": item_id})
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Этот предмет нельзя продать.", show_alert=True)
            return
        await query.answer(f"🪙 +{int(data.get('refund') or 0)} RC", show_alert=True)
        await query.edit_message_text(
            f"✅ Предмет продан.\n🪙 Получено: {int(data.get('refund') or 0)} RC\n👛 Баланс: {int(data.get('balance') or 0)} RC"
        )
    except Exception:
        await query.answer("❌ Продажа недоступна.", show_alert=True)


async def trade_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    context.user_data["trade_stage"] = "choose"
    await update.message.reply_text(
        "🔁 Выберите пользователя для обмена украшениями.",
        reply_markup=trade_user_keyboard,
    )


async def trade_choose_partner(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    context.user_data["trade_stage"] = "give"
    context.user_data["trade_target_id"] = target_id
    try:
        response, data = await fetch_shop(update.effective_user.id)
        items = [x for x in (data.get("items") or []) if x.get("category") == "items" and x.get("owned") and not x.get("dailyOnly")]
        rows = [[InlineKeyboardButton(
            x.get("name"),
            callback_data=f"trade_give:{x.get('id')}",
        )] for x in items]
        await update.message.reply_text(
            "🔁 Выберите украшение, которое вы отдаёте:",
            reply_markup=InlineKeyboardMarkup(rows) if rows else activities_keyboard,
        )
    except Exception:
        clear_modes(context)
        await update.message.reply_text("❌ Обмен недоступен.", reply_markup=activities_keyboard)


async def handle_trade_give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    item_id = query.data.split(":", 1)[1]
    target_id = context.user_data.get("trade_target_id")
    if not target_id:
        await query.answer("Сначала выберите пользователя.", show_alert=True)
        return
    context.user_data["trade_give_item"] = item_id
    context.user_data["trade_stage"] = "want"
    try:
        response, data = await fetch_shop(target_id)
        items = [x for x in (data.get("items") or []) if x.get("category") == "items" and x.get("owned") and not x.get("dailyOnly")]
        rows = [[InlineKeyboardButton(
            x.get("name"),
            callback_data=f"trade_want:{x.get('id')}",
        )] for x in items]
        await query.answer()
        await query.edit_message_text(
            "🔁 Теперь выберите украшение, которое хотите получить:",
            reply_markup=InlineKeyboardMarkup(rows),
        )
    except Exception:
        await query.answer("❌ Не удалось открыть инвентарь пользователя.", show_alert=True)


async def handle_trade_want(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    want_item = query.data.split(":", 1)[1]
    target_id = context.user_data.get("trade_target_id")
    give_item = context.user_data.get("trade_give_item")
    if not target_id or not give_item:
        await query.answer("Обмен устарел.", show_alert=True)
        return
    try:
        response, data = await api_post(
            "/trade/create",
            {
                "fromUserId": query.from_user.id,
                "toUserId": target_id,
                "giveItem": give_item,
                "wantItem": want_item,
            },
        )
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Не удалось создать обмен.", show_alert=True)
            return
        trade = data.get("trade") or {}
        trade_id = trade.get("id")
        clear_modes(context)
        await query.edit_message_text("✅ Предложение обмена отправлено пользователю.")
        if await notifications_enabled(target_id):
            await context.bot.send_message(
                chat_id=target_id,
                text="🔁 Вам предложили обмен украшениями. Принять?",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Принять", callback_data=f"trade_resp:{trade_id}:yes"),
                    InlineKeyboardButton("❌ Отклонить", callback_data=f"trade_resp:{trade_id}:no"),
                ]]),
            )
    except Exception:
        logging.exception("Ошибка создания обмена")
        await query.answer("❌ Обмен недоступен.", show_alert=True)


async def handle_trade_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    _, trade_id, answer = query.data.split(":", 2)
    try:
        response, data = await api_post(
            "/trade/respond",
            {"tradeId": trade_id, "userId": query.from_user.id, "accept": answer == "yes"},
        )
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Обмен уже недоступен.", show_alert=True)
            return
        await query.answer("✅ Готово" if answer == "yes" else "❌ Отклонено", show_alert=True)
        await query.edit_message_text("✅ Обмен выполнен." if answer == "yes" else "❌ Обмен отклонён.")
    except Exception:
        await query.answer("❌ Обмен недоступен.", show_alert=True)


async def profile_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    clear_modes(context)
    context.user_data["status_waiting"] = True
    await query.message.reply_text(
        "🪪 Напишите новый статус профиля до 80 символов. Для очистки отправьте «-».",
        reply_markup=cancel_keyboard,
    )


async def profile_background_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    try:
        response, data = await fetch_profile(query.from_user.id)
        backgrounds = [x for x in (data.get("cosmetics") or []) if x.get("kind") == "background"]
        rows = [[InlineKeyboardButton(
            x.get("name"),
            callback_data=f"profile_bg:{x.get('id')}",
        )] for x in backgrounds]
        rows.append([InlineKeyboardButton("⬅️ Назад", callback_data="profile_back")])
        await query.answer()
        await query.edit_message_text("🖼 Выберите фон профиля:", reply_markup=InlineKeyboardMarkup(rows))
    except Exception:
        await query.answer("❌ Фоны недоступны.", show_alert=True)


async def profile_background_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    item_id = query.data.split(":", 1)[1]
    try:
        response, data = await api_post("/profile/background", {"userId": query.from_user.id, "itemId": item_id})
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Этот фон недоступен.", show_alert=True)
            return
        await query.answer("✅ Фон выбран", show_alert=True)
        await query.edit_message_text(f"🖼 Выбран фон: {data.get('item', {}).get('name')}")
    except Exception:
        await query.answer("❌ Не удалось выбрать фон.", show_alert=True)


async def claim_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    user = update.effective_user
    try:
        response, data = await api_post(
            "/daily",
            {
                "userId": user.id,
                "displayName": user.full_name,
                "username": user.username or "",
            },
        )
        if response.status_code == 429 and data.get("code") == "daily_cooldown":
            remaining_ms = int(data.get("remainingMs") or 0)
            hours = remaining_ms // 3_600_000
            minutes = (remaining_ms % 3_600_000) // 60_000
            await update.message.reply_text(
                f"⏳ Награда уже получена. До следующей: {hours} ч {minutes} мин.\n"
                f"📅 Серия: {int(data.get('streak') or 0)} дн.",
                reply_markup=activities_keyboard,
            )
            return
        if response.status_code != 200 or not data.get("ok"):
            await update.message.reply_text("❌ Не удалось получить награду.", reply_markup=activities_keyboard)
            return

        reward = int(data.get("reward") or 0)
        milestone = int(data.get("milestone") or 0)
        streak = int(data.get("streak") or 0)
        balance = int(data.get("balance") or 0)
        reward_item = data.get("rewardItem")
        random_reward = data.get("randomReward")
        item_already_owned = bool(data.get("itemAlreadyOwned"))
        bonus_text = f"\n🎉 Бонус за серию: +{milestone:,} RC".replace(",", " ") if milestone else ""
        item_text = ""
        if reward_item:
            item_text = f"\n🎁 Предмет: {reward_item.get('name')}"
        elif item_already_owned:
            item_text = "\nℹ️ Предмет из награды у вас уже есть."

        random_text = ""
        if random_reward and random_reward.get("coins"):
            random_text = f"\n🎲 Случайный бонус сработал: +{int(random_reward.get('coins') or 0):,} RC".replace(",", " ")

        coins_text = f"🪙 +{reward:,} RC" if reward else "🪙 Без коинов"
        await update.message.reply_text(
            (
                f"🎁 Ежедневная награда\n"
                f"{coins_text}"
                f"{item_text}"
                f"{random_text}\n"
                f"📅 Серия входов: {streak} дн.{bonus_text}\n"
                f"👛 Баланс: {balance:,} RC"
            ).replace(",", " "),
            reply_markup=activities_keyboard,
        )
    except Exception:
        logging.exception("Ошибка ежедневной награды")
        await update.message.reply_text("❌ Сервис наград недоступен.", reply_markup=activities_keyboard)


async def show_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    try:
        response, data = await fetch_shop(update.effective_user.id)
        if response.status_code != 200 or not data.get("ok"):
            await update.message.reply_text("❌ Инвентарь недоступен.", reply_markup=activities_keyboard)
            return
        owned = [item for item in (data.get("items") or []) if item.get("owned")]
        lines = ["🧰 Инвентарь", ""]
        if not owned:
            lines.append("Пока пусто.")
        else:
            rarity_labels = {
                "common": "⚪ Обычный",
                "rare": "🔵 Редкий",
                "epic": "🟣 Эпический",
                "legendary": "🟡 Легендарный",
                "exclusive": "🔴 Эксклюзивный",
            }
            for item in owned:
                rarity = rarity_labels.get(item.get("rarity"), "⚪ Обычный")
                lines.append(f"• {item.get('name')} — {rarity}")
        await update.message.reply_text("\n".join(lines), reply_markup=activities_keyboard)
    except Exception:
        logging.exception("Ошибка инвентаря")
        await update.message.reply_text("❌ Инвентарь недоступен.", reply_markup=activities_keyboard)


async def transfer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    context.user_data["transfer_stage"] = "choose"
    await update.message.reply_text(
        "💸 Выберите пользователя, которому перевести Random Coins.",
        reply_markup=transfer_user_keyboard,
    )


async def transfer_choose_amount(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    context.user_data["transfer_stage"] = "amount"
    context.user_data["transfer_target_id"] = target_id
    await update.message.reply_text(
        f"💸 Сколько Random Coins перевести пользователю {target_id}?\n"
        "Напишите целое число.",
        reply_markup=cancel_keyboard,
    )


async def transfer_send(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    target_id = context.user_data.get("transfer_target_id")
    raw = text.replace(" ", "").replace(",", "")
    if not target_id or not raw.isdigit():
        await update.message.reply_text("❌ Напишите целое число.", reply_markup=cancel_keyboard)
        return
    amount = int(raw)
    try:
        response, data = await api_post(
            "/transfer",
            {"fromUserId": update.effective_user.id, "toUserId": target_id, "amount": amount},
        )
        if response.status_code != 200 or not data.get("ok"):
            code = data.get("code")
            if code == "insufficient_funds":
                msg = f"❌ Не хватает {int(data.get('missing') or 0):,} RC".replace(",", " ")
            elif code == "self_transfer":
                msg = "❌ Нельзя переводить коины самому себе."
            elif code == "economy_blocked":
                msg = "🚫 Переводы для одного из пользователей заблокированы администратором."
            else:
                msg = "❌ Перевод не выполнен."
            await update.message.reply_text(msg, reply_markup=activities_keyboard)
            clear_modes(context)
            return

        balance = int(data.get("fromBalance") or 0)
        clear_modes(context)
        await update.message.reply_text(
            f"✅ Переведено {amount:,} RC.\n👛 Баланс: {balance:,} RC".replace(",", " "),
            reply_markup=activities_keyboard,
        )
        try:
            if await notifications_enabled(target_id):
                await context.bot.send_message(
                    chat_id=target_id,
                    text=f"💸 Вам перевели {amount:,} Random Coins.".replace(",", " "),
                )
        except Exception:
            pass
    except Exception:
        logging.exception("Ошибка перевода")
        clear_modes(context)
        await update.message.reply_text("❌ Сервис переводов недоступен.", reply_markup=activities_keyboard)


async def gift_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    context.user_data["gift_stage"] = "choose"
    await update.message.reply_text(
        "🎁 Выберите пользователя, которому хотите купить украшение.",
        reply_markup=gift_user_keyboard,
    )


async def gift_choose_item(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    context.user_data["gift_stage"] = "item"
    context.user_data["gift_target_id"] = target_id
    try:
        response, data = await fetch_shop(target_id)
        if response.status_code != 200 or not data.get("ok"):
            await update.message.reply_text("❌ Не удалось открыть список подарков.", reply_markup=activities_keyboard)
            clear_modes(context)
            return
        items = [
            item for item in (data.get("items") or [])
            if item.get("category") == "items" and not item.get("owned")
        ]
        if not items:
            await update.message.reply_text("🎁 У этого пользователя уже есть все доступные украшения.", reply_markup=activities_keyboard)
            clear_modes(context)
            return
        rows = []
        for item in items:
            locked = " 🔒Premium" if item.get("locked") else ""
            rows.append([
                InlineKeyboardButton(
                    f"{item.get('name')} — {int(item.get('price') or 0):,} RC{locked}".replace(",", " "),
                    callback_data=f"gift_buy:{item.get('id')}",
                )
            ])
        rows.append([InlineKeyboardButton("❌ Отмена", callback_data="gift_cancel")])
        await update.message.reply_text(
            "🎁 Выберите украшение для подарка:",
            reply_markup=InlineKeyboardMarkup(rows),
        )
    except Exception:
        logging.exception("Ошибка списка подарков")
        clear_modes(context)
        await update.message.reply_text("❌ Подарки недоступны.", reply_markup=activities_keyboard)


async def handle_gift_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    item_id = query.data.split(":", 1)[1]
    target_id = context.user_data.get("gift_target_id")
    if not target_id:
        await query.answer("Сначала выберите получателя.", show_alert=True)
        return
    try:
        response, data = await api_post(
            "/gift/buy",
            {"fromUserId": query.from_user.id, "toUserId": target_id, "itemId": item_id},
        )
        if response.status_code != 200 or not data.get("ok"):
            code = data.get("code")
            messages = {
                "already_owned": "У получателя уже есть это украшение.",
                "recipient_premium_required": "Это украшение можно подарить только пользователю с Premium.",
                "insufficient_funds": "Не хватает Random Coins.",
                "expired": "Это ограниченное украшение уже недоступно.",
                "daily_only": "Этот эксклюзив можно получить только из ежедневной награды.",
                "economy_blocked": "Подарки для одного из пользователей заблокированы администратором.",
            }
            await query.answer(messages.get(code, "❌ Не удалось купить подарок."), show_alert=True)
            return
        item = data.get("item") or {}
        balance = int(data.get("balance") or 0)
        clear_modes(context)
        await query.answer("🎁 Подарок отправлен!", show_alert=True)
        await query.edit_message_text(
            f"✅ Подарено: {item.get('name')}\n🪙 Остаток: {balance:,} RC".replace(",", " ")
        )
        try:
            if await notifications_enabled(target_id):
                await context.bot.send_message(
                    chat_id=target_id,
                    text=f"🎁 Вам подарили украшение: {item.get('name')}!",
                )
        except Exception:
            pass
    except Exception:
        logging.exception("Ошибка покупки подарка")
        await query.answer("❌ Подарки недоступны.", show_alert=True)


async def handle_gift_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        clear_modes(context)
        await query.answer("Отменено")
        await query.edit_message_text("❌ Подарок отменён.")


async def promo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    context.user_data["promo_waiting"] = True
    await update.message.reply_text(
        "🎟 Введите промокод:",
        reply_markup=cancel_keyboard,
    )


async def promo_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    code = text.strip().upper()
    try:
        response, data = await api_post(
            "/promo/redeem",
            {"userId": update.effective_user.id, "code": code},
        )
        clear_modes(context)
        if response.status_code != 200 or not data.get("ok"):
            messages = {
                "promo_not_found": "❌ Промокод не найден.",
                "promo_used": "ℹ️ Вы уже использовали этот промокод.",
                "promo_limit": "❌ Лимит активаций промокода закончился.",
            }
            await update.message.reply_text(messages.get(data.get("code"), "❌ Промокод не сработал."), reply_markup=activities_keyboard)
            return
        reward = data.get("reward") or {}
        parts = ["✅ Промокод активирован!"]
        if reward.get("amount"):
            parts.append(f"🪙 +{int(reward['amount']):,} RC".replace(",", " "))
        if reward.get("item"):
            parts.append(f"🎁 {reward['item'].get('name')}")
        await update.message.reply_text("\n".join(parts), reply_markup=activities_keyboard)
    except Exception:
        logging.exception("Ошибка промокода")
        clear_modes(context)
        await update.message.reply_text("❌ Промокоды недоступны.", reply_markup=activities_keyboard)


async def admin_promo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    clear_modes(context)
    context.user_data["admin_promo_waiting"] = True
    await update.message.reply_text(
        "🎟 Создание промокода\n\n"
        "Для коинов: CODE 1000 50\n"
        "Для украшения: CODE item:crown 50\n\n"
        "Последнее число — максимум активаций.",
        reply_markup=cancel_keyboard,
    )


async def admin_promo_create(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    parts = text.strip().split()
    if len(parts) < 2:
        await update.message.reply_text("❌ Формат: CODE 1000 50 или CODE item:crown 50", reply_markup=cancel_keyboard)
        return
    code = parts[0].upper()
    reward = parts[1]
    max_uses = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 100
    payload = {"code": code, "maxUses": max_uses}
    if reward.lower().startswith("item:"):
        payload["itemId"] = reward.split(":", 1)[1]
    elif reward.replace(" ", "").isdigit():
        payload["amount"] = int(reward)
    else:
        await update.message.reply_text("❌ Награда должна быть числом или item:id.", reply_markup=cancel_keyboard)
        return
    try:
        response, data = await api_post("/admin/promo", payload)
        clear_modes(context)
        if response.status_code != 200 or not data.get("ok"):
            if data.get("code") == "daily_only_item":
                msg = "❌ Эксклюзив «только ежедневка» нельзя выдавать промокодом."
            else:
                msg = "❌ Не удалось создать промокод."
            await update.message.reply_text(msg, reply_markup=get_main_keyboard(update.effective_user.id))
            return
        await update.message.reply_text(
            f"✅ Промокод {code} создан. Лимит: {max_uses}.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
    except Exception:
        logging.exception("Ошибка создания промокода")
        clear_modes(context)
        await update.message.reply_text("❌ Сервис промокодов недоступен.", reply_markup=get_main_keyboard(update.effective_user.id))


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    clear_modes(context)
    try:
        response, data = await api_post("/admin/stats", {})
        if response.status_code != 200 or not data.get("ok"):
            raise RuntimeError("stats")
        event = data.get("activeEvent")
        lines = [
            "📊 Статистика бота",
            "",
            f"👥 Пользователей: {int(data.get('users') or 0)}",
            f"🪙 Коинов в кошельках: {int(data.get('totalCoins') or 0):,}".replace(",", " "),
            f"🏦 Коинов в банке: {int(data.get('bankCoins') or 0):,}".replace(",", " "),
            f"🛍 Всего предметов у пользователей: {int(data.get('purchases') or 0)}",
            f"🎟 Промокодов: {int(data.get('promos') or 0)}",
            f"✨ Кастомных предметов: {int(data.get('customItems') or 0)}",
            f"🎖 Кастомных титулов: {int(data.get('customTitles') or 0)}",
            f"🎉 Ивент: {event.get('name') if event else 'нет'}",
        ]
        popular = data.get("popular") or []
        if popular:
            lines.append("")
            lines.append("🔥 Популярные предметы:")
            for item in popular:
                lines.append(f"• {item.get('name')} — {int(item.get('count') or 0)}")
        await update.message.reply_text("\n".join(lines), reply_markup=admin_panel_keyboard)
    except Exception:
        logging.exception("Ошибка админ статистики")
        await update.message.reply_text("❌ Статистика недоступна.", reply_markup=admin_panel_keyboard)


async def admin_log_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    clear_modes(context)
    try:
        response, data = await api_post("/admin/log", {})
        rows = data.get("rows") or []
        lines = ["🧾 История админ-действий", ""]
        if not rows:
            lines.append("История пока пустая.")
        for row in rows[:30]:
            extra = ""
            if row.get("userId"):
                extra += f" · ID {row.get('userId')}"
            if row.get("amount") is not None:
                extra += f" · {row.get('amount')} RC"
            if row.get("itemId"):
                extra += f" · {row.get('itemId')}"
            lines.append(f"• {row.get('action')}{extra}")
        await update.message.reply_text("\n".join(lines), reply_markup=admin_panel_keyboard)
    except Exception:
        logging.exception("Ошибка админ лога")
        await update.message.reply_text("❌ История недоступна.", reply_markup=admin_panel_keyboard)


async def admin_shop_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    clear_modes(context)
    context.user_data["admin_shop_edit_waiting"] = True

    items_text = ""
    try:
        response, data = await api_post("/admin/shop/list", {})
        items = data.get("items") or []
        if items:
            rows = ["", "", "Предметы магазина:"]
            for item in items[:25]:
                rows.append(
                    f"• {item.get('id')} — {item.get('name')} — "
                    f"{int(item.get('price') or 0)} RC — "
                    f"{'hidden' if item.get('hidden') else 'show'} — "
                    f"{item.get('rarity') or 'exclusive'}"
                )
            items_text = "\n".join(rows)
    except Exception:
        pass

    await update.message.reply_text(
        "🧰 Редактор магазина\n\n"
        "Изменить: ID | цена | show/hidden | rarity\n"
        "Удалить: ID | delete\n\n"
        "Пример: ex_abc123 | 2500 | hidden | legendary"
        + items_text,
        reply_markup=cancel_keyboard,
    )


async def admin_shop_edit_apply(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    parts = [x.strip() for x in text.split("|")]
    if len(parts) < 2:
        await update.message.reply_text("❌ Формат: ID | цена | show/hidden | rarity или ID | delete", reply_markup=cancel_keyboard)
        return
    item_id = parts[0]
    if parts[1].lower() == "delete":
        payload = {"itemId": item_id, "delete": True}
    else:
        if not parts[1].replace(" ", "").isdigit():
            await update.message.reply_text("❌ Цена должна быть числом.", reply_markup=cancel_keyboard)
            return
        payload = {"itemId": item_id, "price": int(parts[1].replace(" ", ""))}
        if len(parts) > 2 and parts[2]:
            payload["hidden"] = parts[2].lower() in {"hidden", "hide", "скрыто"}
        if len(parts) > 3 and parts[3]:
            payload["rarity"] = parts[3].lower()
    try:
        response, data = await api_post("/admin/shop/edit", payload)
        clear_modes(context)
        if response.status_code != 200 or not data.get("ok"):
            await update.message.reply_text("❌ Предмет не найден или изменить его нельзя.", reply_markup=admin_panel_keyboard)
            return
        await update.message.reply_text(
            "✅ Предмет удалён." if data.get("deleted") else "✅ Предмет магазина обновлён.",
            reply_markup=admin_panel_keyboard,
        )
    except Exception:
        logging.exception("Ошибка редактора магазина")
        clear_modes(context)
        await update.message.reply_text("❌ Редактор магазина недоступен.", reply_markup=admin_panel_keyboard)


async def admin_economy_block_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    clear_modes(context)
    context.user_data["admin_economy_stage"] = "choose"
    await update.message.reply_text(
        "🚫 Выберите пользователя. Повторное нажатие снимает блокировку переводов и подарков.",
        reply_markup=admin_economy_user_keyboard,
    )


async def admin_toggle_economy_block(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    try:
        response, data = await api_post("/admin/economy-block", {"userId": target_id})
        clear_modes(context)
        if response.status_code != 200 or not data.get("ok"):
            raise RuntimeError("block")
        await update.message.reply_text(
            f"{'🚫 Экономика заблокирована' if data.get('enabled') else '✅ Блокировка экономики снята'} для ID {target_id}.",
            reply_markup=admin_panel_keyboard,
        )
    except Exception:
        logging.exception("Ошибка блокировки экономики")
        clear_modes(context)
        await update.message.reply_text("❌ Не удалось изменить блокировку.", reply_markup=admin_panel_keyboard)


async def admin_random_daily_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    clear_modes(context)
    context.user_data["admin_random_daily_waiting"] = True
    await update.message.reply_text(
        "🎲 Случайная ежедневка\n\n"
        "Формат: on | награда:шанс,награда:шанс\n"
        "Пример: on | 100:50,500:20,1000:5\n"
        "Это означает +100 RC с шансом 50%, +500 с шансом 20%, +1000 с шансом 5%.\n"
        "Чтобы выключить: off",
        reply_markup=cancel_keyboard,
    )


async def admin_random_daily_set(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    raw = text.strip().lower()
    if raw == "off":
        payload = {"enabled": False, "rewards": []}
    else:
        parts = [x.strip() for x in text.split("|")]
        if len(parts) < 2 or parts[0].lower() != "on":
            await update.message.reply_text("❌ Пример: on | 100:50,500:20,1000:5", reply_markup=cancel_keyboard)
            return
        rewards = []
        total = 0.0
        try:
            for pair in parts[1].split(","):
                coins_s, chance_s = [x.strip() for x in pair.split(":", 1)]
                coins = int(coins_s)
                chance = float(chance_s.replace(",", "."))
                if coins < 0 or chance <= 0:
                    raise ValueError
                rewards.append({"coins": coins, "chance": chance})
                total += chance
        except Exception:
            await update.message.reply_text("❌ Неверный список. Формат: 100:50,500:20", reply_markup=cancel_keyboard)
            return
        if total > 100:
            await update.message.reply_text("❌ Сумма всех шансов не может быть больше 100%.", reply_markup=cancel_keyboard)
            return
        payload = {"enabled": True, "rewards": rewards}

    try:
        response, data = await api_post("/admin/random-daily", payload)
        clear_modes(context)
        if response.status_code != 200 or not data.get("ok"):
            raise RuntimeError("random daily")
        await update.message.reply_text(
            f"✅ Случайная ежедневка: {'включена' if data.get('randomDaily', {}).get('enabled') else 'выключена'}.",
            reply_markup=admin_panel_keyboard,
        )
    except Exception:
        clear_modes(context)
        await update.message.reply_text("❌ Не удалось сохранить настройки.", reply_markup=admin_panel_keyboard)


async def admin_bundle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    clear_modes(context)
    context.user_data["admin_bundle_waiting"] = True
    await update.message.reply_text(
        "📦 Создание набора\n\n"
        "Формат: Название | цена | item1,item2,item3\n"
        "Пример: Sakura Pack | 3000 | crown,sakura_badge,bg_sakura",
        reply_markup=cancel_keyboard,
    )


async def admin_bundle_create(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    parts = [x.strip() for x in text.split("|")]
    if len(parts) < 3 or not parts[1].replace(" ", "").isdigit():
        await update.message.reply_text("❌ Формат: Название | цена | item1,item2", reply_markup=cancel_keyboard)
        return
    payload = {
        "name": parts[0],
        "price": int(parts[1].replace(" ", "")),
        "items": [x.strip() for x in parts[2].split(",") if x.strip()],
    }
    try:
        response, data = await api_post("/admin/bundle", payload)
        clear_modes(context)
        if response.status_code != 200 or not data.get("ok"):
            await update.message.reply_text("❌ Проверь ID предметов.", reply_markup=admin_panel_keyboard)
            return
        bundle = data.get("bundle") or {}
        await update.message.reply_text(
            f"✅ Набор создан: {bundle.get('name')}\n🆔 {bundle.get('id')}\n🪙 {int(bundle.get('price') or 0)} RC",
            reply_markup=admin_panel_keyboard,
        )
    except Exception:
        clear_modes(context)
        await update.message.reply_text("❌ Не удалось создать набор.", reply_markup=admin_panel_keyboard)


async def admin_season_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    clear_modes(context)
    context.user_data["admin_season_waiting"] = True
    current_text = ""

    try:
        response, data = await api_post("/admin/season/get", {})
        season = data.get("season") or {}
        if response.status_code == 200 and data.get("ok"):
            rows = [
                "",
                "",
                f"Сейчас: {season.get('name') or 'Сезон'}",
                f"ID: {season.get('id') or '-'}",
            ]
            tiers = season.get("tiers") or []
            if tiers:
                rows.append("Этапы:")
                for tier in tiers[:25]:
                    rewards = []
                    if int(tier.get("reward") or 0):
                        rewards.append(f"{int(tier.get('reward') or 0)} RC")
                    if tier.get("item"):
                        rewards.append(tier.get("item", {}).get("name") or tier.get("itemId"))
                    rows.append(
                        f"• ур. {int(tier.get('need') or 1)} = "
                        + (" + ".join(rewards) if rewards else "без награды")
                    )
            current_text = "\n".join(rows)
    except Exception:
        pass

    await update.message.reply_text(
        "🎫 Настройка сезонного пропуска\n\n"
        "Формат:\n"
        "new/edit | Название | дней | этапы\n\n"
        "Этап: уровень=награда. Этапы разделяй точкой с запятой.\n"
        "Награда может быть коинами, предметом или обоими сразу.\n\n"
        "Пример нового сезона:\n"
        "new | Sakura Season | 30 | 1=100; 3=250; 5=500+item:crown; 10=item:premium_star\n\n"
        "Чтобы изменить текущий сезон без сброса уже забранных этапов, вместо new используй edit.\n"
        "Дней 0 = без даты окончания."
        + current_text,
        reply_markup=cancel_keyboard,
    )


async def admin_season_set(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    parts = [x.strip() for x in text.split("|", 3)]
    if len(parts) < 4:
        await update.message.reply_text(
            "❌ Формат: new/edit | Название | дней | 1=100; 3=250+item:crown",
            reply_markup=cancel_keyboard,
        )
        return

    mode = parts[0].lower()
    if mode not in {"new", "edit"}:
        await update.message.reply_text("❌ Первый параметр только new или edit.", reply_markup=cancel_keyboard)
        return

    name = parts[1][:60]
    days_raw = parts[2].replace(" ", "")
    if not days_raw.isdigit():
        await update.message.reply_text("❌ Количество дней должно быть числом.", reply_markup=cancel_keyboard)
        return

    tiers = []
    try:
        for raw_tier in [x.strip() for x in parts[3].split(";") if x.strip()]:
            need_s, reward_s = [x.strip() for x in raw_tier.split("=", 1)]
            need = int(need_s)
            if need < 1:
                raise ValueError

            coins = 0
            item_id = None
            for reward_part in [x.strip() for x in reward_s.split("+") if x.strip()]:
                if reward_part.lower().startswith("item:"):
                    item_id = reward_part.split(":", 1)[1].strip().lower()
                else:
                    coins += int(reward_part.replace(" ", ""))

            if coins < 0 or (coins == 0 and not item_id):
                raise ValueError

            tiers.append({
                "need": need,
                "reward": coins,
                "itemId": item_id,
            })
    except Exception:
        await update.message.reply_text(
            "❌ Ошибка в этапах. Пример: 1=100; 5=500+item:crown; 10=item:premium_star",
            reply_markup=cancel_keyboard,
        )
        return

    if not tiers:
        await update.message.reply_text("❌ Добавь хотя бы один этап.", reply_markup=cancel_keyboard)
        return

    tiers.sort(key=lambda x: x["need"])

    try:
        response, data = await api_post(
            "/admin/season",
            {
                "mode": mode,
                "name": name,
                "days": int(days_raw),
                "tiers": tiers,
            },
        )
        if response.status_code != 200 or not data.get("ok"):
            error = data.get("error") or "неизвестная ошибка"
            item_id = data.get("itemId")
            if item_id:
                error += f" ({item_id})"
            await update.message.reply_text(
                f"❌ Не удалось сохранить сезон: {error}",
                reply_markup=cancel_keyboard,
            )
            return

        clear_modes(context)
        season = data.get("season") or {}
        lines = [
            "✅ Сезонный пропуск сохранён.",
            f"🎫 {season.get('name')}",
            f"🆔 {season.get('id')}",
            f"🎁 Этапов: {len(season.get('tiers') or [])}",
        ]
        if mode == "new":
            lines.append("🔄 Это новый сезон — награды этапов можно получать заново.")
        else:
            lines.append("✏️ Текущий сезон изменён без нового ID.")

        await update.message.reply_text("\n".join(lines), reply_markup=admin_panel_keyboard)
    except Exception:
        logging.exception("Ошибка настройки сезона")
        clear_modes(context)
        await update.message.reply_text("❌ Сервис сезона недоступен.", reply_markup=admin_panel_keyboard)


QUEST_TYPE_ALIASES = {
    "messages": "messages",
    "message": "messages",
    "сообщения": "messages",
    "сообщение": "messages",
    "daily": "daily",
    "ежедневка": "daily",
    "ежедневная": "daily",
    "spent": "spent",
    "потратить": "spent",
    "траты": "spent",
    "cases": "cases",
    "кейсы": "cases",
    "кейс": "cases",
    "purchases": "purchases",
    "покупки": "purchases",
    "покупка": "purchases",
    "transferred": "transferred",
    "переводы": "transferred",
    "перевод": "transferred",
}


async def admin_quests_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    clear_modes(context)
    context.user_data["admin_quests_waiting"] = True
    current_text = ""

    try:
        response, data = await api_post("/admin/quests/get", {})
        quests = data.get("quests") or []
        if response.status_code == 200 and data.get("ok") and quests:
            rows = ["", "", "Текущие задания:"]
            for q in quests[:30]:
                rows.append(
                    f"• {q.get('id')} | {q.get('type')} | "
                    f"{int(q.get('target') or 0)} | {int(q.get('reward') or 0)} RC | {q.get('name')}"
                )
            current_text = "\n".join(rows)
    except Exception:
        pass

    await update.message.reply_text(
        "🎯 Редактор заданий на день\n\n"
        "Добавить:\n"
        "add | тип | цель | награда_RC | название\n"
        "Пример: add | messages | 5 | 200 | Отправить 5 сообщений\n\n"
        "Изменить:\n"
        "edit | ID | тип | цель | награда_RC | название\n\n"
        "Удалить:\n"
        "delete | ID\n\n"
        "Типы: messages, daily, spent, cases, purchases, transferred.\n"
        "Можно также писать: сообщения, ежедневка, потратить, кейсы, покупки, переводы."
        + current_text,
        reply_markup=cancel_keyboard,
    )


async def admin_quests_apply(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    parts = [x.strip() for x in text.split("|")]
    if not parts:
        return

    action = parts[0].lower()

    if action == "delete":
        if len(parts) < 2:
            await update.message.reply_text("❌ Формат: delete | ID", reply_markup=cancel_keyboard)
            return
        payload = {"action": "delete", "id": parts[1]}

    elif action == "add":
        if len(parts) < 5:
            await update.message.reply_text(
                "❌ Формат: add | тип | цель | награда_RC | название",
                reply_markup=cancel_keyboard,
            )
            return
        quest_type = QUEST_TYPE_ALIASES.get(parts[1].lower())
        if not quest_type or not parts[2].replace(" ", "").isdigit() or not parts[3].replace(" ", "").isdigit():
            await update.message.reply_text("❌ Проверь тип, цель и награду.", reply_markup=cancel_keyboard)
            return
        payload = {
            "action": "add",
            "type": quest_type,
            "target": int(parts[2].replace(" ", "")),
            "reward": int(parts[3].replace(" ", "")),
            "name": "|".join(parts[4:]).strip(),
        }

    elif action == "edit":
        if len(parts) < 6:
            await update.message.reply_text(
                "❌ Формат: edit | ID | тип | цель | награда_RC | название",
                reply_markup=cancel_keyboard,
            )
            return
        quest_type = QUEST_TYPE_ALIASES.get(parts[2].lower())
        if not quest_type or not parts[3].replace(" ", "").isdigit() or not parts[4].replace(" ", "").isdigit():
            await update.message.reply_text("❌ Проверь тип, цель и награду.", reply_markup=cancel_keyboard)
            return
        payload = {
            "action": "edit",
            "id": parts[1],
            "type": quest_type,
            "target": int(parts[3].replace(" ", "")),
            "reward": int(parts[4].replace(" ", "")),
            "name": "|".join(parts[5:]).strip(),
        }

    else:
        await update.message.reply_text(
            "❌ Используй add, edit или delete.",
            reply_markup=cancel_keyboard,
        )
        return

    try:
        response, data = await api_post("/admin/quests", payload)
        if response.status_code != 200 or not data.get("ok"):
            await update.message.reply_text(
                f"❌ Не удалось изменить задания: {data.get('error') or 'ошибка'}",
                reply_markup=cancel_keyboard,
            )
            return

        clear_modes(context)
        if action == "delete":
            result = "🗑 Задание удалено."
        elif action == "add":
            q = data.get("quest") or {}
            result = f"✅ Задание создано. ID: {q.get('id')}"
        else:
            q = data.get("quest") or {}
            result = f"✅ Задание {q.get('id')} обновлено."

        await update.message.reply_text(result, reply_markup=admin_panel_keyboard)
    except Exception:
        logging.exception("Ошибка редактора заданий")
        clear_modes(context)
        await update.message.reply_text("❌ Редактор заданий недоступен.", reply_markup=admin_panel_keyboard)


async def admin_event_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    clear_modes(context)
    context.user_data["admin_event_waiting"] = True
    await update.message.reply_text(
        "🎉 Настройка ивента\n\n"
        "Включить: on | Название | дней | бонус_к_ежедневке\n"
        "Пример: on | Sakura Week | 7 | 250\n"
        "Выключить: off",
        reply_markup=cancel_keyboard,
    )


async def admin_event_set(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    raw = text.strip()
    if raw.lower() == "off":
        payload = {"active": False}
    else:
        parts = [x.strip() for x in raw.split("|")]
        if len(parts) < 4 or parts[0].lower() != "on" or not parts[2].isdigit() or not parts[3].replace(" ", "").isdigit():
            await update.message.reply_text("❌ Пример: on | Sakura Week | 7 | 250", reply_markup=cancel_keyboard)
            return
        payload = {
            "active": True,
            "name": parts[1],
            "days": int(parts[2]),
            "dailyBonus": int(parts[3].replace(" ", "")),
        }
    try:
        response, data = await api_post("/admin/event", payload)
        clear_modes(context)
        if response.status_code != 200 or not data.get("ok"):
            raise RuntimeError("event")
        event = data.get("event") or {}
        await update.message.reply_text(
            f"✅ Ивент {'включён: ' + str(event.get('name')) if event.get('active') else 'выключен'}.",
            reply_markup=admin_panel_keyboard,
        )
    except Exception:
        clear_modes(context)
        await update.message.reply_text("❌ Не удалось изменить ивент.", reply_markup=admin_panel_keyboard)


async def admin_daily_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    clear_modes(context)
    context.user_data["admin_daily_waiting"] = True

    current_text = ""
    try:
        response, data = await api_post("/admin/daily/get", {})
        if response.status_code == 200 and data.get("ok"):
            schedule = data.get("schedule") or []
            if schedule:
                rows = ["", "", "📅 Уже настроено:"]
                for entry in schedule[:20]:
                    item = entry.get("item")
                    reward = f"{int(entry.get('coins') or 0):,} RC".replace(",", " ")
                    if item:
                        reward += f" + {item.get('name')}"
                    bonus = " + бонус серии" if entry.get("streakBonus", True) else ""
                    rows.append(f"• День {int(entry.get('day') or 0)}: {reward}{bonus}")
                if len(schedule) > 20:
                    rows.append(f"… ещё {len(schedule) - 20}")
                current_text = "\n".join(rows)
    except Exception:
        pass

    await update.message.reply_text(
        "🎁 Настройка ежедневной награды по дням\n\n"
        "Формат: коины | ID предмета | on/off | день | secret/normal\n\n"
        "4 число — день серии, на который ставится награда.\n"
        "5 часть необязательная: secret скрывает награду в календаре.\n"
        "Например:\n"
        "250 | ex_mufvp8asrs | on | 1 | normal\n"
        "500 |  | off | 2 | secret\n"
        "1000 | crown | on | 7 | normal\n\n"
        "1 — коины. 2 — ID предмета. 3 — бонус серии on/off. 4 — номер дня. 5 — secret/normal."
        + current_text,
        reply_markup=cancel_keyboard,
    )

async def admin_daily_set(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    if update.effective_user.id != ADMIN_ID:
        clear_modes(context)
        return

    parts = [part.strip() for part in text.split("|")]
    if len(parts) < 4:
        await update.message.reply_text(
            "❌ Нужно 4 части. Например: 250 | ex_mufvp8asrs | on | 1",
            reply_markup=cancel_keyboard,
        )
        return

    coins_raw = parts[0].replace(" ", "")
    item_id = parts[1].strip().lower() if parts[1].strip() else None
    bonus_raw = parts[2].strip().lower()
    day_raw = parts[3].replace(" ", "")
    surprise_raw = parts[4].strip().lower() if len(parts) > 4 else "normal"
    surprise = surprise_raw in {"secret", "сюрприз", "скрыто", "hidden"}

    if not coins_raw.isdigit():
        await update.message.reply_text(
            "❌ Первый параметр должен быть количеством коинов.",
            reply_markup=cancel_keyboard,
        )
        return

    if bonus_raw in {"off", "0", "нет", "false"}:
        streak_bonus = False
    elif bonus_raw in {"on", "1", "да", "true"}:
        streak_bonus = True
    else:
        await update.message.reply_text(
            "❌ Третий параметр только on или off.",
            reply_markup=cancel_keyboard,
        )
        return

    if not day_raw.isdigit():
        await update.message.reply_text(
            "❌ Последний параметр должен быть номером дня.",
            reply_markup=cancel_keyboard,
        )
        return

    day = int(day_raw)
    if day < 1 or day > 3650:
        await update.message.reply_text(
            "❌ День должен быть от 1 до 3650.",
            reply_markup=cancel_keyboard,
        )
        return

    coins = int(coins_raw)

    try:
        response, data = await api_post(
            "/admin/daily",
            {
                "coins": coins,
                "itemId": item_id,
                "streakBonus": streak_bonus,
                "day": day,
                "surprise": surprise,
            },
        )
        if response.status_code != 200 or not data.get("ok"):
            await update.message.reply_text(
                "❌ Не удалось сохранить награду. Проверь ID предмета и номер дня.",
                reply_markup=cancel_keyboard,
            )
            return

        clear_modes(context)
        daily = data.get("daily") or {}
        item = data.get("item")
        lines = [
            f"✅ Награда на день {int(data.get('day') or day)} сохранена.",
            f"🪙 Коины: {int(daily.get('coins') or 0):,}".replace(",", " "),
            f"📅 Бонус серии: {'вкл' if daily.get('streakBonus', True) else 'выкл'}",
            f"🎁 В календаре: {'СЮРПРИЗ' if daily.get('surprise') else 'показана'}",
        ]
        if item:
            lines.append(f"🎁 Предмет: {item.get('name')} ({item.get('id')})")
        await update.message.reply_text(
            "\n".join(lines),
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
    except Exception:
        logging.exception("Ошибка настройки ежедневной награды")
        clear_modes(context)
        await update.message.reply_text(
            "❌ Сервис наград недоступен.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )

async def admin_promos_delete_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    clear_modes(context)
    try:
        response, data = await api_post("/admin/promos", {})
        if response.status_code != 200 or not data.get("ok"):
            await update.message.reply_text("❌ Не удалось получить промокоды.", reply_markup=get_main_keyboard(update.effective_user.id))
            return

        promos = data.get("promos") or []
        if not promos:
            await update.message.reply_text("🗑 Активных промокодов нет.", reply_markup=get_main_keyboard(update.effective_user.id))
            return

        rows = []
        for promo in promos[:50]:
            code = promo.get("code")
            uses = int(promo.get("uses") or 0)
            max_uses = int(promo.get("maxUses") or 0)
            reward = f"{int(promo.get('amount') or 0):,} RC".replace(",", " ") if promo.get("amount") else f"item:{promo.get('itemId')}"
            rows.append([
                InlineKeyboardButton(
                    f"🗑 {code} · {reward} · {uses}/{max_uses}",
                    callback_data=f"promo_del:{code}",
                )
            ])

        await update.message.reply_text(
            "🗑 Выберите промокод для удаления:",
            reply_markup=InlineKeyboardMarkup(rows),
        )
    except Exception:
        logging.exception("Ошибка списка промокодов")
        await update.message.reply_text("❌ Сервис промокодов недоступен.", reply_markup=get_main_keyboard(update.effective_user.id))


async def handle_admin_promo_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or query.from_user.id != ADMIN_ID:
        if query:
            await query.answer("⛔ Только для администратора.", show_alert=True)
        return

    code = query.data.split(":", 1)[1]
    try:
        response, data = await api_post("/admin/promo/delete", {"code": code})
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Не удалось удалить промокод.", show_alert=True)
            return
        await query.answer("🗑 Промокод удалён", show_alert=True)
        await query.edit_message_text(f"✅ Промокод {code} удалён.")
    except Exception:
        logging.exception("Ошибка удаления промокода")
        await query.answer("❌ Сервис промокодов недоступен.", show_alert=True)


async def admin_title_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    clear_modes(context)
    context.user_data["admin_title_waiting"] = True
    await update.message.reply_text(
        "🎖 Создание титула\n\n"
        "Формат:\n"
        "Название | цена | эмодзи | тип | редкость | видимость\n\n"
        "Тип: обычный или premium.\n"
        "Редкость: common/rare/epic/legendary/exclusive.\n"
        "Видимость: show или hidden.\n\n"
        "Пример:\n"
        "Король | 2500 | 👑 | обычный | legendary | show",
        reply_markup=cancel_keyboard,
    )


async def admin_title_create(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    if update.effective_user.id != ADMIN_ID:
        clear_modes(context)
        return

    parts = [part.strip() for part in text.split("|")]
    if len(parts) < 2:
        await update.message.reply_text(
            "❌ Формат: Название | цена | эмодзи | обычный/premium | редкость | show/hidden",
            reply_markup=cancel_keyboard,
        )
        return

    name = parts[0]
    price_raw = parts[1].replace(" ", "")
    emoji = parts[2] if len(parts) > 2 and parts[2] else "🎖"
    kind = parts[3].lower() if len(parts) > 3 else "обычный"
    rarity = parts[4].lower() if len(parts) > 4 and parts[4] else "rare"
    visibility = parts[5].lower() if len(parts) > 5 and parts[5] else "show"

    if not price_raw.isdigit() or int(price_raw) < 1:
        await update.message.reply_text(
            "❌ Цена должна быть целым числом от 1 RC.",
            reply_markup=cancel_keyboard,
        )
        return

    payload = {
        "name": name,
        "price": int(price_raw),
        "emoji": emoji,
        "premiumOnly": kind in {"premium", "премиум", "vip"},
        "rarity": rarity,
        "hidden": visibility in {"hidden", "hide", "скрыто"},
    }

    try:
        response, data = await api_post("/admin/title", payload)
        if response.status_code != 200 or not data.get("ok"):
            await update.message.reply_text(
                "❌ Не удалось создать титул.",
                reply_markup=cancel_keyboard,
            )
            return

        clear_modes(context)
        item = data.get("item") or {}
        await update.message.reply_text(
            (
                "✅ Титул создан!\n"
                f"🎖 {item.get('titleName') or item.get('name')}\n"
                f"🪙 Цена: {int(item.get('price') or 0):,} RC\n"
                f"🆔 ID: {item.get('id')}\n"
                f"💠 Редкость: {item.get('rarity')}\n"
                f"🔒 Premium: {'да' if item.get('premiumOnly') else 'нет'}\n"
                f"👁 Видимость: {'скрыт' if item.get('hidden') else 'показан'}"
            ).replace(",", " "),
            reply_markup=admin_panel_keyboard,
        )
    except Exception:
        logging.exception("Ошибка создания титула")
        clear_modes(context)
        await update.message.reply_text(
            "❌ Сервис титулов недоступен.",
            reply_markup=admin_panel_keyboard,
        )


async def admin_exclusive_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    clear_modes(context)
    context.user_data["admin_exclusive_waiting"] = True
    await update.message.reply_text(
        "✨ Создание кастомного эксклюзива\n\n"
        "Формат:\n"
        "Название | цена | эмодзи | тип | дней | редкость | видимость\n\n"
        "Тип: premium, обычный, ежедневка или фон.\n"
        "Редкость: common/rare/epic/legendary/exclusive.\n"
        "Видимость: show или hidden.\n"
        "Дней: 0 = навсегда.\n\n"
        "Примеры:\n"
        "Молния RNMD | 2500 | ⚡ | premium | 7 | epic | show\n"
        "Секрет | 3000 | 👻 | обычный | 0 | legendary | hidden\n"
        "Sakura Sky | 1800 | 🌸 | фон | 0 | epic | show",
        reply_markup=cancel_keyboard,
    )


async def admin_exclusive_create(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    if update.effective_user.id != ADMIN_ID:
        clear_modes(context)
        return

    parts = [part.strip() for part in text.split("|")]
    if len(parts) < 2:
        await update.message.reply_text(
            "❌ Формат: Название | цена | эмодзи | premium/обычный | дней",
            reply_markup=cancel_keyboard,
        )
        return

    name = parts[0]
    price_raw = parts[1].replace(" ", "")
    emoji = parts[2] if len(parts) > 2 and parts[2] else "✨"
    kind = parts[3].lower() if len(parts) > 3 else "обычный"
    days_raw = parts[4].replace(" ", "") if len(parts) > 4 else "0"
    rarity = parts[5].strip().lower() if len(parts) > 5 and parts[5].strip() else "exclusive"
    visibility = parts[6].strip().lower() if len(parts) > 6 and parts[6].strip() else "show"
    daily_only = kind in {"ежедневка", "daily", "daily_only", "ежедневная"}
    background_kind = kind in {"фон", "background", "bg"}

    if not price_raw.isdigit() or not days_raw.isdigit():
        await update.message.reply_text(
            "❌ Цена и количество дней должны быть числами.",
            reply_markup=cancel_keyboard,
        )
        return

    price = int(price_raw)
    if price < 1 and not daily_only:
        await update.message.reply_text(
            "❌ Для обычного/Premium эксклюзива цена должна быть от 1 RC. Для типа «ежедневка» можно поставить 0.",
            reply_markup=cancel_keyboard,
        )
        return

    payload = {
        "name": name,
        "price": price,
        "emoji": emoji,
        "premiumOnly": (kind in {"premium", "премиум", "vip"}) and not daily_only,
        "dailyOnly": daily_only,
        "kind": "background" if background_kind else "decoration",
        "rarity": rarity,
        "hidden": visibility in {"hidden", "скрыто", "hide"},
        "days": int(days_raw),
    }

    try:
        response, data = await api_post("/admin/exclusive", payload)
        if response.status_code != 200 or not data.get("ok"):
            await update.message.reply_text("❌ Не удалось создать эксклюзив.", reply_markup=cancel_keyboard)
            return

        clear_modes(context)
        item = data.get("item") or {}
        until = item.get("availableUntil")
        lines = [
            "✅ Эксклюзив создан!",
            f"✨ {item.get('name')}",
        ]
        if item.get("dailyOnly"):
            lines.append("🎁 Получение: только ежедневная награда")
        else:
            lines.append(f"🪙 Цена: {int(item.get('price') or 0):,} RC".replace(",", " "))
            lines.append(f"🔒 Premium: {'да' if item.get('premiumOnly') else 'нет'}")
        lines.extend([
            f"🆔 ID: {item.get('id')}",
            f"💠 Редкость: {item.get('rarity') or 'exclusive'}",
            f"👁 Видимость: {'скрыт' if item.get('hidden') else 'показан'}",
            f"🖼 Тип: {'фон профиля' if item.get('kind') == 'background' else 'украшение'}",
            f"⏳ Срок: {'до ' + until if until else 'навсегда'}",
            "",
        ])
        if item.get("dailyOnly"):
            lines.append("Вставь этот ID в «🎁 Настроить ежедневку». В магазине его не будет.")
        else:
            lines.append("Этот ID можно использовать в промокодах и ежедневной награде.")
        await update.message.reply_text(
            "\n".join(lines),
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
    except Exception:
        logging.exception("Ошибка создания эксклюзива")
        clear_modes(context)
        await update.message.reply_text(
            "❌ Сервис эксклюзивов недоступен.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )


async def top_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⭐ Уровень", callback_data="top:level"),
            InlineKeyboardButton("⚡ XP", callback_data="top:xp"),
        ],
        [
            InlineKeyboardButton("🪙 Коины", callback_data="top:coins"),
            InlineKeyboardButton("✨ Коллекция", callback_data="top:collection"),
        ],
        [
            InlineKeyboardButton("❤️ Лайки", callback_data="top:likes"),
            InlineKeyboardButton("📅 Серия", callback_data="top:streak"),
        ],
    ])
    await update.message.reply_text("🏆 Выберите рейтинг:", reply_markup=keyboard)


async def handle_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    kind = query.data.split(":", 1)[1]
    await query.answer()
    try:
        response, data = await api_post("/leaderboard", {"type": kind})
        if response.status_code != 200 or not data.get("ok"):
            await query.edit_message_text("❌ Рейтинг недоступен.")
            return
        labels = {
            "level": "⭐ По уровню",
            "xp": "⚡ По XP",
            "coins": "🪙 По коинам",
            "collection": "✨ По коллекции",
            "likes": "❤️ По лайкам",
            "streak": "📅 По серии входов",
        }
        lines = [f"🏆 {labels.get(kind, 'Топ')}", ""]
        for i, row in enumerate(data.get("rows") or [], 1):
            who = f"@{row.get('username')}" if row.get("username") else (row.get("displayName") or f"ID {row.get('userId')}")
            value_map = {
                "level": row.get("level"),
                "xp": row.get("xp"),
                "coins": row.get("balance"),
                "collection": row.get("collection"),
                "likes": row.get("likes"),
                "streak": row.get("streak"),
            }
            value = value_map.get(kind)
            lines.append(f"{i}. {who} — {value}")
        await query.edit_message_text("\n".join(lines))
    except Exception:
        logging.exception("Ошибка рейтинга")
        await query.edit_message_text("❌ Рейтинг недоступен.")


async def like_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    context.user_data["like_stage"] = "choose"
    await update.message.reply_text("❤️ Выберите профиль, которому поставить лайк.", reply_markup=like_user_keyboard)


async def like_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    try:
        response, data = await api_post(
            "/like",
            {"fromUserId": update.effective_user.id, "toUserId": target_id},
        )
        clear_modes(context)
        if response.status_code != 200 or not data.get("ok"):
            code = data.get("code")
            msg = "Вы уже ставили лайк этому профилю." if code == "already_liked" else "Нельзя лайкнуть свой профиль." if code == "self_like" else "Не удалось поставить лайк."
            await update.message.reply_text(f"❌ {msg}", reply_markup=activities_keyboard)
            return
        likes = int(data.get("likes") or 0)
        await update.message.reply_text(f"❤️ Лайк поставлен! Теперь у профиля {likes} лайков.", reply_markup=activities_keyboard)
        try:
            if await notifications_enabled(target_id):
                await context.bot.send_message(chat_id=target_id, text="❤️ Ваш профиль получил новый лайк!")
        except Exception:
            pass
    except Exception:
        logging.exception("Ошибка лайка")
        clear_modes(context)
        await update.message.reply_text("❌ Лайки недоступны.", reply_markup=activities_keyboard)


async def open_case(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    try:
        response, data = await api_post("/case/open", {"userId": update.effective_user.id})
        if response.status_code != 200 or not data.get("ok"):
            if data.get("code") == "insufficient_funds":
                await update.message.reply_text(
                    f"❌ Для кейса нужно 400 RC. Не хватает {int(data.get('missing') or 0):,} RC".replace(",", " "),
                    reply_markup=activities_keyboard,
                )
            else:
                await update.message.reply_text("❌ Кейс сейчас недоступен.", reply_markup=activities_keyboard)
            return
        reward = data.get("reward") or {}
        if reward.get("type") == "item":
            reward_text = f"🎁 Выпало украшение: {reward.get('item', {}).get('name')}"
        else:
            reward_text = f"🪙 Выпало {int(reward.get('amount') or 0):,} RC".replace(",", " ")
        await update.message.reply_text(
            f"🎁 Кейс открыт за 400 RC!\n{reward_text}\n👛 Баланс: {int(data.get('balance') or 0):,} RC".replace(",", " "),
            reply_markup=activities_keyboard,
        )
    except Exception:
        logging.exception("Ошибка кейса")
        await update.message.reply_text("❌ Кейс недоступен.", reply_markup=activities_keyboard)


async def handle_shop_titles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    try:
        response, data = await fetch_shop(query.from_user.id)
        if response.status_code != 200 or not data.get("ok"):
            await query.answer("❌ Магазин титулов недоступен.", show_alert=True)
            return

        titles = [item for item in (data.get("items") or []) if item.get("category") == "titles"]
        text = "🎖 Магазин титулов\n\nКупленный титул сразу становится выбранным."
        if not titles:
            text += "\n\nАдминистратор пока не добавил титулы."

        await query.edit_message_text(
            text,
            reply_markup=shop_titles_keyboard(data.get("items") or []),
        )
    except Exception:
        logging.exception("Ошибка магазина титулов")
        await query.answer("❌ Магазин титулов недоступен.", show_alert=True)


async def handle_shop_bundles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    try:
        response, data = await fetch_shop(query.from_user.id)
        bundles = data.get("bundles") or []
        rows = []
        lines = ["📦 Наборы", ""]
        if not bundles:
            lines.append("Наборов пока нет.")
        for bundle in bundles:
            lines.append(f"• {bundle.get('name')} — {int(bundle.get('price') or 0):,} RC".replace(",", " "))
            rows.append([InlineKeyboardButton(
                f"Купить {bundle.get('name')}",
                callback_data=f"bundle_buy:{bundle.get('id')}",
            )])
        rows.append([InlineKeyboardButton("⬅️ Назад в магазин", callback_data="shop_back")])
        await query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(rows))
    except Exception:
        await query.answer("❌ Наборы недоступны.", show_alert=True)


def parse_spooky_price_request(text: str):
    match = re.search(r"/an\d{3}", text.lower())
    if not match:
        return None, None

    auction = match.group(0)
    if not re.fullmatch(r"/an(?:10[1-8]|20[1-9]|30[1-9])", auction):
        return None, "bad_auction"

    item = (text[:match.start()] + " " + text[match.end():]).strip(" -,:;")
    item = re.sub(r"\s+", " ", item).strip()

    if not item:
        return None, "no_item"

    return (item, auction), None

async def spooky_price_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_modes(context)
    context.user_data["spooky_price_waiting"] = True
    await update.message.reply_text(
        "💰 Напишите предмет и анку одним сообщением.\n\n"
        "Например: тотем /an205\n\n"
        "Разрешены: /an101–/an108, /an201–/an209, /an301–/an309.",
        reply_markup=spooky_keyboard,
    )

async def spooky_price_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    parsed, error = parse_spooky_price_request(text)

    if error == "bad_auction":
        await update.message.reply_text(
            "❌ Эта анка не разрешена.\n"
            "Можно только /an101–/an108, /an201–/an209, /an301–/an309.",
            reply_markup=spooky_keyboard,
        )
        return

    if error == "no_item" or not parsed:
        await update.message.reply_text(
            "❌ Напишите и предмет, и анку.\nНапример: тотем /an205",
            reply_markup=spooky_keyboard,
        )
        return

    item, auction = parsed

    if not SPOOKY_PRICE_API:
        await update.message.reply_text(
            "⚙️ Minecraft-бот поиска цен ещё не подключён.",
            reply_markup=spooky_keyboard,
        )
        return

    await update.message.reply_text(
        f"🔎 Ищу «{item}» на {auction} и считаю среднюю цену..."
    )

    headers = {}
    if PRICE_API_KEY:
        headers["x-api-key"] = PRICE_API_KEY

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{SPOOKY_PRICE_API}/price",
                json={"item": item, "auction": auction},
                headers=headers,
            )

        data = response.json()

        if response.status_code != 200 or not data.get("ok"):
            error_text = data.get("error")
            if not error_text:
                error_text = f"HTTP {response.status_code}"
            await update.message.reply_text(
                f"❌ Не удалось проверить цены: {error_text}",
                reply_markup=spooky_keyboard,
            )
            return

        count = int(data.get("count") or 0)
        if count == 0:
            await update.message.reply_text(
                f"🔎 Предмет: {item}\n"
                f"Анка: {auction}\n\n"
                "Ничего с ценой не найдено.",
                reply_markup=spooky_keyboard,
            )
            return

        def money(value):
            return f"{int(value):,}".replace(",", " ")

        collectors = int(data.get("collectors") or 0)
        age_seconds = int(data.get("ageSeconds") or 0)
        age_minutes = max(0, age_seconds // 60)
        source_auction = data.get("sourceAuction") or auction
        fallback = bool(data.get("fallback"))

        fallback_text = ""
        if fallback and source_auction != auction:
            fallback_text = (
                f"⚠️ На {auction} данных нет. "
                f"Использую цену с {source_auction}.\n"
            )

        min_price = int(data["min"])
        avg_price = int(data["average"])
        max_price = int(data["max"])

        if min_price == max_price:
            price_text = f"💵 Цена: {money(avg_price)}"
        else:
            price_text = (
                f"📉 Минимум: {money(min_price)}\n"
                f"📊 Средняя: {money(avg_price)}\n"
                f"📈 Максимум: {money(max_price)}"
            )

        await update.message.reply_text(
            f"💰 Предмет: {item}\n"
            f"📦 Запрошенная анка: {auction}\n"
            f"{fallback_text}"
            f"🔎 Найдено цен: {count}\n"
            f"👥 Источников: {collectors}\n"
            f"🕒 Обновлено: {age_minutes} мин назад\n\n"
            f"{price_text}",
            reply_markup=spooky_keyboard,
        )

    except Exception:
        logging.exception("Ошибка запроса цены Spooky Time")
        await update.message.reply_text(
            "❌ Minecraft-бот сейчас не отвечает. Попробуйте чуть позже.",
            reply_markup=spooky_keyboard,
        )

    context.user_data["spooky_price_waiting"] = False

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

    premium = await user_has_premium(user_id)

    if premium:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("15 мин", callback_data="dnd_15"),
                    InlineKeyboardButton("30 мин", callback_data="dnd_30"),
                    InlineKeyboardButton("1 час", callback_data="dnd_60"),
                ],
                [
                    InlineKeyboardButton("⭐ 1 час 30 мин", callback_data="dnd_90"),
                ],
            ]
        )
        info_text = (
            "🔕 На сколько включить «Не беспокоить»?\n\n"
            "⭐ Premium: максимум — 1 час 30 минут. "
            "После окончания перезарядка 25 минут."
        )
    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("15 мин", callback_data="dnd_15"),
                    InlineKeyboardButton("30 мин", callback_data="dnd_30"),
                    InlineKeyboardButton("1 час", callback_data="dnd_60"),
                ]
            ]
        )
        info_text = (
            "🔕 На сколько включить «Не беспокоить»?\n\n"
            "Максимум — 1 час. После окончания перезарядка 30 минут."
        )

    await update.message.reply_text(
        info_text,
        reply_markup=keyboard,
    )

async def dnd_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    status, remaining = get_dnd_status(context.application, user_id)

    if status == "active":
        premium = await user_has_premium(user_id)
        cooldown_minutes = 25 if premium else 30

        now = time.time()
        get_dnd_map(context.application)[user_id] = {
            "active_until": 0,
            "cooldown_until": now + cooldown_minutes * 60,
        }
        await update.message.reply_text(
            f"🔔 «Не беспокоить» отключён. Перезарядка — {cooldown_minutes} минут.",
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

async def admin_coins_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(
            "⛔ Эта кнопка доступна только администратору.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    clear_modes(context)
    context.user_data["admin_coins_stage"] = "choose"

    await update.message.reply_text(
        "🪙 Выберите пользователя, которому нужно выдать Random Coins.",
        reply_markup=admin_coins_keyboard,
    )


async def admin_coins_choose_amount(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    if update.effective_user.id != ADMIN_ID:
        return

    context.user_data["admin_coins_stage"] = "amount"
    context.user_data["admin_coins_target_id"] = target_id

    await update.message.reply_text(
        f"🪙 Сколько Random Coins выдать пользователю {target_id}?\n"
        "Напишите целое число от 1 до 1 000 000 000.",
        reply_markup=cancel_keyboard,
    )


async def admin_grant_coins(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    if update.effective_user.id != ADMIN_ID:
        clear_modes(context)
        return

    target_id = context.user_data.get("admin_coins_target_id")
    if not target_id:
        clear_modes(context)
        await update.message.reply_text(
            "❌ Сначала выберите пользователя.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    raw = text.replace(" ", "").replace(",", "")
    if not raw.isdigit():
        await update.message.reply_text(
            "❌ Напишите только число. Например: 1000",
            reply_markup=cancel_keyboard,
        )
        return

    amount = int(raw)
    if amount < 1 or amount > 1_000_000_000:
        await update.message.reply_text(
            "❌ Можно выдать от 1 до 1 000 000 000 Random Coins.",
            reply_markup=cancel_keyboard,
        )
        return

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(
                f"{SPOOKY_PRICE_API}/admin/coins",
                json={"userId": target_id, "amount": amount},
                headers=shop_headers(),
            )

        data = response.json()
        if response.status_code != 200 or not data.get("ok"):
            error_text = data.get("error") or f"HTTP {response.status_code}"
            await update.message.reply_text(
                f"❌ Не удалось выдать коины: {error_text}",
                reply_markup=get_main_keyboard(update.effective_user.id),
            )
            clear_modes(context)
            return

        balance = int(data.get("balance") or 0)
        clear_modes(context)

        await update.message.reply_text(
            (
                f"✅ Выдано: {amount:,} Random Coins\n"
                f"👤 Пользователь: {target_id}\n"
                f"👛 Новый баланс: {balance:,}"
            ).replace(",", " "),
            reply_markup=get_main_keyboard(update.effective_user.id),
        )

        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=(
                    f"🪙 Администратор выдал вам {amount:,} Random Coins.\n"
                    f"👛 Баланс: {balance:,}"
                ).replace(",", " "),
            )
        except Exception:
            logging.exception("Не удалось уведомить пользователя о выдаче коинов")

    except Exception:
        logging.exception("Ошибка выдачи Random Coins")
        clear_modes(context)
        await update.message.reply_text(
            "❌ Сервис коинов сейчас недоступен.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )


async def admin_remove_coins_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(
            "⛔ Эта кнопка доступна только администратору.",
            reply_markup=get_main_keyboard(update.effective_user.id),
        )
        return

    clear_modes(context)
    context.user_data["admin_remove_coins_stage"] = "choose"

    await update.message.reply_text(
        "➖ Выберите пользователя, у которого нужно удалить Random Coins.",
        reply_markup=admin_remove_coins_keyboard,
    )


async def admin_remove_coins_choose_amount(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    if update.effective_user.id != ADMIN_ID:
        return

    context.user_data["admin_remove_coins_stage"] = "amount"
    context.user_data["admin_remove_coins_target_id"] = target_id

    await update.message.reply_text(
        f"➖ Сколько Random Coins удалить у пользователя {target_id}?\n"
        "Напишите целое число от 1 до 1 000 000 000.",
        reply_markup=cancel_keyboard,
    )


async def admin_remove_coins(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    if update.effective_user.id != ADMIN_ID:
        clear_modes(context)
        return

    target_id = context.user_data.get("admin_remove_coins_target_id")
    if not target_id:
        clear_modes(context)
        await update.message.reply_text(
            "❌ Сначала выберите пользователя.",
            reply_markup=admin_panel_keyboard,
        )
        return

    raw = text.replace(" ", "").replace(",", "")
    if not raw.isdigit():
        await update.message.reply_text(
            "❌ Напишите только число. Например: 1000",
            reply_markup=cancel_keyboard,
        )
        return

    amount = int(raw)
    if amount < 1 or amount > 1_000_000_000:
        await update.message.reply_text(
            "❌ Можно удалить от 1 до 1 000 000 000 Random Coins.",
            reply_markup=cancel_keyboard,
        )
        return

    try:
        response, data = await api_post(
            "/admin/coins/remove",
            {"userId": target_id, "amount": amount},
        )

        if response.status_code != 200 or not data.get("ok"):
            error_text = data.get("error") or f"HTTP {response.status_code}"
            clear_modes(context)
            await update.message.reply_text(
                f"❌ Не удалось удалить коины: {error_text}",
                reply_markup=admin_panel_keyboard,
            )
            return

        removed = int(data.get("removed") or 0)
        balance = int(data.get("balance") or 0)
        clear_modes(context)

        await update.message.reply_text(
            (
                f"✅ Удалено: {removed:,} Random Coins\n"
                f"👤 Пользователь: {target_id}\n"
                f"👛 Новый баланс: {balance:,}"
            ).replace(",", " "),
            reply_markup=admin_panel_keyboard,
        )

        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=(
                    f"➖ Администратор удалил у вас {removed:,} Random Coins.\n"
                    f"👛 Баланс: {balance:,}"
                ).replace(",", " "),
            )
        except Exception:
            logging.exception("Не удалось уведомить пользователя об удалении коинов")

    except Exception:
        logging.exception("Ошибка удаления Random Coins")
        clear_modes(context)
        await update.message.reply_text(
            "❌ Сервис коинов сейчас недоступен.",
            reply_markup=admin_panel_keyboard,
        )


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

    user_id = query.from_user.id
    premium = await user_has_premium(user_id)

    max_minutes = 90 if premium else 60
    cooldown_minutes = 25 if premium else 30

    if minutes == 90 and not premium:
        await query.answer(
            "⭐ 1 час 30 минут доступно только с Premium.",
            show_alert=True,
        )
        return

    minutes = min(max(minutes, 1), max_minutes)

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
        "cooldown_until": active_until + cooldown_minutes * 60,
    }

    await query.answer("Включено")
    await query.edit_message_text(
        f"🔕 «Не беспокоить» включён на {minutes} мин.\n"
        f"После окончания будет перезарядка {cooldown_minutes} минут."
    )

async def handle_users_shared(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.users_shared:
        return

    shared = update.message.users_shared.users

    if context.user_data.get("other_profile_stage") == "choose":
        if not shared:
            await update.message.reply_text(
                "❌ Пользователь не выбран.",
                reply_markup=other_profile_keyboard,
            )
            return
        await show_other_profile(update, context, shared[0])
        return

    if context.user_data.get("friends_stage") == "choose":
        if not shared:
            await update.message.reply_text("❌ Пользователь не выбран.", reply_markup=friends_user_keyboard)
            return
        await toggle_friend(update, context, shared[0].user_id)
        return

    if context.user_data.get("direct_stage") == "choose":
        if not shared:
            await update.message.reply_text("❌ Пользователь не выбран.", reply_markup=direct_user_keyboard)
            return
        await direct_choose_message(update, context, shared[0].user_id)
        return

    if context.user_data.get("trade_stage") == "choose":
        if not shared:
            await update.message.reply_text("❌ Пользователь не выбран.", reply_markup=trade_user_keyboard)
            return
        await trade_choose_partner(update, context, shared[0].user_id)
        return

    if context.user_data.get("admin_economy_stage") == "choose":
        if update.effective_user.id != ADMIN_ID:
            clear_modes(context)
            return
        if not shared:
            await update.message.reply_text("❌ Пользователь не выбран.", reply_markup=admin_economy_user_keyboard)
            return
        await admin_toggle_economy_block(update, context, shared[0].user_id)
        return

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

    if context.user_data.get("admin_coins_stage") == "choose":
        if update.effective_user.id != ADMIN_ID:
            clear_modes(context)
            return
        if not shared:
            await update.message.reply_text(
                "❌ Пользователь не выбран.",
                reply_markup=admin_coins_keyboard,
            )
            return
        await admin_coins_choose_amount(update, context, shared[0].user_id)
        return

    if context.user_data.get("admin_remove_coins_stage") == "choose":
        if update.effective_user.id != ADMIN_ID:
            clear_modes(context)
            return
        if not shared:
            await update.message.reply_text(
                "❌ Пользователь не выбран.",
                reply_markup=admin_remove_coins_keyboard,
            )
            return
        await admin_remove_coins_choose_amount(update, context, shared[0].user_id)
        return

    if context.user_data.get("transfer_stage") == "choose":
        if not shared:
            await update.message.reply_text("❌ Пользователь не выбран.", reply_markup=transfer_user_keyboard)
            return
        await transfer_choose_amount(update, context, shared[0].user_id)
        return

    if context.user_data.get("gift_stage") == "choose":
        if not shared:
            await update.message.reply_text("❌ Пользователь не выбран.", reply_markup=gift_user_keyboard)
            return
        await gift_choose_item(update, context, shared[0].user_id)
        return

    if context.user_data.get("like_stage") == "choose":
        if not shared:
            await update.message.reply_text("❌ Пользователь не выбран.", reply_markup=like_user_keyboard)
            return
        await like_profile(update, context, shared[0].user_id)
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
    await track_activity(update.effective_user)
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
        styled = await has_message_style(update.effective_user.id)
        anon_text = (
            f"✨╭─ Анонимное сообщение ─╮\n\n{text}\n\n╰────────────╯"
            if styled
            else f"📨 Анонимное сообщение\n\n{text}"
        )
        sent = await context.bot.send_message(
            chat_id=target_id,
            text=anon_text,
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
    await track_activity(update.effective_user)
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
        styled = await has_message_style(update.effective_user.id)
        reply_text = (
            f"✨╭─ Анонимный ответ ─╮\n\n{text}\n\n╰───────────╯"
            if styled
            else f"💬 Анонимный ответ\n\n{text}"
        )
        sent = await context.bot.send_message(
            chat_id=target_id,
            text=reply_text,
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

    if text == WALLET_BUTTON:
        await show_wallet(update, context)
        return

    if text == SHOP_BUTTON:
        await show_shop(update, context)
        return

    if text == PROFILE_BUTTON:
        await show_profile(update, context)
        return

    if text == OTHER_PROFILE_BUTTON:
        await other_profile_start(update, context)
        return

    if text == ACTIVITIES_BUTTON:
        await activities_section(update, context)
        return

    if text == DAILY_BUTTON:
        await claim_daily(update, context)
        return

    if text == FRIENDS_BUTTON:
        await friends_menu(update, context)
        return

    if text == DIRECT_BUTTON:
        await direct_start(update, context)
        return

    if text == ACHIEVEMENTS_BUTTON:
        await show_achievements(update, context)
        return

    if text == QUESTS_BUTTON:
        await show_quests(update, context)
        return

    if text == BANK_BUTTON:
        await bank_menu(update, context)
        return

    if text == SEASON_BUTTON:
        await show_season(update, context)
        return

    if text == CALENDAR_BUTTON:
        await show_daily_calendar(update, context)
        return

    if text == ROTATION_BUTTON:
        await show_rotation(update, context)
        return

    if text == INVENTORY_BUTTON:
        await show_inventory(update, context)
        return

    if text == TRANSFER_BUTTON:
        await transfer_start(update, context)
        return

    if text == GIFT_BUTTON:
        await gift_start(update, context)
        return

    if text == TRADE_BUTTON:
        await trade_start(update, context)
        return

    if text == SELL_BUTTON:
        await sell_menu(update, context)
        return

    if text == PROMO_BUTTON:
        await promo_start(update, context)
        return

    if text == BUNDLES_BUTTON:
        await show_bundles(update, context)
        return

    if text == TOP_BUTTON:
        await top_menu(update, context)
        return

    if text == LIKE_BUTTON:
        await like_start(update, context)
        return

    if text == HISTORY_BUTTON:
        await show_balance_history(update, context)
        return

    if text == NOTIFICATIONS_BUTTON:
        await toggle_notifications(update, context)
        return

    if text == STATUS_BUTTON:
        await status_start(update, context)
        return

    if text == EVENT_BUTTON:
        await show_event(update, context)
        return

    if text == CASE_BUTTON:
        await open_case(update, context)
        return

    if text == SPOOKY_BUTTON:
        await spooky_section(update, context)
        return

    if text == SPOOKY_PRICE_BUTTON:
        await spooky_price_start(update, context)
        return

    if text == BACK_BUTTON:
        await back_to_main(update, context)
        return

    if text == MINECRAFT_BACK_BUTTON:
        await minecraft_section(update, context)
        return

    if text == ADMIN_PANEL_BUTTON:
        await admin_panel(update, context)
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

    if text == ADMIN_COINS_BUTTON:
        await admin_coins_start(update, context)
        return

    if text == ADMIN_REMOVE_COINS_BUTTON:
        await admin_remove_coins_start(update, context)
        return

    if text == ADMIN_PROMO_BUTTON:
        await admin_promo_start(update, context)
        return

    if text == ADMIN_DAILY_BUTTON:
        await admin_daily_start(update, context)
        return

    if text == ADMIN_PROMO_DELETE_BUTTON:
        await admin_promos_delete_menu(update, context)
        return

    if text == ADMIN_EXCLUSIVE_BUTTON:
        await admin_exclusive_start(update, context)
        return

    if text == ADMIN_TITLE_BUTTON:
        await admin_title_start(update, context)
        return

    if text == ADMIN_STATS_BUTTON:
        await admin_stats(update, context)
        return

    if text == ADMIN_LOG_BUTTON:
        await admin_log_show(update, context)
        return

    if text == ADMIN_SHOP_EDIT_BUTTON:
        await admin_shop_edit_start(update, context)
        return

    if text == ADMIN_ECONOMY_BLOCK_BUTTON:
        await admin_economy_block_start(update, context)
        return

    if text == ADMIN_RANDOM_DAILY_BUTTON:
        await admin_random_daily_start(update, context)
        return

    if text == ADMIN_BUNDLE_BUTTON:
        await admin_bundle_start(update, context)
        return

    if text == ADMIN_SEASON_BUTTON:
        await admin_season_start(update, context)
        return

    if text == ADMIN_QUESTS_BUTTON:
        await admin_quests_start(update, context)
        return

    if text == ADMIN_EVENT_BUTTON:
        await admin_event_start(update, context)
        return

    if text == CANCEL_BUTTON:
        await cancel_action(update, context)
        return

    if context.user_data.get("admin_coins_stage") == "amount":
        await admin_grant_coins(update, context, text)
        return

    if context.user_data.get("admin_remove_coins_stage") == "amount":
        await admin_remove_coins(update, context, text)
        return

    if context.user_data.get("admin_promo_waiting"):
        await admin_promo_create(update, context, text)
        return

    if context.user_data.get("admin_daily_waiting"):
        await admin_daily_set(update, context, text)
        return

    if context.user_data.get("admin_exclusive_waiting"):
        await admin_exclusive_create(update, context, text)
        return

    if context.user_data.get("admin_title_waiting"):
        await admin_title_create(update, context, text)
        return

    if context.user_data.get("admin_shop_edit_waiting"):
        await admin_shop_edit_apply(update, context, text)
        return

    if context.user_data.get("admin_random_daily_waiting"):
        await admin_random_daily_set(update, context, text)
        return

    if context.user_data.get("admin_bundle_waiting"):
        await admin_bundle_create(update, context, text)
        return

    if context.user_data.get("admin_season_waiting"):
        await admin_season_set(update, context, text)
        return

    if context.user_data.get("admin_quests_waiting"):
        await admin_quests_apply(update, context, text)
        return

    if context.user_data.get("admin_event_waiting"):
        await admin_event_set(update, context, text)
        return

    if context.user_data.get("promo_waiting"):
        await promo_redeem(update, context, text)
        return

    if context.user_data.get("direct_stage") == "message":
        await direct_send(update, context, text)
        return

    if context.user_data.get("bank_stage") in {"deposit", "withdraw"}:
        await bank_amount(update, context, text)
        return

    if context.user_data.get("status_waiting"):
        await status_set(update, context, text)
        return

    if context.user_data.get("transfer_stage") == "amount":
        await transfer_send(update, context, text)
        return

    if context.user_data.get("gift_stage") == "item":
        await update.message.reply_text(
            "🎁 Выберите украшение кнопкой под сообщением или нажмите «❌ Отменить».",
            reply_markup=cancel_keyboard,
        )
        return

    if context.user_data.get("spooky_price_waiting"):
        await spooky_price_lookup(update, context, text)
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

    await track_activity(update.effective_user)

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
    app.add_handler(CallbackQueryHandler(handle_dnd_callback, pattern="^dnd_(15|30|60|90)$"))
    app.add_handler(CallbackQueryHandler(handle_admin_anon_ban_callback, pattern="^admin_anon_ban_(15|20|25|30|60)$"))
    app.add_handler(CallbackQueryHandler(handle_report_ban_callback, pattern=r"^report:ban:-?\d+:(15|20|25|30|60)$"))
    app.add_handler(CallbackQueryHandler(handle_shop_buy, pattern=r"^shop_buy:[a-z0-9_]+$"))
    app.add_handler(CallbackQueryHandler(handle_shop_items, pattern=r"^shop_items$"))
    app.add_handler(CallbackQueryHandler(handle_shop_titles, pattern=r"^shop_titles$"))
    app.add_handler(CallbackQueryHandler(handle_shop_bundles, pattern=r"^shop_bundles$"))
    app.add_handler(CallbackQueryHandler(handle_bundle_buy, pattern=r"^bundle_buy:bd_[a-z0-9]+$"))
    app.add_handler(CallbackQueryHandler(handle_quest_claim, pattern=r"^quest_claim:[a-z0-9_]+$"))
    app.add_handler(CallbackQueryHandler(handle_bank_action, pattern=r"^bank:(deposit|withdraw)$"))
    app.add_handler(CallbackQueryHandler(handle_season_claim, pattern=r"^season_claim:\d+$"))
    app.add_handler(CallbackQueryHandler(handle_sell_item, pattern=r"^sell_item:[a-z0-9_]+$"))
    app.add_handler(CallbackQueryHandler(handle_trade_give, pattern=r"^trade_give:[a-z0-9_]+$"))
    app.add_handler(CallbackQueryHandler(handle_trade_want, pattern=r"^trade_want:[a-z0-9_]+$"))
    app.add_handler(CallbackQueryHandler(handle_trade_response, pattern=r"^trade_resp:tr_[a-z0-9]+:(yes|no)$"))
    app.add_handler(CallbackQueryHandler(profile_status_callback, pattern=r"^profile_status$"))
    app.add_handler(CallbackQueryHandler(profile_background_menu, pattern=r"^profile_background$"))
    app.add_handler(CallbackQueryHandler(profile_background_set, pattern=r"^profile_bg:[a-z0-9_]+$"))
    app.add_handler(CallbackQueryHandler(handle_shop_back, pattern=r"^shop_back$"))
    app.add_handler(CallbackQueryHandler(handle_shop_owned, pattern=r"^shop_owned$"))
    app.add_handler(CallbackQueryHandler(handle_profile_decor, pattern=r"^profile_decor$"))
    app.add_handler(CallbackQueryHandler(handle_profile_colors, pattern=r"^profile_colors$"))
    app.add_handler(CallbackQueryHandler(handle_profile_color_set, pattern=r"^profile_color:(green|white|gray|black|red|purple|pink|dark_green|light_blue|blue)$"))
    app.add_handler(CallbackQueryHandler(handle_profile_toggle, pattern=r"^profile_toggle:[a-z0-9_]+$"))
    app.add_handler(CallbackQueryHandler(handle_profile_back, pattern=r"^profile_back$"))
    app.add_handler(CallbackQueryHandler(handle_profile_titles, pattern=r"^profile_titles$"))
    app.add_handler(CallbackQueryHandler(handle_profile_title_set, pattern=r"^profile_title:[a-z0-9_]+$"))
    app.add_handler(CallbackQueryHandler(handle_profile_favorite, pattern=r"^profile_favorite$"))
    app.add_handler(CallbackQueryHandler(handle_profile_favorite_set, pattern=r"^profile_fav:[a-z0-9_]+$"))
    app.add_handler(CallbackQueryHandler(handle_gift_buy, pattern=r"^gift_buy:[a-z0-9_]+$"))
    app.add_handler(CallbackQueryHandler(handle_gift_cancel, pattern=r"^gift_cancel$"))
    app.add_handler(CallbackQueryHandler(handle_top, pattern=r"^top:(level|xp|coins|collection|likes|streak)$"))
    app.add_handler(CallbackQueryHandler(handle_admin_promo_delete, pattern=r"^promo_del:[A-Z0-9_-]{3,24}$"))

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
