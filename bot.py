import json
import logging
import os
from pathlib import Path

from telegram import (
    BotCommand,
    BotCommandScopeChat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    Update,
    WebAppInfo,
)
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

# ---------- Настройки ----------
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВЬ_ТОКЕН_СЮДА")

SERVER_NAME = "Recublica"
SERVER_IP = "play.recublica.com"
SERVER_VERSION = "26.1.2"
SITE_URL = "https://recublica.com"
DISCORD_URL = "https://discord.gg/vzzfbq4JVW"

DEFAULT_LANG = "ru"
LANG_FILE = Path("languages.json")  # тут хранится язык каждого пользователя

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO
)

# ---------- Тексты ----------
TEXTS = {
    "ru": {
        "start": (
            f"👋 Привет! Я бот сервера <b>{SERVER_NAME}</b> — "
            "Minecraft-сервера с картой Беларуси 🇧🇾\n\n"
            "Команды:\n"
            "/connect — как подключиться\n"
            "/site — сайт сервера\n"
            "/discord — наш Discord\n"
            "/ru, /by — сменить язык"
        ),
        "connect": (
            f"🎮 <b>Подключение к {SERVER_NAME}</b>\n\n"
            f"IP: <code>{SERVER_IP}</code>\n"
            f"Версия: <code>{SERVER_VERSION}</code>"
        ),
        "site": f"🌐 Сайт сервера: {SITE_URL}",
        "discord": f"💬 Наш Discord: {DISCORD_URL}",
        "btn_site": "🌐 Открыть сайт",
        "btn_discord": "💬 Discord",
        "lang_set": "✅ Язык изменён на русский 🇷🇺",
        "menu_button": "Сайт",
        "cmd_start": "Начать",
        "cmd_connect": "Как подключиться",
        "cmd_site": "Сайт сервера",
        "cmd_discord": "Наш Discord",
        "cmd_ru": "Русский язык",
        "cmd_by": "Беларуская мова",
    },
    "by": {
        "start": (
            f"👋 Прывітанне! Я бот сервера <b>{SERVER_NAME}</b> — "
            "Minecraft-сервера з картай Беларусі 🇧🇾\n\n"
            "Каманды:\n"
            "/connect — як падключыцца\n"
            "/site — сайт сервера\n"
            "/discord — наш Discord\n"
            "/ru, /by — змяніць мову"
        ),
        "connect": (
            f"🎮 <b>Падключэнне да {SERVER_NAME}</b>\n\n"
            f"IP: <code>{SERVER_IP}</code>\n"
            f"Версія: <code>{SERVER_VERSION}</code>"
        ),
        "site": f"🌐 Сайт сервера: {SITE_URL}",
        "discord": f"💬 Наш Discord: {DISCORD_URL}",
        "btn_site": "🌐 Адкрыць сайт",
        "btn_discord": "💬 Discord",
        "lang_set": "✅ Мова зменена на беларускую 🇧🇾",
        "menu_button": "Сайт",
        "cmd_start": "Пачаць",
        "cmd_connect": "Як падключыцца",
        "cmd_site": "Сайт сервера",
        "cmd_discord": "Наш Discord",
        "cmd_ru": "Русский язык",
        "cmd_by": "Беларуская мова",
    },
}

# ---------- Хранение языка ----------
def load_langs() -> dict:
    if LANG_FILE.exists():
        try:
            return json.loads(LANG_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_langs(data: dict) -> None:
    LANG_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


LANGS = load_langs()


def get_lang(user_id: int) -> str:
    return LANGS.get(str(user_id), DEFAULT_LANG)


def t(user_id: int, key: str) -> str:
    return TEXTS[get_lang(user_id)][key]


def commands_for(lang: str) -> list[BotCommand]:
    tx = TEXTS[lang]
    return [
        BotCommand("start", tx["cmd_start"]),
        BotCommand("connect", tx["cmd_connect"]),
        BotCommand("site", tx["cmd_site"]),
        BotCommand("discord", tx["cmd_discord"]),
        BotCommand("ru", tx["cmd_ru"]),
        BotCommand("by", tx["cmd_by"]),
    ]


def main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                # Мини-приложение: сайт открывается прямо внутри Telegram
                InlineKeyboardButton(
                    t(user_id, "btn_site"), web_app=WebAppInfo(url=SITE_URL)
                )
            ],
            [InlineKeyboardButton(t(user_id, "btn_discord"), url=DISCORD_URL)],
        ]
    )


# ---------- Команды ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(
        t(uid, "start"),
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard(uid),
    )


async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(t(uid, "connect"), parse_mode=ParseMode.HTML)


async def site(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(t(uid, "btn_site"), web_app=WebAppInfo(url=SITE_URL))]]
    )
    await update.message.reply_text(t(uid, "site"), reply_markup=keyboard)


async def discord(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(t(uid, "btn_discord"), url=DISCORD_URL)]]
    )
    await update.message.reply_text(t(uid, "discord"), reply_markup=keyboard)


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    uid = update.effective_user.id
    LANGS[str(uid)] = lang
    save_langs(LANGS)

    # Меню команд и кнопка меню тоже меняются на выбранный язык
    chat_id = update.effective_chat.id
    await context.bot.set_my_commands(
        commands_for(lang), scope=BotCommandScopeChat(chat_id)
    )
    await context.bot.set_chat_menu_button(
        chat_id=chat_id,
        menu_button=MenuButtonWebApp(
            text=TEXTS[lang]["menu_button"], web_app=WebAppInfo(url=SITE_URL)
        ),
    )

    await update.message.reply_text(
        TEXTS[lang]["lang_set"], reply_markup=main_keyboard(uid)
    )


async def cmd_ru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_language(update, context, "ru")


async def cmd_by(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_language(update, context, "by")


# ---------- Запуск ----------
async def post_init(app: Application):
    await app.bot.set_my_commands(commands_for(DEFAULT_LANG))
    await app.bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text=TEXTS[DEFAULT_LANG]["menu_button"], web_app=WebAppInfo(url=SITE_URL)
        )
    )


def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("connect", connect))
    app.add_handler(CommandHandler("site", site))
    app.add_handler(CommandHandler("discord", discord))
    app.add_handler(CommandHandler("ru", cmd_ru))
    app.add_handler(CommandHandler("by", cmd_by))

    logging.info("Бот Recublica запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
