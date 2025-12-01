from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Iterable


main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Каталог 📦", callback_data="catalogue")],
        [InlineKeyboardButton(text="Рассылка ✉️", callback_data="send_menu")],
        [InlineKeyboardButton(text="📊 Юнит-экономика", callback_data="unit_menu")],
        [InlineKeyboardButton(text="Опрос качества 📊", callback_data="start_polling")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")]
    ]
)


main_special = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Уйти 😢", callback_data="exit_hysteria")],
    ]
)


def grade_keyboard(
    prefix = "grade"
):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="⭐️⭐️⭐️⭐️⭐️", callback_data=f"{prefix}_{5}"))
    keyboard.add(InlineKeyboardButton(text="⭐️⭐️⭐️⭐️", callback_data=f"{prefix}_{4}"))
    keyboard.add(InlineKeyboardButton(text="⭐️⭐️⭐️", callback_data=f"{prefix}_{3}"))
    keyboard.add(InlineKeyboardButton(text="⭐️⭐️", callback_data=f"{prefix}_{2}"))
    keyboard.add(InlineKeyboardButton(text="⭐️", callback_data=f"{prefix}_{1}"))
    keyboard.add(InlineKeyboardButton(text="💀", callback_data=f"{prefix}_{0}"))
    return keyboard.adjust(1).as_markup()




account_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Админ ⚙️", callback_data="admin_menu")],
        [InlineKeyboardButton(text="Запросить права администратора 👑", callback_data="request_admin")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
)

delete_account_confirmation_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="delete_account")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="account_menu")],
    ]
)



home = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
)

restart = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Главное меню", callback_data="restart")],
    ]
)


catalogue = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=" Каталог", callback_data="catalogue")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
)


async def give_acess(user_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Разрешить ✅", callback_data=f"access_give_{user_id}"))
    keyboard.add(InlineKeyboardButton(text="Отклонить ❌", callback_data=f"access_reject_{user_id}"))
    return keyboard.adjust(1).as_markup()