import os
import re
import asyncio
import aiohttp
from typing import Any, Dict, List, Union, Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext



BOT_TOKEN="8521035854:AAFHVzkfiXjj9hQm1nNpEKVQhER0L8cvgoE"
API_BASE = "https://api-savdo.elegantchinni.uz/api/v1"
TG_SECRET = "change-me-strong-secret"


class RegisterState(StatesGroup):
    full_name = State()
    region = State()
    district = State()
    phone = State()


JSONType = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


def normalize_phone(phone: str) -> str:
    raw = (phone or "").strip()
    digits = re.sub(r"\D+", "", raw)

    if digits.startswith("998") and len(digits) == 12:
        return f"+{digits}"
    if len(digits) == 9:
        return f"+998{digits}"
    if raw.startswith("+") and len(digits) >= 9:
        return raw
    return raw


def unwrap_list(data: JSONType) -> List[Dict[str, Any]]:
    """
    Siz pagination olib tashlagansiz => list qaytadi.
    Lekin ehtiyot uchun results bo'lsa ham ushlaymiz.
    """
    if isinstance(data, list):
        return data  # type: ignore
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        return data["results"]  # type: ignore
    return []


def pick_name(obj: Dict[str, Any]) -> str:
    # Siz aytganidek: faqat name
    print("obj:", obj)
    return str(obj.get("name") or f"#{obj.get('id', '')}")


def short_err(e: Exception, limit: int = 200) -> str:
    """
    Telegram 'message too long' bo'lmasligi uchun xatoni qisqartiramiz.
    """
    txt = str(e)
    txt = re.sub(r"\s+", " ", txt).strip()
    if len(txt) > limit:
        txt = txt[:limit] + "..."
    return txt


async def api_get(session: aiohttp.ClientSession, path: str, params=None) -> JSONType:
    url = f"{API_BASE}{path}"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "uz",  # yoki "ru"
    }
    async with session.get(url, params=params, headers=headers) as r:
        if r.status >= 400:
            # juda uzun HTML chiqib ketmasin
            try:
                err_json = await r.json(content_type=None)
                msg = str(err_json)
            except Exception:
                txt = await r.text()
                msg = txt[:300]
            raise aiohttp.ClientResponseError(
                request_info=r.request_info,
                history=r.history,
                status=r.status,
                message=msg,
                headers=r.headers
            )
        return await r.json(content_type=None)


async def api_post(session: aiohttp.ClientSession, path: str, payload: dict) -> Dict[str, Any]:
    url = f"{API_BASE}{path}"
    headers = {"Content-Type": "application/json"}

    # Agar backend secret tekshirsa:
    if TG_SECRET:
        headers["X-TG-SECRET"] = TG_SECRET

    async with session.post(url, json=payload, headers=headers) as r:
        try:
            data = await r.json(content_type=None)
        except Exception:
            text = await r.text()
            data = {"detail": text}

        if r.status >= 400:
            return {"_error": True, "status": r.status, "data": data}

        if isinstance(data, dict):
            return data
        return {"_error": False, "data": data}


async def has_user_by_telegram_id(telegram_id: int) -> bool:
    """
    Eng ishonchli tekshiruv: token endpoint'iga uramiz.
    - 200 -> user bor
    - 404 -> user yo'q
    - 401 -> secret xato (bu holatni alohida ko'rsatamiz)
    """
    async with aiohttp.ClientSession() as session:
        resp = await api_post(session, "/auth/telegram/token/", {"telegram_id": telegram_id})

    if resp.get("_error"):
        status = resp.get("status")
        if status == 404:
            return False
        if status == 401:
            # secret noto'g'ri bo'lsa bot doim registerga o'tib ketmasin
            raise RuntimeError("TG_SECRET noto‘g‘ri yoki backend secret tekshiryapti (401).")
        # boshqa xatolar: 500 va hokazo
        raise RuntimeError(f"User check xato: {status} {str(resp.get('data'))[:200]}")
    return True



def chunk_buttons(items: List[InlineKeyboardButton], per_row: int = 2) -> List[List[InlineKeyboardButton]]:
    rows: List[List[InlineKeyboardButton]] = []
    row: List[InlineKeyboardButton] = []
    for b in items:
        row.append(b)
        if len(row) == per_row:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return rows


def phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
# WEBAPP_LOGIN_URL = "https://api-savdo.elegantchinni.uz/api/v1/tg/login/"
WEBAPP_LOGIN_URL = "https://savdo.elegantchinni.uz/"

def token_button_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        # [InlineKeyboardButton(text="🔑 Tizimga kirish (token olish)", callback_data="get_token")],
        [InlineKeyboardButton(text="🌐 Savdo saytini ochish", web_app=WebAppInfo(url=WEBAPP_LOGIN_URL))],
    ])


async def build_regions_keyboard() -> InlineKeyboardMarkup:
    async with aiohttp.ClientSession() as session:
        data = await api_get(session, "/region/telegram/")
    regions = unwrap_list(data)
    buttons = []
    for r in regions:

        rid = r.get("id")
        if rid is None:
            continue
        buttons.append(InlineKeyboardButton(text=pick_name(r), callback_data=f"region:{rid}"))

    return InlineKeyboardMarkup(inline_keyboard=chunk_buttons(buttons, 2))


async def build_districts_keyboard(region_id: int) -> InlineKeyboardMarkup:
    async with aiohttp.ClientSession() as session:
        data = await api_get(session, "/district/telegram/", params={"region_id": region_id})
    districts = unwrap_list(data)

    buttons = []
    for d in districts:
        did = d.get("id")
        if did is None:
            continue
        buttons.append(InlineKeyboardButton(text=pick_name(d), callback_data=f"district:{did}"))

    return InlineKeyboardMarkup(inline_keyboard=chunk_buttons(buttons, 2))


