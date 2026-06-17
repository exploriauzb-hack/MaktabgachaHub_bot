import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

# ====== SOZLAMALAR ======
# Token va Admin ID endi Render'dagi "Environment Variables" dan o'qiladi.
# Lokal sinash uchun pastdagi qatorlarga vaqtincha o'z qiymatlaringizni yozishingiz mumkin.
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Admin ID - hozircha 0, /myid orqali o'z ID'ingizni bilib, Render'da ADMIN_ID qiymatini kiritasiz
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

CARD_NUMBER = "6262 5707 8346 7618"
CARD_OWNER = "M.Gulmira"

PRO_PRICE = "29 000 so'm"  # narxni o'zingiz moslang
PRO_DESCRIPTION = (
    "🌟 *MaktabgachaHub PRO*\n\n"
    "Pro versiyada siz uchun:\n"
    "✅ Barcha materiallarga to'liq kirish\n"
    "✅ Reklamasiz interfeys\n"
    "✅ Yangi qo'shimchalar birinchi bo'lib\n\n"
    f"💰 Narxi: *{PRO_PRICE}*"
)

PRO_LINK = "https://maktabgachahub.uz/pro"  # tasdiqlangandan keyin yuboriladigan link

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class PaymentStates(StatesGroup):
    waiting_screenshot = State()


def main_menu_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Pro sotib olish", callback_data="buy_pro")]
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
        PRO_DESCRIPTION,
        parse_mode="Markdown",
        reply_markup=main_menu_kb()
    )


@dp.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(f"Sizning chat ID'ingiz: `{message.from_user.id}`", parse_mode="Markdown")


@dp.callback_query(lambda c: c.data == "buy_pro")
async def process_buy(callback: CallbackQuery, state: FSMContext):
    text = (
        f"💳 To'lov uchun karta:\n\n"
        f"`{CARD_NUMBER}`\n"
        f"Egasi: *{CARD_OWNER}*\n\n"
        f"Summasi: *{PRO_PRICE}*\n\n"
        f"To'lovni amalga oshirgandan so'ng, chek/screenshot rasmini shu yerga yuboring 👇"
    )
    await callback.message.answer(text, parse_mode="Markdown")
    await state.set_state(PaymentStates.waiting_screenshot)
    await callback.answer()


@dp.message(PaymentStates.waiting_screenshot, lambda m: m.photo or m.document)
async def process_screenshot(message: Message, state: FSMContext):
    user = message.from_user
    caption = (
        f"🆕 Yangi to'lov so'rovi!\n\n"
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
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
