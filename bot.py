import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


# ===== HEALTH SERVER =====
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot ishlayapti")

    def log_message(self, format, *args):
        return


def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"Health server port {port} da ishga tushdi")
    server.serve_forever()


# ===== COMMANDS =====
@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        "🎉 Assalomu alaykum!\n\n"
        "MaktabgachaHub Premium botiga xush kelibsiz."
    )


@dp.message(Command("ping"))
async def ping_cmd(message: Message):
    await message.answer("🏓 Pong!")


# ===== MAIN =====
async def main():
    threading.Thread(
        target=run_health_server,
        daemon=True
    ).start()

    print("Bot polling boshlandi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
