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
ADMIN_STATS_BUTTON = "📊 Статистика бота"
ADMIN_LOG_BUTTON = "🧾 История админа"
ADMIN_SHOP_EDIT_BUTTON = "🧰 Редактор магазина"
ADMIN_ECONOMY_BLOCK_BUTTON = "🚫 Блок экономики"
ADMIN_RANDOM_DAILY_BUTTON = "🎲 Случайная ежедневка"
ADMIN_BUNDLE_BUTTON = "📦 Создать набор"
ADMIN_EVENT_BUTTON = "🎉 Настроить ивент"
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
        [KeyboardButton(ADMIN_STATS_BUTTON), KeyboardButton(ADMIN_LOG_BUTTON)],
        [KeyboardButton(ADMIN_SHOP_EDIT_BUTTON), KeyboardButton(ADMIN_ECONOMY_BLOCK_BUTTON)],
        [KeyboardButton(ADMIN_RANDOM_DAILY_BUTTON), KeyboardButton(ADMIN_BUNDLE_BUTTON)],
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
    context.user_data.pop("promo_waiting", None)
    context.user_data.pop("admin_promo_waiting", None)
    context.user_data.pop("admin_daily_waiting", None)
    context.user_data.pop("admin_exclusive_waiting", None)
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
        item_already_owned = bool(data.get("itemAlreadyOwned"))
        bonus_text = f"\n🎉 Бонус за серию: +{milestone:,} RC".replace(",", " ") if milestone else ""
        item_text = ""
        if reward_item:
            item_text = f"\n🎁 Предмет: {reward_item.get('name')}"
        elif item_already_owned:
            item_text = "\nℹ️ Предмет из награды у вас уже есть."

        coins_text = f"🪙 +{reward:,} RC" if reward else "🪙 Без коинов"
        await update.message.reply_text(
            (
                f"🎁 Ежедневная награда\n"
                f"{coins_text}"
                f"{item_text}\n"
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
            for item in owned:
                lines.append(f"• {item.get('name')}")
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
        "Формат: коины | ID предмета | on/off | день\n\n"
        "Последнее число — день серии, на который ставится награда.\n"
        "Например:\n"
        "250 | ex_mufvp8asrs | on | 1\n"
        "500 |  | off | 2\n"
        "1000 | crown | on | 7\n\n"
        "1 — коины. 2 — ID предмета. 3 — бонус серии on/off. 4 — номер дня."
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


async def admin_exclusive_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    clear_modes(context)
    context.user_data["admin_exclusive_waiting"] = True
    await update.message.reply_text(
        "✨ Создание кастомного эксклюзива\n\n"
        "Формат:\n"
        "Название | цена | эмодзи | тип | дней\n\n"
        "Тип: premium, обычный или ежедневка\n"
        "Если тип «ежедневка», цена может быть 0 — такой эксклюзив нельзя купить, подарить, получить из кейса или промокода.\n"
        "Дней: 0 = навсегда\n\n"
        "Примеры:\n"
        "Молния RNMD | 2500 | ⚡ | premium | 7\n"
        "Шахед | 0 | 🛩️ | ежедневка | 14",
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
    daily_only = kind in {"ежедневка", "daily", "daily_only", "ежедневная"}

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
            InlineKeyboardButton("🪙 Коины", callback_data="top:coins"),
        ],
        [InlineKeyboardButton("✨ Коллекция", callback_data="top:collection")],
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
        labels = {"level": "⭐ По уровню", "coins": "🪙 По коинам", "collection": "✨ По коллекции"}
        lines = [f"🏆 {labels.get(kind, 'Топ')}", ""]
        for i, row in enumerate(data.get("rows") or [], 1):
            who = f"@{row.get('username')}" if row.get("username") else (row.get("displayName") or f"ID {row.get('userId')}")
            value = row.get("level") if kind == "level" else row.get("balance") if kind == "coins" else row.get("collection")
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

    if text == INVENTORY_BUTTON:
        await show_inventory(update, context)
        return

    if text == TRANSFER_BUTTON:
        await transfer_start(update, context)
        return

    if text == GIFT_BUTTON:
        await gift_start(update, context)
        return

    if text == PROMO_BUTTON:
        await promo_start(update, context)
        return

    if text == TOP_BUTTON:
        await top_menu(update, context)
        return

    if text == LIKE_BUTTON:
        await like_start(update, context)
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

    if context.user_data.get("promo_waiting"):
        await promo_redeem(update, context, text)
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
    app.add_handler(CallbackQueryHandler(handle_shop_buy, pattern=r"^shop_buy:(plus|premium|name_color|crown|star_badge|profile_frame|message_style|random_item|rnmd_badge|diamond_badge|sakura_badge|trophy|premium_gold_frame|premium_star|autumn_frame|pumpkin_badge|ex_[a-z0-9]+)$"))
    app.add_handler(CallbackQueryHandler(handle_shop_items, pattern=r"^shop_items$"))
    app.add_handler(CallbackQueryHandler(handle_shop_back, pattern=r"^shop_back$"))
    app.add_handler(CallbackQueryHandler(handle_shop_owned, pattern=r"^shop_owned$"))
    app.add_handler(CallbackQueryHandler(handle_profile_decor, pattern=r"^profile_decor$"))
    app.add_handler(CallbackQueryHandler(handle_profile_colors, pattern=r"^profile_colors$"))
    app.add_handler(CallbackQueryHandler(handle_profile_color_set, pattern=r"^profile_color:(green|white|gray|black|red|purple|pink|dark_green|light_blue|blue)$"))
    app.add_handler(CallbackQueryHandler(handle_profile_toggle, pattern=r"^profile_toggle:[a-z0-9_]+$"))
    app.add_handler(CallbackQueryHandler(handle_profile_back, pattern=r"^profile_back$"))
    app.add_handler(CallbackQueryHandler(handle_profile_titles, pattern=r"^profile_titles$"))
    app.add_handler(CallbackQueryHandler(handle_profile_title_set, pattern=r"^profile_title:[a-z_]+$"))
    app.add_handler(CallbackQueryHandler(handle_profile_favorite, pattern=r"^profile_favorite$"))
    app.add_handler(CallbackQueryHandler(handle_profile_favorite_set, pattern=r"^profile_fav:[a-z0-9_]+$"))
    app.add_handler(CallbackQueryHandler(handle_gift_buy, pattern=r"^gift_buy:[a-z0-9_]+$"))
    app.add_handler(CallbackQueryHandler(handle_gift_cancel, pattern=r"^gift_cancel$"))
    app.add_handler(CallbackQueryHandler(handle_top, pattern=r"^top:(level|coins|collection)$"))
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
