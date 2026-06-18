import logging
import os
import threading
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer

# ====== SOZLAMALAR ======
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

CARD_NUMBER = "6262 5707 8346 7618"
CARD_OWNER = "M.Gulmira"

PLANS = {
    "professional": {
        "name": "Professional ⭐",
        "price": "49 000 so'm/oy",
        "description": (
            "🌟 *Professional* — eng mashhur tarif\n\n"
            "✅ Cheksiz testlar (6 toifa)\n"
            "✅ Barcha konspektlar (30+)\n"
            "✅ O'yinlar, qo'shiqlar, mashg'ulotlar\n"
            "✅ AI Konspekt generator\n"
            "✅ Attestatsiya testlari\n"
            "✅ Portfolio yaratish\n\n"
            "💰 Narxi: *49 000 so'm/oy*"
        ),
    },
    "korporativ": {
        "name": "MTT Korporativ 🏢",
        "price": "299 000 so'm/oy",
        "description": (
            "🏢 *MTT Korporativ* — butun muassasa uchun\n\n"
            "✅ Professional + hamma narsa\n"
            "✅ 20+ tarbiyachi uchun\n"
            "✅ Admin boshqaruv paneli\n"
            "✅ Davomat tizimi (QR)\n"
            "✅ Ota-ona portali\n"
            "✅ Bola rivojlanish monitoringi\n"
            "✅ Oylik hisobotlar (PDF)\n"
            "✅ Texnik yordam (telefon)\n\n"
            "💰 Narxi: *299 000 so'm/oy*"
        ),
    },
}

PRO_LINK = "https://maktabgachahub.uz/pro"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot ishlab turibdi")

    def log_message(self, format, *args):
        pass


def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


class PaymentStates(StatesGroup):
    waiting_screenshot = State()


def main_menu_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Professional — 49 000 so'm", callback_data="plan_professional")],
        [InlineKeyboardButton(text="🏢 MTT Korporativ — 299 000 so'm", callback_data="plan_korporativ")],
    ])
    return kb


def buy_kb(plan_key: str):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Sotib olish", callback_data=f"buy_{plan_key}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_menu")],
    ])
    return kb


def confirm_kb(user_id: int):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm_{user_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}")
        ]
    ])
    return kb


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🌟 *MaktabgachaHub Premium obuna*\n\n"
        "MTT tarbiyachilari uchun professional vositalar — testlar, konspektlar, "
        "AI generator va ko'p narsa.\n\n"
        "Tarifni tanlang 👇",
        parse_mode="Markdown",
        reply_markup=main_menu_kb()
    )


@dp.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(f"Sizning chat ID'ingiz: `{message.from_user.id}`", parse_mode="Markdown")


@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🌟 *MaktabgachaHub Premium obuna*\n\nTarifni tanlang 👇",
        parse_mode="Markdown",
        reply_markup=main_menu_kb()
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("plan_"))
async def show_plan(callback: CallbackQuery):
    plan_key = callback.data.split("_", 1)[1]
    plan = PLANS[plan_key]
    await callback.message.edit_text(
        plan["description"],
        parse_mode="Markdown",
        reply_markup=buy_kb(plan_key)
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def process_buy(callback: CallbackQuery, state: FSMContext):
    plan_key = callback.data.split("_", 1)[1]
    plan = PLANS[plan_key]

    text = (
        f"💳 To'lov uchun karta:\n\n"
        f"`{CARD_NUMBER}`\n"
        f"Egasi: *{CARD_OWNER}*\n\n"
        f"Tarif: *{plan['name']}*\n"
        f"Summasi: *{plan['price']}*\n\n"
        f"To'lovni amalga oshirgandan so'ng, chek/screenshot rasmini shu yerga yuboring 👇"
    )
    await callback.message.answer(text, parse_mode="Markdown")
    await state.set_state(PaymentStates.waiting_screenshot)
    await state.update_data(plan_key=plan_key)
    await callback.answer()


@dp.message(PaymentStates.waiting_screenshot, lambda m: m.photo or m.document)
async def process_screenshot(message: Message, state: FSMContext):
    user = message.from_user
    data = await state.get_data()
    plan_key = data.get("plan_key", "professional")
    plan = PLANS[plan_key]

    caption = (
        f"🆕 Yangi to'lov so'rovi!\n\n"
        f"📦 Tarif: {plan['name']}\n"
        f"💰 Summasi: {plan['price']}\n\n"
        f"👤 Foydalanuvchi: {user.full_name}\n"
        f"🔗 Username: @{user.username if user.username else 'yoq'}\n"
        f"🆔 ID: {user.id}"
    )

    if ADMIN_ID == 0:
        await message.answer(
            "⚠️ Bot hali to'liq sozlanmagan (admin ID yo'q). Iltimos /myid buyrug'idan foydalaning va dasturchiga ID'ni yuboring."
        )
        return

    if message.photo:
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=confirm_kb(user.id))
    elif message.document:
        await bot.send_document(ADMIN_ID, message.document.file_id, caption=caption, reply_markup=confirm_kb(user.id))

    await message.answer("✅ Rahmat! To'lovingiz tekshirilmoqda, tasdiqlangandan so'ng sizga xabar beramiz.")
    await state.clear()


@dp.message(PaymentStates.waiting_screenshot)
async def wrong_content(message: Message):
    await message.answer("Iltimos, to'lov chekining rasmini (screenshot) yuboring 🖼")


@dp.callback_query(lambda c: c.data.startswith("confirm_"))
async def process_confirm(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await bot.send_message(
        user_id,
        f"🎉 To'lovingiz tasdiqlandi!\n\nPro versiyaga havola: {PRO_LINK}"
    )
    await callback.message.edit_caption(callback.message.caption + "\n\n✅ TASDIQLANDI")
    await callback.answer("Tasdiqlandi va foydalanuvchiga xabar yuborildi")


@dp.callback_query(lambda c: c.data.startswith("reject_"))
async def process_reject(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await bot.send_message(
        user_id,
        "❌ Kechirasiz, to'lovingiz tasdiqlanmadi. Iltimos qaytadan urinib ko'ring yoki dasturchi bilan bog'laning."
    )
    await callback.message.edit_caption(callback.message.caption + "\n\n❌ RAD ETILDI")
    await callback.answer("Rad etildi va foydalanuvchiga xabar yuborildi")


async def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
