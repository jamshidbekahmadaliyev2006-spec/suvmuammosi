from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def get_phone_request_keyboard() -> ReplyKeyboardMarkup:
    """Yangi foydalanuvchilar uchun telefon raqam yuborish klaviaturasi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True),
            ],
        ],
        resize_keyboard=True,
    )


def get_citizen_reply_keyboard() -> ReplyKeyboardMarkup:
    """Fuqarolar uchun doimiy menyu klaviaturasi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✍️ Murojaat yo'llash"),
                KeyboardButton(text="📍 Lokatsiya yuborish", request_location=True),
            ],
            [
                KeyboardButton(text="❌ Bekor qilish"),
                KeyboardButton(text="ℹ️ Bot haqida"),
            ],
        ],
        resize_keyboard=True,
    )


def get_cancel_inline_keyboard(incident_id: int | None = None) -> InlineKeyboardMarkup | None:
    """Murojaatni bir bosishda bekor qilish uchun inline tugma."""
    if incident_id is None:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Murojaatni bekor qilish",
                    callback_data=f"cancel_inc:{incident_id}",
                )
            ]
        ]
    )


def get_admin_reply_keyboard() -> ReplyKeyboardMarkup:
    """Tasdiqlangan administratorlar uchun boshqaruv klaviaturasi (Fuqaroga o'tish tugmasisiz)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📊 Markaziy Statistika"),
                KeyboardButton(text="🚨 So'nggi hodisalar"),
            ],
            [
                KeyboardButton(text="🔄 Yangilash"),
            ],
        ],
        resize_keyboard=True,
    )