# =========================
# BOT MAIN
# =========================
async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start(message: Message, state: FSMContext):
        await state.clear()

        try:
            exists = await has_user_by_telegram_id(message.from_user.id)
        except Exception as e:
            await message.answer(f"❌ Tekshiruvda xatolik: {short_err(e)}\nIltimos keyinroq urinib ko‘ring.")
            return

        if exists:
            await message.answer(
                "Assalomu alaykum! 👋\n"
                "Siz avval ro‘yxatdan o‘tib bo‘lgansiz.\n\n"
                "Token olish uchun tugmani bosing. 🔑",
                reply_markup=token_button_keyboard()
            )
            return

        # Aks holda registratsiya davom etadi
        await state.set_state(RegisterState.full_name)
        await message.answer(
            "Assalomu alaykum! 👋\n"
            "Tizimga ulanish uchun avval ro‘yxatdan o‘tamiz.\n\n"
            "Iltimos, FIO (to‘liq ism-familiya) ni kiriting:"
        )

    @dp.message(RegisterState.full_name)
    async def handle_full_name(message: Message, state: FSMContext):
        full_name = (message.text or "").strip()
        if len(full_name) < 5:
            await message.answer("FIO juda qisqa. Iltimos, to‘liqroq kiriting (masalan: Aliyev Ali).")
            return

        await state.update_data(full_name=full_name)

        try:
            kb = await build_regions_keyboard()
        except Exception as e:
            await message.answer(f"Regionlarni olishda xatolik. {short_err(e)}")
            return

        await state.set_state(RegisterState.region)
        await message.answer("Viloyatingizni tanlang:", reply_markup=kb)

    @dp.callback_query(RegisterState.region, F.data.startswith("region:"))
    async def handle_region(call: CallbackQuery, state: FSMContext):
        try:
            region_id = int(call.data.split(":")[1])
        except Exception:
            await call.answer("Noto‘g‘ri region", show_alert=True)
            return

        await state.update_data(region_id=region_id)

        try:
            kb = await build_districts_keyboard(region_id)
        except Exception as e:
            await call.message.answer(f"Tumanlarni olishda xatolik. {short_err(e)}")
            await call.answer()
            return

        await state.set_state(RegisterState.district)
        try:
            await call.message.edit_text("Tumanni tanlang:", reply_markup=kb)
        except Exception:
            await call.message.answer("Tumanni tanlang:", reply_markup=kb)

        await call.answer()

    @dp.callback_query(RegisterState.district, F.data.startswith("district:"))
    async def handle_district(call: CallbackQuery, state: FSMContext):
        try:
            district_id = int(call.data.split(":")[1])
        except Exception:
            await call.answer("Noto‘g‘ri tuman", show_alert=True)
            return

        await state.update_data(district_id=district_id)
        await state.set_state(RegisterState.phone)

        await call.message.answer(
            "Endi telefon raqamingizni yuboring (Contact tugmasi orqali):",
            reply_markup=phone_keyboard()
        )
        await call.answer()

    @dp.message(RegisterState.phone, F.contact)
    async def handle_phone(message: Message, state: FSMContext):
        data = await state.get_data()

        if "full_name" not in data or "region_id" not in data or "district_id" not in data:
            await message.answer("Ma’lumotlar topilmadi. Iltimos, qaytadan /start bosing.")
            await state.clear()
            return

        phone = normalize_phone(message.contact.phone_number)

        payload = {
            "telegram_id": message.from_user.id,
            "full_name": data["full_name"],
            "region_id": int(data["region_id"]),
            "district_id": int(data["district_id"]),
            "phone_number": phone,
        }

        async with aiohttp.ClientSession() as session:

            reg = await api_post(session, "/auth/telegram/register/", payload)

        if reg.get("_error"):
            await message.answer(f"❌ Xatolik: {reg['status']}\n{str(reg['data'])[:500]}")
            return

        await message.answer(
            "✅ Ma’lumotlaringiz saqlandi.\n\n"
            "Endi tizimga kirish uchun token olish tugmasini bosing.\n"
            "🔁 Har safar bossangiz yangi token beriladi.",
            reply_markup=token_button_keyboard()
        )

        await state.clear()

    @dp.message(RegisterState.phone)
    async def handle_phone_wrong(message: Message, state: FSMContext):
        await message.answer(
            "Iltimos, telefon raqamni Contact tugmasi orqali yuboring. 👇",
            reply_markup=phone_keyboard()
        )

    @dp.callback_query(F.data == "get_token")
    async def handle_get_token(call: CallbackQuery):
        async with aiohttp.ClientSession() as session:
            tok = await api_post(session, "/auth/telegram/token/", {"telegram_id": call.from_user.id})

        if tok.get("_error"):
            if tok.get("status") == 404:
                await call.message.answer("Siz ro‘yxatdan o‘tmagansiz. /start ni bosing.")
            else:
                await call.message.answer(f"❌ Token olishda xatolik: {tok.get('status')}\n{str(tok.get('data'))[:500]}")
            await call.answer()
            return

        access = tok.get("access")
        refresh = tok.get("refresh")

        if not access or not refresh:
            await call.message.answer(f"❌ Noto‘g‘ri javob: {str(tok)[:500]}")
            await call.answer()
            return

        await call.message.answer(
            "✅ Token tayyor!\n\n"
            f"ACCESS:\n{access}\n\n"
            f"REFRESH:\n{refresh}\n\n"
            "🔁 Tugmani yana bossangiz, yangisini olasiz."
        )
        await call.answer()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
