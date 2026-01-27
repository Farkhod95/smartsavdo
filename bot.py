import re
import aiohttp
from typing import Any, Dict, List, Union, Optional

from django.conf import settings

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext


# =========================
# CONFIG
# =========================
BOT_TOKEN="8521035854:AAFHVzkfiXjj9hQm1nNpEKVQhER0L8cvgoE"
API_BASE = "https://api-savdo.elegantchinni.uz/api/v1"
TG_SECRET = "change-me-strong-secret"

if not BOT_TOKEN:
    raise RuntimeError("settings.TELEGRAM_BOT_TOKEN yo‘q")


# =========================
# STATE
# =========================
class RegisterState(StatesGroup):
    full_name = State()
    region = State()
    district = State()
    phone = State()


JSONType = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


# =========================
# HELPERS
# =========================
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
    # Siz paginationni olib tashlagansiz => list bo'lishi kerak
    if isinstance(data, list):
        return data  # type: ignore
    # ehtiyot: agar baribir results bo'lib qolsa
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        return data["results"]  # type: ignore
    return []


def pick_name(obj: Dict[str, Any]) -> str:
    return str(obj.get("name") or f"#{obj.get('id', '')}")


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


def token_button_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Tizimga kirish (token olish)", callback_data="get_token")]
    ])


def safe_err_text(text: str, limit: int = 200) -> str:
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if len(text) > limit:
        return text[:limit] + "..."
    return text


async def api_get(path: str, params=None) -> JSONType:
    url = f"{API_BASE}{path}"
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as r:
            if r.status >= 400:
                body = await r.text()
                raise RuntimeError(f"{r.status}: {safe_err_text(body)}")
            return await r.json(content_type=None)


async def api_post(path: str, payload: dict) -> Dict[str, Any]:
    url = f"{API_BASE}{path}"
    headers = {"Content-Type": "application/json", "X-TG-SECRET": TG_SECRET}
    timeout = aiohttp.ClientTimeout(total=20)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload, headers=headers) as r:
            try:
                data = await r.json(content_type=None)
            except Exception:
                data = {"detail": await r.text()}

            if r.status >= 400:
                return {"_error": True, "status": r.status, "data": data}

            return data if isinstance(data, dict) else {"data": data}


async def build_regions_keyboard() -> InlineKeyboardMarkup:
    data = await api_get("/region/telegram/")
    regions = unwrap_list(data)

    buttons = []
    for r in regions:
        rid = r.get("id")
        if rid is None:
            continue
        buttons.append(InlineKeyboardButton(text=pick_name(r), callback_data=f"region:{rid}"))

    return InlineKeyboardMarkup(inline_keyboard=chunk_buttons(buttons, 2))


async def build_districts_keyboard(region_id: int) -> InlineKeyboardMarkup:
    data = await api_get("/district/telegram/", params={"region_id": region_id})
    districts = unwrap_list(data)

    buttons = []
    for d in districts:
        did = d.get("id")
        if did is None:
            continue
        buttons.append(InlineKeyboardButton(text=pick_name(d), callback_data=f"district:{did}"))

    return InlineKeyboardMarkup(inline_keyboard=chunk_buttons(buttons, 2))


# =========================
# GLOBAL BOT/DP (Django ichida)
# =========================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# =========================
# HANDLERS
# =========================
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
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
    except Exception:
        await message.answer("Regionlarni olishda xatolik. Admin bilan bog‘laning.")
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
    except Exception:
        await call.message.answer("Tumanlarni olishda xatolik. Admin bilan bog‘laning.")
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

    if not all(k in data for k in ("full_name", "region_id", "district_id")):
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

    reg = await api_post("/auth/telegram/register/", payload)
    if reg.get("_error"):
        await message.answer("❌ Ro‘yxatdan o‘tishda xatolik. Admin bilan bog‘laning.")
        return

    await message.answer(
        "✅ Ma’lumotlaringiz saqlandi.\n\n"
        "Endi token olish tugmasini bosing.\n"
        "🔁 Har safar bossangiz yangi token beriladi.",
        reply_markup=token_button_keyboard()
    )
    await state.clear()


@dp.message(RegisterState.phone)
async def handle_phone_wrong(message: Message, state: FSMContext):
    await message.answer("Iltimos, telefon raqamni Contact tugmasi orqali yuboring. 👇", reply_markup=phone_keyboard())


@dp.callback_query(F.data == "get_token")
async def handle_get_token(call: CallbackQuery):
    tok = await api_post("/auth/telegram/token/", {"telegram_id": call.from_user.id})

    if tok.get("_error"):
        if tok.get("status") == 404:
            await call.message.answer("Siz ro‘yxatdan o‘tmagansiz. /start ni bosing.")
        else:
            await call.message.answer("❌ Token olishda xatolik. Admin bilan bog‘laning.")
        await call.answer()
        return

    access = tok.get("access")
    refresh = tok.get("refresh")

    if not access or not refresh:
        await call.message.answer("❌ Token javobi noto‘g‘ri formatda.")
        await call.answer()
        return

    await call.message.answer(
        "✅ Token tayyor!\n\n"
        f"ACCESS:\n{access}\n\n"
        f"REFRESH:\n{refresh}\n\n"
        "🔁 Tugmani yana bossangiz, yangisini olasiz."
    )
    await call.answer()
