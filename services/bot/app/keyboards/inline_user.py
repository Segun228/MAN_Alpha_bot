from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Iterable
from pprint import pprint
from app.requests.get.get_business import get_business, get_user_business
import logging

main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Каталог 📦", callback_data="catalogue")],
        [InlineKeyboardButton(text="ИИ-инструменты", callback_data="ai_menu")],
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


async def confirm(        
    object_id:int,
    confirm_callback:str,
    decline_callback:str,
):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Подтвердить ✅", callback_data=f"{confirm_callback + str(object_id)}"))
    keyboard.add(InlineKeyboardButton(text="Отклонить ❌", callback_data=f"{decline_callback + str(object_id)}"))
    return keyboard.adjust(1).as_markup()


home = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
)


home_retry = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Попробовать еще", callback_data="retry_send_lawyer")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
)


retry_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="retry_lawyer_question")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
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


async def create_catalogue(business_id:int):
    keyboard= InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Персональный юрист", callback_data=f"personal_lawyer_{business_id}")],
            [InlineKeyboardButton(text="👤 Генерация идей", callback_data=f"idea_generation_{business_id}")],
            [InlineKeyboardButton(text="📞 Бизнес-анализ", callback_data=f"business_analysis_{business_id}")],
            [InlineKeyboardButton(text="👤 Структурирование информации", callback_data=f"information_structure_{business_id}")],
            [InlineKeyboardButton(text="На главную", callback_data="main_menu")]
        ]
    )
    return keyboard


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
    business_list:list|None = None
):
    keyboard = InlineKeyboardBuilder()
    if business_list is None:
        business_list = await get_user_business(telegram_id=telegram_id)
    logging.info(business_list)
    if business_list and isinstance(business_list, (list, tuple)):
        for bus in business_list:
            keyboard.add(InlineKeyboardButton(text=f"{bus.get("name", "business")}", callback_data=f"retrieve_business_{bus.get("id")}"))
    keyboard.add(InlineKeyboardButton(text="Добавить проект", callback_data="create_business"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="main_menu"))
    return keyboard.adjust(1).as_markup()



async def get_precise_catalogue(
    telegram_id,
    business_list:list|None = None
):
    keyboard = InlineKeyboardBuilder()
    if business_list is None:
        business_list = await get_user_business(telegram_id=telegram_id)
    logging.info(business_list)
    if business_list and isinstance(business_list, (list, tuple)):
        for bus in business_list:
            keyboard.add(InlineKeyboardButton(text=f"{bus.get("name", "business")}", callback_data=f"choose_business_{bus.get("id")}"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="main_menu"))
    return keyboard.adjust(1).as_markup()


async def get_single_business(
    telegram_id,
    business:dict
):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Изменить Бизнес", callback_data=f"edit_business_{business.get("id")}"))
    keyboard.add(InlineKeyboardButton(text="Удалить Бизнес", callback_data=f"delete_business_{business.get("id")}"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="main_menu"))
    return keyboard.adjust(1).as_markup()