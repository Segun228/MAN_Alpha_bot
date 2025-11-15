from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Iterable
from pprint import pprint

main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Каталог 📦", callback_data="catalogue")],
        [InlineKeyboardButton(text="👤 Аккаунт", callback_data="account_menu")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")]
    ]
)

account_menu = InlineKeyboardMarkup(
    inline_keyboard=[
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
        [InlineKeyboardButton(text="📦 Персональный юрист", callback_data="personal_lawyer")],
        [InlineKeyboardButton(text="👤 Генерация идей", callback_data="idea_generation")],
        [InlineKeyboardButton(text="📞 Бизнес-анализ", callback_data="business_analysis")],
        [InlineKeyboardButton(text="👤 Структурирование информации", callback_data="information_structure")],
        [InlineKeyboardButton(text="На главную", callback_data="main_menu")]
    ]
)


justice = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📦 Юридическая консультация", callback_data="personal_lawyer_start")],
        [InlineKeyboardButton(text="Назад", callback_data="catalogue")]
    ]
)


idea_generation = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📦 Сгенерировать идеи", callback_data="idea_generate_start")],
        [InlineKeyboardButton(text="Назад", callback_data="catalogue")]
    ]
)


business_analysis = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📦 SWOT-анализ", callback_data="swot_start")],
        [InlineKeyboardButton(text="📦 Business Model Canvas", callback_data="bmc_start")],
        [InlineKeyboardButton(text="📦 Customer Journey Map", callback_data="cjm_start")],
        [InlineKeyboardButton(text="📦 Value Proposition Canvas", callback_data="vpc_start")],
        [InlineKeyboardButton(text="📦 PEST-анализ", callback_data="pest_start")],
        [InlineKeyboardButton(text="Назад", callback_data="catalogue")]
    ]
)

async def give_acess(user_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Разрешить ✅", callback_data=f"access_give_{user_id}"))
    keyboard.add(InlineKeyboardButton(text="Отклонить ❌", callback_data=f"access_reject_{user_id}"))
    return keyboard.adjust(1).as_markup()


async def get_business_catalogue(
    telegram_id,
    business_list:list|None
):
    keyboard = InlineKeyboardBuilder()
    if business_list:
        for bus in business_list:
            keyboard.add(InlineKeyboardButton(text=f"{bus.get("name", "business")}", callback_data=f"{bus.get("id")}"))
    keyboard.add(InlineKeyboardButton(text="Добавить проект", callback_data=f"create_business"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="home"))
    return keyboard.adjust(1).as_markup()