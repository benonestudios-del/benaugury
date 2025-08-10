# main.py — запуск в режиме вебхуков на Render
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# импортируем готовые bot, dp из твоего bot.py (важно: не запускать polling там!)
from bot import bot, dp  # bot = Bot(...), dp = Dispatcher()

SECRET_TOKEN = os.getenv("SECRET_TOKEN")  # обязателен
if not SECRET_TOKEN:
    raise RuntimeError("SECRET_TOKEN is required for webhook validation")

# путь обработчика на твоём сервисе
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook").rstrip("/")
PORT = int(os.getenv("PORT", "8000"))

# Render даёт внешний URL вот тут:
BASE_URL = os.getenv("RENDER_EXTERNAL_URL")
if not BASE_URL:
    # fallback — можно задать вручную в ENV, например https://your-service.onrender.com
    BASE_URL = os.getenv("WEBHOOK_BASE_URL")
if not BASE_URL:
    raise RuntimeError("RENDER_EXTERNAL_URL (или WEBHOOK_BASE_URL) не задан — нужен публичный базовый URL")

WEBHOOK_URL = f"{BASE_URL.rstrip('/')}{WEBHOOK_PATH}"

async def on_startup(app: web.Application):
    # Вешаем вебхук: Telegram будет слать апдейты на WEBHOOK_URL
    await bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token=SECRET_TOKEN,
        drop_pending_updates=True,
    )

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()

def build_app() -> web.Application:
    app = web.Application()
    app["bot"] = bot

    # Регистрируем обработчик входящих апдейтов (с проверкой секретного токена)
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=SECRET_TOKEN
    ).register(app, path=WEBHOOK_PATH)

    # Корректная житейка диспетчера внутри aiohttp-приложения
    setup_application(app, dp, bot=bot)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app

if __name__ == "__main__":
    web.run_app(build_app(), host="0.0.0.0", port=PORT)
