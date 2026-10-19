import json
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
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
SERVER_IP = "recublica.com:8000"
SERVER_VERSION = "26.1.2"
SITE_URL = "https://recublica.com/"
DISCORD_URL = "https://discord.gg/vzzfbq4JVW"
TIKTOK_URL = "https://www.tiktok.com/@recublic?lang=ru-RU"
TELEGRAM_URL = "https://t.me/recublica"

DEFAULT_LANG = "ru"
LANG_FILE = Path("languages.json")  # тут хранится язык каждого пользователя

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO
)
# httpx пишет в лог полный URL запроса вместе с токеном — глушим
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# ---------- Тексты ----------
TEXTS = {
    "ru": {
        "start": (
            f"👋 Привет! Я бот сервера <b>{SERVER_NAME}</b> — "
            "Minecraft-сервера с картой Беларуси 🇧🇾\n\n"
            "Команды:\n"
            "/connect — как подключиться\n"
            "/socials — наши соцсети и сайт\n"
            "/ru, /by — сменить язык"
        ),
        "connect": (
            f"🎮 <b>Подключение к {SERVER_NAME}</b>\n\n"
            f"IP: <code>{SERVER_IP}</code>\n"
            f"Версия: <code>{SERVER_VERSION}</code>"
        ),
        "socials": "📲 <b>Наши соцсети</b> и сайт Recublica:",
        "btn_site": "🌐 Открыть сайт",
        "btn_discord": "💬 Discord",
        "btn_tiktok": "🎵 TikTok",
        "btn_telegram": "✈️ Telegram-канал",
        "lang_set": "✅ Язык изменён на русский 🇷🇺",
        "menu_button": "Сайт",
        "cmd_start": "Начать",
        "cmd_connect": "Как подключиться",
        "cmd_socials": "Соцсети и сайт",
        "cmd_ru": "Русский язык",
        "cmd_by": "Беларуская мова",
    },
    "by": {
        "start": (
            f"👋 Прывітанне! Я бот сервера <b>{SERVER_NAME}</b> — "
            "Minecraft-сервера з картай Беларусі 🇧🇾\n\n"
            "Каманды:\n"
            "/connect — як падключыцца\n"
            "/socials — нашы сацсеткі і сайт\n"
            "/ru, /by — змяніць мову"
        ),
        "connect": (
            f"🎮 <b>Падключэнне да {SERVER_NAME}</b>\n\n"
            f"IP: <code>{SERVER_IP}</code>\n"
            f"Версія: <code>{SERVER_VERSION}</code>"
        ),
        "socials": "📲 <b>Нашы сацсеткі</b> і сайт Recublica:",
        "btn_site": "🌐 Адкрыць сайт",
        "btn_discord": "💬 Discord",
        "btn_tiktok": "🎵 TikTok",
        "btn_telegram": "✈️ Telegram-канал",
        "lang_set": "✅ Мова зменена на беларускую 🇧🇾",
        "menu_button": "Сайт",
        "cmd_start": "Пачаць",
        "cmd_connect": "Як падключыцца",
        "cmd_socials": "Сацсеткі і сайт",
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
        BotCommand("socials", tx["cmd_socials"]),
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
            [
                InlineKeyboardButton(t(user_id, "btn_tiktok"), url=TIKTOK_URL),
                InlineKeyboardButton(t(user_id, "btn_telegram"), url=TELEGRAM_URL),
            ],
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


async def socials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(
        t(uid, "socials"),
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard(uid),
    )


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



# ---------- Мини-сервер для Render (Web Service требует открытый порт) ----------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Recublica bot is running")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


def start_health_server():
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logging.info("Health-сервер запущен на порту %s", port)


# ---------- Запуск ----------
async def post_init(app: Application):
    await app.bot.set_my_commands(commands_for(DEFAULT_LANG))
    await app.bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text=TEXTS[DEFAULT_LANG]["menu_button"], web_app=WebAppInfo(url=SITE_URL)
        )
    )


def main():
    start_health_server()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("connect", connect))
    app.add_handler(CommandHandler("socials", socials))
    app.add_handler(CommandHandler("ru", cmd_ru))
    app.add_handler(CommandHandler("by", cmd_by))

    logging.info("Бот Recublica запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
